from evrmail.config import load_config
import json
import time
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.wif_to_privkey_hex import wif_to_privkey_hex
config = load_config()

""" Decrypting payloads 

    Evrmail batchable, encrypted IPFS payloads. 
    Each individual message payload will be in a batch payload.

    Individual message payload:
    {
        'to': str                   # The address this payload is for
        'from': str,                # The address this payload is from
        'to_pubkey': str,           # The pubkey this payload is for 
        'from_pubkey': str,         # The pubkey this payload is from
        'ephemeral_pubkey': str,    # The ephemeral pubkey of the payload
        'nonce': str,               # The hex string nonce of the payload
        'ciphertext': str,          # The encrypted payload message 
        'signature': str            # The senders signature of the message    
    }

"""
""" Flow to send a message """

# Create a message payload
from evrmail.utils.create_message_payload import create_message_payload
my_message = create_message_payload(
    "EL3BmmjmDa5LNMmF8fE4smdfxLmi8EJJMR", # To address
    "Subject here",                       # Subject
    "content"                             # Body content
)

# Create a batch payload
from evrmail.utils.create_batch_payload import create_batch_payload
my_batch = create_batch_payload(
    [my_message]
)

# Add the payload to ipfs
from evrmail.utils.ipfs import add_to_ipfs
my_batch_cid = add_to_ipfs(my_batch)


# Now we can scan our payload
from evrmail.utils.scan_payload import scan_payload
my_messages = scan_payload(my_batch_cid)
print(my_messages)

# Then you can save the message to the inbox directory 
from evrmail.utils.inbox import save_messages
save_messages(my_messages)




# Send the message using an asset




# Check if the message is to the outbox
#if str(msg_json['to']) in config['addresses']:
#    # Decode the message
#    print(f"💌 Message received from {msg_json.get('from')} to {msg_json.get('to')}")
#    print(config['addresses'].get(msg_json['to']))
#    privkey = wif_to_privkey_hex(config['addresses'].get(msg_json['to']).get('privkey'))
#    decrypted_json = decrypt_message(msg_data, privkey)
#    decrypted_json["cid"] = "cid"
#    decrypted_json["received_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
#    decrypted_json["read"] = False
#    messages.append(decrypted_json)
#    print(messages)

