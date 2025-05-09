# ─── 📦 EvrMail Daemon Main ────────────────────────────────────────────────────

import json
import os
import time
import traceback
from pathlib import Path
import logging

from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import ZMQTopic, EvrmoreZMQClient
from evrmail.config import load_config
from evrmail.wallet import list_wallets, load_wallet
from evrmail.utils.inbox import save_messages
from evrmail.utils.scan_payload import scan_payload
from evrmail.utils import (
    configure_logging, 
    daemon as daemon_log, 
    chain as chain_log, 
    wallet as wallet_log, 
    network as network_log,
    debug_log
)
from evrmail.daemon import (
    STORAGE_DIR, INBOX_FILE, PROCESSED_TXIDS_FILE,
    load_inbox, save_inbox, load_processed_txids, save_processed_txids,
    monitor_confirmed_utxos_realtime,
    EVRMailDaemon
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
    MEMPOOL_UTXO_FILE.write_text(json.dumps(utxos["mempool"], indent=2))
    CONFIRMED_UTXO_FILE.write_text(json.dumps(utxos["confirmed"], indent=2))

def mark_utxos_as_spent(tx, txid, utxo_cache):
    """
    Given a transaction, mark matching UTXOs as spent in the cache.
    """
    spent_count = 0
    
    for vin in tx.get("vin", []):
        spent_txid = vin.get("txid")
        spent_vout = vin.get("vout")
        
        if not spent_txid or spent_vout is None:
            continue

        # Check both mempool and confirmed
        for pool_name in ["mempool", "confirmed"]:
            pool = utxo_cache.get(pool_name, {})
            for address, utxos in pool.items():
                for utxo in utxos:
                    if utxo["txid"] == spent_txid and utxo["vout"] == spent_vout:
                        utxo["spent"] = True
                        spent_count += 1
                        asset_name = utxo.get("asset", "EVR")
                        amount = utxo.get("amount", 0)
                        
                        # Log with detailed information
                        chain_log("info", f"🔥 Marked UTXO {spent_txid}:{spent_vout} as spent for address {address}", details={
                            "txid": spent_txid,
                            "vout": spent_vout,
                            "spending_txid": txid if hasattr(tx, "txid") else "Unknown",
                            "address": address,
                            "asset": asset_name,
                            "amount": amount,
                            "pool": pool_name,
                            "explorer_link": f"https://explorer.evrmore.org/tx/{spent_txid}"
                        })
    
    if spent_count > 0:
        wallet_log("info", f"📤 Marked {spent_count} UTXOs as spent in transaction", details={
            "spent_count": spent_count,
            "txid": txid if hasattr(tx, "txid") else "Unknown",
            "explorer_link": f"https://explorer.evrmore.org/tx/{txid}" if hasattr(tx, "txid") else None
        })
    
    return spent_count

# ─── 📋 Address Reloading ──────────────────────────────────────────────────────

def reload_known_addresses():
    global known_addresses
    daemon_log("info", "🔄 Reloading known addresses...")
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

def process_transaction(tx, txid, utxo_cache, is_confirmed, debug_mode=False):
    for vout in tx.get("vout", []):
        script = vout.get("scriptPubKey", {})
        
        # Only log in debug mode
        if debug_mode:
            debug_log(f"Processing script in tx {txid}...", details={
                "txid": txid,
                "vout_index": vout.get("n"),
                "script_type": script.get("type"),
                "addresses": script.get("addresses")
            })
            debug_log(f"Script content: {script}")
        
        from evrmail.wallet.script import decode as decode_script
        # 📡 Always scan for IPFS message
        decoded_script = decode_script(script.get('hex'))
        asset = decoded_script.get("asset", {})
        ipfs_hash = asset.get("message")
        
        # Debug logging only when needed
        if debug_mode:
            debug_log(f"Decoded script: {decoded_script}")
            debug_log(f"Asset info: {asset}")
            debug_log(f"IPFS hash: {ipfs_hash}")
        
        if ipfs_hash:
            chain_log("info", f"🛰 Detected IPFS CID in TX {txid}: {ipfs_hash}", details={
                "txid": txid,
                "ipfs_cid": ipfs_hash,
                "asset_name": asset.get("name"),
                "explorer_link": f"https://explorer.evrmore.org/tx/{txid}"
            })
            try:
                # Get any decrypted messages from the payload
                decrypted_messages = scan_payload(ipfs_hash)
                
                contact_requests = []
                regular_messages = []
                
                # Separate contact requests from regular messages
                for msg in decrypted_messages:
                    # Get the content either directly or from content field
                    content = msg.get("content", {})
                    raw_content = msg.get("raw", {})
                    
                    # Try to parse JSON content if it's a string (might be a serialized contact request)
                    if isinstance(content, str):
                        try:
                            parsed_content = json.loads(content)
                            if isinstance(parsed_content, dict) and parsed_content.get("type") == "contact_request":
                                # It's a contact request in JSON string format
                                daemon_log("info", f"Found contact request in JSON string format")
                                contact_requests.append({"content": parsed_content, "from": parsed_content.get("from")})
                                continue
                        except json.JSONDecodeError:
                            # Not JSON, treat as regular message
                            pass
                    
                    # Check standard contact request format
                    if isinstance(content, dict) and content.get("type") == "contact_request":
                        contact_requests.append(msg)
                        daemon_log("info", f"📇 Received contact request from {content.get('from')}", details={
                            "from": content.get("from"),
                            "name": content.get("name", "Unnamed"),
                            "time": content.get("timestamp")
                        })
                    # Also check in raw field if available
                    elif isinstance(raw_content, dict) and raw_content.get("type") == "contact_request":
                        contact_requests.append({"content": raw_content, "from": raw_content.get("from")})
                        daemon_log("info", f"📇 Received contact request from {raw_content.get('from')} (in raw field)")
                    # Also check if subject is a contact request indicator
                    elif (isinstance(content, dict) and 
                          content.get("subject", "").lower() == "contact request" and 
                          content.get("from") is not None):
                        try:
                            # Try to extract contact request data
                            contact_data = content.get("content", "{}")
                            if isinstance(contact_data, str):
                                contact_data = json.loads(contact_data)
                            
                            if isinstance(contact_data, dict) and "from" in contact_data:
                                contact_requests.append({"content": contact_data, "from": contact_data.get("from")})
                                daemon_log("info", f"📇 Detected contact request by subject from {contact_data.get('from')}")
                            else:
                                # Use message data as contact request
                                contact_requests.append({"content": {
                                    "type": "contact_request",
                                    "from": content.get("from"),
                                    "name": content.get("from"),  # Use address as name if not provided
                                    "timestamp": content.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                                }, "from": content.get("from")})
                                daemon_log("info", f"📇 Created contact request from message with Contact Request subject")
                        except Exception as e:
                            daemon_log("warning", f"Failed to process potential contact request: {e}")
                    else:
                        regular_messages.append(msg)
                
                # Add verbose debugging for contact request detection
                if decrypted_messages and not contact_requests and not regular_messages:
                    daemon_log("debug", f"Messages found but none classified as contact request or regular message")
                    # Log first message structure for debugging
                    if decrypted_messages:
                        first_msg = decrypted_messages[0]
                        daemon_log("debug", f"First message structure: {json.dumps(first_msg, default=str)}")
                
                # Process contact requests with EVRMailDaemon
                if contact_requests:
                    daemon = EVRMailDaemon()
                    for request in contact_requests:
                        daemon_log("info", f"Processing contact request from {request.get('from')}")
                        daemon.process_contact_request(request.get("content"))
                
                # Save regular messages to inbox
                if regular_messages:
                    inbox = load_inbox()
                    inbox.extend(regular_messages)
                    save_inbox(inbox)
                    daemon_log("info", f"✉️ Saved {len(regular_messages)} new messages to inbox.", details={
                        "message_count": len(regular_messages),
                        "ipfs_cid": ipfs_hash,
                        "message_subjects": [msg.get("content", {}).get("subject", "No Subject") for msg in regular_messages[:3]]
                    })
                
                if not decrypted_messages:
                    daemon_log("info", f"ℹ️ No messages for us in payload {ipfs_hash}", details={
                        "ipfs_cid": ipfs_hash,
                        "txid": txid
                    })
            except Exception as e:
                daemon_log("error", f"⚠️ Failed to scan IPFS payload {ipfs_hash}: {e}", details={
                    "ipfs_cid": ipfs_hash,
                    "error": str(e),
                    "txid": txid
                })

        # 🔵 Normal UTXO tracking
        addresses = script.get("addresses", [])
        address = addresses[0] if addresses else None
        asset_name = asset.get("name")
        
        if type(script) is str:
            script_hex = script
        else:
            script_hex = script.get('hex')
            
        # Only log detailed information in debug mode
        if debug_mode:
            debug_log(f"Transaction output details: {vout}")

        # Add UTXO to appropriate cache
        if address and address in known_addresses:
            amount = vout.get("value") if asset_name is None else script.get("amount")
            
            # Log with detailed information
            if asset_name:
                chain_log("info", f"Found {asset_name} for address {address} in tx {txid}", details={
                    "asset": asset_name,
                    "address": address,
                    "amount": amount * 1e8,
                    "txid": txid,
                    "vout": vout["n"],
                    "explorer_link": f"https://explorer.evrmore.org/tx/{txid}"
                })
            else:
                chain_log("info", f"Found EVR for address {address} in tx {txid}", details={
                    "address": address,
                    "amount": amount * 1e8,
                    "txid": txid,
                    "vout": vout["n"],
                    "explorer_link": f"https://explorer.evrmore.org/tx/{txid}"
                })
                
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
    
    # Stats for logging
    stats = {
        "total_evr_utxos": 0,
        "total_asset_utxos": 0,
        "updated_utxos": 0,
        "new_utxos": 0,
        "addresses_with_utxos": set(),
        "assets_found": set()
    }

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
            stats["total_evr_utxos"] += len(evr_utxos)
            
            for u in evr_utxos:
                addr = u["address"]
                txid = u["txid"]
                vout = u["outputIndex"]
                stats["addresses_with_utxos"].add(addr)

                # Find the matching old UTXO or add new
                found = False
                for utxo in existing_confirmed.get(addr, []):
                    if utxo["txid"] == txid and utxo["vout"] == vout:
                        utxo["spent"] = False
                        utxo["confirmations"] = u.get("confirmations", 1)
                        found = True
                        stats["updated_utxos"] += 1
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
                    stats["new_utxos"] += 1

            # 🟠 Asset UTXOs
            asset_utxos = rpc.getaddressutxos({"addresses": chunk, "assetName": "*"})
            stats["total_asset_utxos"] += len(asset_utxos)
            
            for u in asset_utxos:
                addr = u["address"]
                txid = u["txid"]
                vout = u["outputIndex"]
                asset_name = u.get("assetName")
                stats["addresses_with_utxos"].add(addr)
                if asset_name:
                    stats["assets_found"].add(asset_name)

                found = False
                for utxo in existing_confirmed.get(addr, []):
                    if utxo["txid"] == txid and utxo["vout"] == vout:
                        utxo["spent"] = False
                        utxo["confirmations"] = u.get("confirmations", 1)
                        found = True
                        stats["updated_utxos"] += 1
                        break
                if not found:
                    utxo = {
                        "txid": txid,
                        "vout": vout,
                        "amount": u.get("satoshis"),
                        "asset": asset_name,
                        "confirmations": u.get("confirmations", 1),
                        "block_height": u.get("height"),
                        "spent": False,
                        "script": u.get("script"),
                        "address": addr
                    }
                    existing_confirmed.setdefault(addr, []).append(utxo)
                    stats["new_utxos"] += 1

        except Exception as e:
            log(f"⚠️ Failed to fetch UTXOs for chunk: {e}")

    # Save updated
    confirmed_path.write_text(json.dumps(existing_confirmed, indent=2))

    # Reset mempool (optional depending if you want to do smarter merging there too)
    mempool_path = UTXO_DIR / "mempool.json"
    mempool_path.write_text("{}")

    # Calculate totals for detailed logging
    total_utxos = sum(len(v) for v in existing_confirmed.values())
    active_addresses = len([a for a, utxos in existing_confirmed.items() if any(not u.get("spent", False) for u in utxos)])
    
    # Log detailed statistics
    wallet_log("info", f"📊 Synced {total_utxos} UTXOs for {active_addresses} active addresses", details={
        "total_utxos": total_utxos,
        "active_addresses": active_addresses,
        "evr_utxos": stats["total_evr_utxos"],
        "asset_utxos": stats["total_asset_utxos"],
        "updated_utxos": stats["updated_utxos"],
        "new_utxos": stats["new_utxos"],
        "addresses_with_utxos": len(stats["addresses_with_utxos"]),
        "assets_found": list(stats["assets_found"])
    })
    
    # Return a simple structure for backward compatibility
    return {
        "confirmed": existing_confirmed,
        "mempool": {}
    }

# ─── 🚀 Main Entry ─────────────────────────────────────────────────────────────

def main(debug_mode=False):
    """Main daemon entry point with optional debug mode"""
    # Configure logging
    log_level = logging.DEBUG if debug_mode else logging.INFO
    configure_logging(level=log_level)
    
    daemon_log("info", "📡 EvrMail Daemon starting...")
    reload_known_addresses()
    wallet_log("info", f"🔑 Loaded {len(known_addresses)} known addresses.", details={
        "address_count": len(known_addresses),
        "addresses": list(known_addresses.keys())[:5] + (["..."] if len(known_addresses) > 5 else [])
    })
    
    daemon_log("info", "🔄 Syncing UTXOs from node...")
    utxo_data = sync_utxos_from_node(rpc_client, known_addresses, 
                         lambda msg: daemon_log("info", msg))
    
    # Update the global utxo cache
    utxo_cache = load_utxos()
    utxo_cache.update(utxo_data)
    
    processed_txids = load_processed_txids()
    
    total_utxos = sum(len(utxos) for utxos in utxo_cache["confirmed"].values()) + \
                  sum(len(utxos) for utxos in utxo_cache["mempool"].values())
    
    daemon_log("info", f"✅ Synced {total_utxos} total UTXOs (spent + unspent).", details={
        "confirmed_utxos": sum(len(utxos) for utxos in utxo_cache["confirmed"].values()),
        "mempool_utxos": sum(len(utxos) for utxos in utxo_cache["mempool"].values()),
        "processed_txids": len(processed_txids)
    })

    @zmq_client.on(ZMQTopic.RAW_TX)
    def on_raw_tx(notification):
        from evrmail.wallet.tx import decode_transaction
        tx = decode_transaction(notification.hex)
        txid = tx["txid"]

        if txid not in processed_txids:
            processed_txids.append(txid)
            mark_utxos_as_spent(tx, txid, utxo_cache)
            process_transaction(tx, txid, utxo_cache, is_confirmed=False, debug_mode=debug_mode)
            save_utxos(utxo_cache)
            save_processed_txids(processed_txids)
            chain_log("info", f"💬 Mempool TX: {txid}", details={
                "txid": txid,
                "vins": len(tx.get("vin", [])),
                "vouts": len(tx.get("vout", [])),
                "explorer_link": f"https://explorer.evrmore.org/tx/{txid}"
            })

    @zmq_client.on(ZMQTopic.RAW_BLOCK)
    def on_raw_block(notification):
        from evrmail.wallet.block import decode as decode_block
        from evrmail.wallet.tx import decode_transaction

        block = decode_block(notification.hex)
        tx_count = len(block['tx'])
        
        chain_log("info", f"📦 Received block with {tx_count} transactions", details={
            "block_hash": block.get("hash"),
            "block_height": block.get("height"),
            "tx_count": tx_count,
            "timestamp": block.get("time"),
            "explorer_link": f"https://explorer.evrmore.org/block/{block.get('hash')}"
        })
        
        processed_tx_count = 0
        for tx_hex in block["tx"]:
            tx = decode_transaction(tx_hex)
            txid = tx["txid"]

            moved = move_utxo_from_mempool_to_confirmed(txid, utxo_cache)
            if not moved:
                # Mark existing UTXOs as spent first
                mark_utxos_as_spent(tx, txid, utxo_cache)
                process_transaction(tx, txid, utxo_cache, is_confirmed=True, debug_mode=debug_mode)
                processed_tx_count += 1

            if txid not in processed_txids:
                processed_txids.append(txid)

        save_utxos(utxo_cache)
        save_processed_txids(processed_txids)
        chain_log("info", f"📦 Processed {processed_tx_count} new transactions in block", details={
            "block_hash": block.get("hash"),
            "tx_count": tx_count,
            "processed_tx_count": processed_tx_count,
            "total_processed_txids": len(processed_txids)
        })

    network_log("info", "🌐 Starting ZMQ client...", details={
        "zmq_topics": ["rawtx", "rawblock"],
        "endpoint": f"tcp://{config['rpc_host'].split('tcp://')[1]}:28332"
    })
    zmq_client.start()
    daemon_log("info", "👁️ Starting UTXO monitoring...")
    monitor_confirmed_utxos_realtime()

    daemon_log("info", "✅ Daemon listening for transactions and blocks.", details={
        "total_utxos": total_utxos,
        "known_addresses": len(known_addresses),
        "processed_txids": len(processed_txids)
    })

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        daemon_log("info", "🛑 Shutting down.")
    finally:
        zmq_client.stop_sync()
        rpc_client.close_sync()

# ─── 🚀 Entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
