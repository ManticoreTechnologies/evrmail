import json
import subprocess
from evrmore_rpc import EvrmoreClient

client = EvrmoreClient()

message = {
    "to": "INBOX~CYMOS",
    "from": "INBOX~PHOENIX",
    "subject": "Hey what's up",
    "timestamp": "2025-03-24T18:35:00Z",
    "content": "Hey bro, just testing this message system!"
}

# Step 1: Sort keys and serialize
message_str = json.dumps(message, sort_keys=True)

# Step 2: Sign using `evrmore-cli signmessage`
address = "Eci1daTpnUKi7QtrMEMzamGcv8BKRLUeWZ"  # Must correspond to the private key
signature = client.signmessage(address, message_str)


# Step 3: Add the signature back
message["signature"] = signature

# Step 4: You can now upload this signed JSON to IPFS
print(json.dumps(message, indent=2))

# Step 5: Save to file
with open("message.json", "w") as f:
    json.dump(message, f, indent=2)