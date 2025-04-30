""" Creating batch payloads 

    Evrmail uses batchable, encrypted IPFS payloads. 
    Each individual message payload will be in a batch payload.

    Batch payload:
    {
        "batch_id": str,            # Optional: UUID or hash
        "created": str,             # ISO 8601 UTC timestamp
        "sender": str,              # Sender's address
        "sender_pubkey": str,       # Cached sender pubkey (for audit)
        "version": 1,               # For protocol upgrades
        "messages": [               # Array of individual encrypted messages
            {message_payload},      # An individual message payload
            {message_payload}
            ...
        ]
    }

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

import uuid
from datetime import datetime
from evrmail.config import load_config

def create_batch_payload(from_address: str, message_payloads: list) -> dict:
    """
    Assemble a batch payload from individual encrypted message payloads.

    Args:
        message_payloads (list): A list of encrypted message payloads.

    Returns:
        dict: Full batch payload ready for IPFS.
    """
    from evrmail.wallet.addresses.get_address import get_address

    if not from_address:
        raise Exception("⚠️ From address not set, cannot create batch payload.")

    sender_info = get_address(from_address)
    if not sender_info:
        raise Exception(f"⚠️ Address {from_address} is not found.")

    sender_pubkey = sender_info.get("public_key")
    if not sender_pubkey:
        raise Exception(f"⚠️ No pubkey found for address {from_address}.")

    batch_payload = {
        "batch_id": str(uuid.uuid4()),
        "created": datetime.utcnow().isoformat() + "Z",
        "sender": from_address,
        "sender_pubkey": sender_pubkey,
        "version": 1,
        "messages": message_payloads
    }

    return batch_payload
