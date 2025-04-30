""" Creating payloads 

    Evrmail batchable, encrypted IPFS payloads. 
    Each individual message payload will be in a batch payload.

    Returns an encrypted message payload:
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

import json
from evrmail.crypto import sign_message
from evrmail.utils.encrypt_message import encrypt_message
from evrmail.utils.get_pubkey import get_pubkey
from evrmail.utils.get_channel_pubkey import get_channel_pubkey
from evrmail.config import load_config
from evrmail.wallet import get_private_key_for_address

def create_message_payload(from_address: str, to: str, subject: str, content: str, encrypted: bool=False) -> dict:
    """
    Create a single encrypted and signed EvrMail message payload.

    Args:
        from_address (str): Sender address.
        to (str): Recipient address (address or channel).
        subject (str): Subject of the message.
        content (str): Message body.

    Returns:
        dict: Encrypted message payload for inclusion in a batch.
    """

    # Build the raw message
    message = {
        "to": to,
        "from": from_address,
        "subject": subject,
        "content": content,
        "encrypted": encrypted
    }

    # Get private key for signing
    privkey = get_private_key_for_address(from_address)
    signature = sign_message(json.dumps(message), privkey)
    message["signature"] = signature

    # Encrypt using recipient pubkey
    try:
        if encrypted:
            encrypted_payload = encrypt_message(message, to, from_address)
            encrypted_payload["to"] = to
            encrypted_payload["from"] = from_address
            encrypted_payload["signature"] = signature
            return encrypted_payload
        else:
            return message
    except Exception as e:
        print("Failed to encrypt message", e)
        raise e
