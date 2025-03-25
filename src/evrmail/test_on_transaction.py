from evrmail.daemon import load_inbox, read_message
import json
import time
from evrmail.daemon import load_config
config = load_config()


test_notification = {
    "vout": [
        {
            "scriptPubKey": {
                "type": "transfer_asset",
                "asset": {
                    "message": "QmeMNDWLPrbG9n17i2R267961FtbBWbBhXAdo5Z9idB4UV"
                }
            }
        }
    ]
}
def on_transaction(notification=test_notification):
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
                        msg_json["cid"] = cid
                        msg_json["received_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        messages.append(msg_json)
                        print(messages)
                        print(f"💌 Message received from {msg_json.get('from')} to {msg_json.get('to')}")
                    except json.JSONDecodeError:
                        print(f"⚠️ Invalid JSON in message: {cid}")