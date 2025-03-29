import json
import os
import subprocess
import time
from pathlib import Path
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmail.config import load_config   
from evrmail.utils.scan_payload import scan_payload
from evrmail.utils.inbox import save_messages
from evrmail.utils.ipfs import fetch_ipfs_json

config = load_config()

STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Load/save helpers

def load_processed_txids():
    if PROCESSED_TXIDS_FILE.exists():
        return json.loads(PROCESSED_TXIDS_FILE.read_text())
    return []

def save_processed_txids(txids):
    PROCESSED_TXIDS_FILE.write_text(json.dumps(txids, indent=2))

def main():
    print("📡 evrmail Daemon Starting...")
    rpc = EvrmoreClient()
    zmq = EvrmoreZMQClient()

    @zmq.on(ZMQTopic.TX)
    def on_transaction(notification):
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
                if cid:
                    print(f"📥 New message CID detected: {cid}")
                    messages = scan_payload(cid)
                    if messages:
                        save_messages(messages)

    zmq.start()
    print("✅ Daemon is now listening for messages.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Stopping evrmail Daemon...")
    finally:
        zmq.stop_sync()
        rpc.close_sync()

if __name__ == "__main__":
    main()
