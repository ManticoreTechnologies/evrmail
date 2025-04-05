import json
import os
import time
from pathlib import Path
from evrmore_rpc.zmq import ZMQTopic
from evrmail.config import load_config
from evrmail.utils.scan_payload import scan_payload
from evrmail.utils.inbox import save_messages
from evrmail.wallet import list_wallets, load_wallet
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc import EvrmoreClient
rpc_client = EvrmoreClient()
zmq_client = EvrmoreZMQClient()
config = load_config()

STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"
PUBLIC_CHANNELS_DIR = STORAGE_DIR / "public_channels"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_CHANNELS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = STORAGE_DIR / "daemon.log"


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)


def load_known_addresses():
    address_map = {}
    for name in list_wallets():
        wallet = load_wallet(name)
        if wallet and "addresses" in wallet:
            for entry in wallet["addresses"]:
                address_map[entry["address"]] = {
                    "wallet": name,
                    "path": entry["path"],
                    "index": entry["index"]
                }
    return address_map


def load_processed_txids():
    if PROCESSED_TXIDS_FILE.exists():
        return json.loads(PROCESSED_TXIDS_FILE.read_text())
    return []


def save_processed_txids(txids):
    PROCESSED_TXIDS_FILE.write_text(json.dumps(txids, indent=2))


def is_probable_cid(value: str) -> bool:
    return value.startswith("Qm") or value.startswith("baf")


def write_to_public_channel(asset_name: str, content: str, txid: str):
    out_file = PUBLIC_CHANNELS_DIR / f"{asset_name}.jsonl"
    entry = {
        "txid": txid,
        "timestamp": time.time(),
        "content": content,
    }
    with open(out_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    log("📡 evrmail Daemon Starting...")
    rpc = rpc_client
    zmq = zmq_client
    known_addresses = load_known_addresses()
    log(f"Loaded {len(known_addresses)} known addresses: {list(known_addresses.keys())}")

    @zmq.on(ZMQTopic.TX)
    def on_transaction(notification):
        try:
            txid = notification.tx.get("txid")
            processed_txids = load_processed_txids()
            if txid in processed_txids:
                return
            processed_txids.append(txid)
            save_processed_txids(processed_txids)

            for vout in notification.tx.get("vout", []):
                script = vout.get("scriptPubKey", {})
                if script.get("type") == "transfer_asset":
                    asset = script.get("asset", {})
                    cid = asset.get("message")
                    asset_name = asset.get("name")

                    if cid:
                        if is_probable_cid(cid):
                            log(f"📥 New message CID detected: {cid}")
                            messages = scan_payload(cid)
                            log(f"📥 Scanned batch includes to: {[m.get('to') for m in messages]}")

                            # move this inside, reloaded in case wallets changed
                            known_addresses = load_known_addresses()

                            relevant = [m for m in messages if m.get("to") in known_addresses]
                            if relevant:
                                log(f"📨 {len(relevant)} new message(s) for local wallets")
                                for msg in relevant:
                                    wallet = known_addresses[msg["to"]]["wallet"]
                                    log(f"📬 {msg['to']} (wallet: {wallet})")
                                save_messages(relevant)
                        else:
                            log(f"🌐 Public message on asset [{asset_name}]: {cid}")
                            write_to_public_channel(asset_name, cid, txid)
        except Exception as e:
            log(f"❌ Error in handler: {e}")


    zmq.start()
    log("✅ Daemon is now listening for messages.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        log("\n🛑 Stopping evrmail Daemon...")
    finally:
        zmq.stop_sync()
        rpc.close_sync()


if __name__ == "__main__":
    main()
