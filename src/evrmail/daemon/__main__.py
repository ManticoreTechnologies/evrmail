# ─── 📦 EvrMail Daemon Main ────────────────────────────────────────────────────

import json
import os
import time
from pathlib import Path

from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import ZMQTopic, EvrmoreZMQClient
from evrmail.config import load_config
from evrmail.wallet import list_wallets, load_wallet
from evrmail.utils.inbox import save_messages
from evrmail.utils.scan_payload import scan_payload
from evrmail.daemon import (
    STORAGE_DIR, INBOX_FILE, PROCESSED_TXIDS_FILE,
    load_inbox, save_inbox, load_processed_txids, save_processed_txids,
    monitor_confirmed_utxos_realtime
)

# ─── 📂 Paths ──────────────────────────────────────────────────────────────────

UTXO_DIR = STORAGE_DIR / "utxos"
LOG_FILE = STORAGE_DIR / "daemon.log"
MEMPOOL_UTXO_FILE = UTXO_DIR / "mempool.json"
CONFIRMED_UTXO_FILE = UTXO_DIR / "confirmed.json"

# ─── 🌍 Global State ──────────────────────────────────────────────────────────

known_addresses = {}

# ─── ⚙️ Setup Clients ──────────────────────────────────────────────────────────

config = load_config()
rpc_client = EvrmoreClient(
    url=config["rpc_host"],
    rpcport=config["rpc_port"],
    rpcuser=config["rpc_user"],
    rpcpassword=config["rpc_password"],
)
zmq_client = EvrmoreZMQClient(
    topics=[ZMQTopic.RAW_TX, ZMQTopic.RAW_BLOCK],
    zmq_host=config["rpc_host"].split('tcp://')[1]
)

# ─── 📦 UTXO Management ────────────────────────────────────────────────────────

def load_utxos():
    mempool = {}
    confirmed = {}
    if MEMPOOL_UTXO_FILE.exists():
        mempool = json.loads(MEMPOOL_UTXO_FILE.read_text())
    if CONFIRMED_UTXO_FILE.exists():
        confirmed = json.loads(CONFIRMED_UTXO_FILE.read_text())
    return {"mempool": mempool, "confirmed": confirmed}

def save_utxos(utxos):
    # Ensure directory exists
    UTXO_DIR.mkdir(parents=True, exist_ok=True)
    MEMPOOL_UTXO_FILE.write_text(json.dumps(utxos["mempool"], indent=2))
    CONFIRMED_UTXO_FILE.write_text(json.dumps(utxos["confirmed"], indent=2))

def mark_utxos_as_spent(tx, utxo_cache):
    """
    Given a transaction, mark matching UTXOs as spent in the cache.
    """
    for vin in tx.get("vin", []):
        spent_txid = vin.get("txid")
        spent_vout = vin.get("vout")

        # Check both mempool and confirmed
        for pool_name in ["mempool", "confirmed"]:
            pool = utxo_cache.get(pool_name, {})
            for address, utxos in pool.items():
                for utxo in utxos:
                    if utxo["txid"] == spent_txid and utxo["vout"] == spent_vout:
                        utxo["spent"] = True
                        print(f"[Daemon] 🔥 Marked UTXO {spent_txid}:{spent_vout} as spent for address {address}")

# ─── 📋 Address Reloading ──────────────────────────────────────────────────────

def reload_known_addresses():
    global known_addresses
    print("[Daemon] 🔄 Reloading known addresses...")
    address_map = {}
    for name in list_wallets():
        wallet = load_wallet(name)
        if wallet and "addresses" in wallet:
            for entry in wallet["addresses"]:
                if isinstance(entry, dict):
                    address_map[entry["address"]] = name
                elif isinstance(entry, str):
                    address_map[entry] = name
    known_addresses = address_map

# ─── 🧠 Transaction Handling ───────────────────────────────────────────────────

def add_utxo(cache, address, utxo):
    cache.setdefault(address, []).append(utxo)

def process_transaction(tx, txid, utxo_cache, is_confirmed):
    for vout in tx.get("vout", []):
        script = vout.get("scriptPubKey", {})
        print("-"*10)
        print(script)
        from evrmail.wallet.script import decode as decode_script
        # 📡 Always scan for IPFS message
        decoded_script = decode_script(script.get('hex'))
        asset = decoded_script.get("asset", {})
        ipfs_hash = asset.get("message")
        print("-"*10)
        print(script)
        print(decoded_script)
        print(asset)
        print(ipfs_hash)
        print("-"*10)
        if ipfs_hash:
            print(f"[Daemon] 🛰 Detected IPFS CID in TX {txid}: {ipfs_hash}")
            try:
                decrypted_messages = scan_payload(ipfs_hash)
                if decrypted_messages:
                    inbox = load_inbox()
                    inbox.extend(decrypted_messages)
                    save_inbox(inbox)
                    print(f"[Daemon] ✉️ Saved {len(decrypted_messages)} new messages to inbox.")
                else:
                    print(f"[Daemon] ℹ️ No messages for us in payload {ipfs_hash}")
            except Exception as e:
                print(f"[Daemon] ⚠️ Failed to scan IPFS payload {ipfs_hash}: {e}")

        # 🔵 Normal UTXO tracking
        addresses = script.get("addresses", [])
        address = addresses[0] if addresses else None
        asset_name = asset.get("name")
        
        if type(script) is str:
            script_hex = script
        else:
            script_hex = script.get('hex')
        print("-"*10,"vout","-"*10)
        print(vout)
        print("-"*10,"vout","-"*10)

        if asset_name is None:
            amount = vout.get("value")
        else:
            amount = script.get("amount")
        if address and address in known_addresses:
            utxo = {
                "txid": txid,
                "vout": vout["n"],
                "amount": amount,
                "asset": asset_name,
                "confirmations": 1 if is_confirmed else 0,
                "spent": False,
                "script": script_hex,
                "address": address
            }
            pool = "confirmed" if is_confirmed else "mempool"
            add_utxo(utxo_cache[pool], address, utxo)



def move_utxo_from_mempool_to_confirmed(txid, utxo_cache):
    found = False
    for address, utxos in list(utxo_cache["mempool"].items()):
        new_utxos = []
        for utxo in utxos:
            if utxo["txid"] == txid:
                utxo["confirmations"] = 1
                add_utxo(utxo_cache["confirmed"], address, utxo)
                found = True
            else:
                new_utxos.append(utxo)
        if new_utxos:
            utxo_cache["mempool"][address] = new_utxos
        else:
            del utxo_cache["mempool"][address]
    return found
def sync_utxos_from_node(rpc, known_addresses, log_callback):
    log = log_callback
    log("🔄 Fetching full UTXO set from node...")
    address_list = list(known_addresses.keys())

    # Ensure directory exists
    UTXO_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing UTXO file if it exists
    confirmed_path = UTXO_DIR / "confirmed.json"
    existing_confirmed = {}
    if confirmed_path.exists():
        existing_confirmed = json.loads(confirmed_path.read_text())

    # Mark all existing UTXOs as spent initially
    for addr, utxos in existing_confirmed.items():
        for utxo in utxos:
            utxo["spent"] = True

    # Fetch current node UTXOs
    for i in range(0, len(address_list), 100):
        chunk = address_list[i:i+100]
        try:
            # 🟢 Normal EVR UTXOs
            evr_utxos = rpc.getaddressutxos({"addresses": chunk})
            for u in evr_utxos:
                addr = u["address"]
                txid = u["txid"]
                vout = u["outputIndex"]

                # Find the matching old UTXO or add new
                found = False
                for utxo in existing_confirmed.get(addr, []):
                    if utxo["txid"] == txid and utxo["vout"] == vout:
                        utxo["spent"] = False
                        utxo["confirmations"] = u.get("confirmations", 1)
                        found = True
                        break
                if not found:
                    utxo = {
                        "txid": txid,
                        "vout": vout,
                        "amount": u["satoshis"],
                        "asset": None,
                        "confirmations": u.get("confirmations", 1),
                        "block_height": u.get("height"),
                        "spent": False,
                        "script": u.get("script"),
                        "address": addr
                    }
                    existing_confirmed.setdefault(addr, []).append(utxo)

            # 🟠 Asset UTXOs
            asset_utxos = rpc.getaddressutxos({"addresses": chunk, "assetName": "*"})
            for u in asset_utxos:
                print(u)
                addr = u["address"]
                txid = u["txid"]
                vout = u["outputIndex"]

                found = False
                for utxo in existing_confirmed.get(addr, []):
                    if utxo["txid"] == txid and utxo["vout"] == vout:
                        utxo["spent"] = False
                        utxo["confirmations"] = u.get("confirmations", 1)
                        found = True
                        break
                if not found:
                    utxo = {
                        "txid": txid,
                        "vout": vout,
                        "amount": u.get("satoshis"),
                        "asset": u.get("assetName"),
                        "confirmations": u.get("confirmations", 1),
                        "block_height": u.get("height"),
                        "spent": False,
                        "script": u.get("script"),
                        "address": addr
                    }
                    existing_confirmed.setdefault(addr, []).append(utxo)

        except Exception as e:
            log(f"⚠️ Failed to fetch UTXOs for chunk: {e}")

    # Save updated
    confirmed_path.write_text(json.dumps(existing_confirmed, indent=2))

    # Reset mempool (optional depending if you want to do smarter merging there too)
    mempool_path = UTXO_DIR / "mempool.json"
    mempool_path.write_text("{}")

    total_utxos = sum(len(v) for v in existing_confirmed.values())
    log(f"✅ Synced {total_utxos} total UTXOs (spent + unspent).")

    return existing_confirmed

# ─── 🚀 Main Entry ─────────────────────────────────────────────────────────────

def main():
    def log(msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        full = f"[{ts}] {msg}"
        with open(LOG_FILE, "a") as f:
            f.write(full + "\n")
        print(full)

    log("📡 EvrMail Daemon starting...")
    reload_known_addresses()
    log(f"🔑 Loaded {len(known_addresses)} known addresses.")
    sync_utxos_from_node(rpc_client, known_addresses, log)
    utxo_cache = load_utxos()
    processed_txids = load_processed_txids()

    @zmq_client.on(ZMQTopic.RAW_TX)
    def on_raw_tx(notification):
        from evrmail.wallet.tx import decode_transaction
        tx = decode_transaction(notification.hex)
        txid = tx["txid"]

        if txid not in processed_txids:
            processed_txids.append(txid)
            mark_utxos_as_spent(tx, utxo_cache)  # 👈 New
            process_transaction(tx, txid, utxo_cache, is_confirmed=False)
            save_utxos(utxo_cache)
            save_processed_txids(processed_txids)
            log(f"💬 Mempool TX: {txid}")


    @zmq_client.on(ZMQTopic.RAW_BLOCK)
    def on_raw_block(notification):
        from evrmail.wallet.block import decode as decode_block
        from evrmail.wallet.tx import decode_transaction

        block = decode_block(notification.hex)
        for tx_hex in block["tx"]:
            tx = decode_transaction(tx_hex)
            txid = tx["txid"]

            moved = move_utxo_from_mempool_to_confirmed(txid, utxo_cache)
            if not moved:
                process_transaction(tx, txid, utxo_cache, is_confirmed=True)

            if txid not in processed_txids:
                processed_txids.append(txid)

        save_utxos(utxo_cache)
        save_processed_txids(processed_txids)
        log(f"📦 Block processed with {len(block['tx'])} txs.")

    zmq_client.start()
    monitor_confirmed_utxos_realtime()

    log("✅ Listening for transactions and blocks.")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        log("🛑 Shutting down.")
    finally:
        zmq_client.stop_sync()
        rpc_client.close_sync()

# ─── 🚀 Entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
