
import json
import os
import subprocess
import time
from pathlib import Path
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmail.config import load_config   
from evrmail.utils.decrypt_message import decrypt_message
config = load_config()
from evrmail.daemon import load_inbox, save_inbox, load_processed_txids, save_processed_txids, read_message

STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("📡 evrmail Daemon Starting...")
    rpc = EvrmoreClient()
    zmq = EvrmoreZMQClient()

    @zmq.on(ZMQTopic.TX)
    def on_transaction(notification):
        # FIrst store the txid so we can check if the message is already processed
        txid = notification.tx.get("txid")
        #load the processed txids
        processed_txids = load_processed_txids()
        #check if the txid is already processed
        if txid in processed_txids:
            # ignore the message if it is already processed
            return
        #save the txid
        processed_txids.append(txid)
        save_processed_txids(processed_txids)
        #load the inbox
        messages = load_inbox()
        for vout in notification.tx.get("vout", []):
            script = vout.get("scriptPubKey", {})
            if script.get("type") == "transfer_asset":
                asset = script.get("asset", {})
                cid = asset.get("message")
                if cid and all(msg["cid"] != cid for msg in messages):
                    msg_data = read_message(cid)
                    if msg_data:
                        """ 
                            A message is a JSON object, we expect the following fields:
                            - from: str - The address of the sender
                            - to: str - The address of the recipient
                            - subject: str - The subject of the message
                            - content: str - The content of the message
                            - timestamp: str - The timestamp of the message
                            - signature: str - The signature of the message

                            evrmail will add the following fields:
                            - cid: str - The CID of the message
                            - received_at: str - The timestamp of when the message was received
                        """
                        try:
                            # First we need to decode the message, its encoded using our address that owns the outbox
                            # We need to get the pubkey of the outbox address
                            outbox_pubkey = config['outbox_pubkey']
                            
                            msg_json = json.loads(msg_data)

                            # Check if the message is to the outbox
                            if str(msg_json['to']) == str(config['outbox_pubkey']):
                                # Decode the message
                                print(f"💌 Message received from {msg_json.get('from')} to {msg_json.get('to')}")
                                decrypted_json = decrypt_message(msg_data, config['outbox_privkey'])
                                decrypted_json["cid"] = cid
                                decrypted_json["received_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                decrypted_json["read"] = False
                                messages.append(decrypted_json)
                                save_inbox(messages)
                        except json.JSONDecodeError:
                            print(f"⚠️ Invalid JSON in message: {cid}")

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