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
from evrmail.wallet import list_wallets, load_wallet, get_private_key_for_address, get_active_address

def create_message_payload(to: str, subject: str, content: str) -> dict:
    """
    Create a single encrypted and signed EvrMail message payload.

    Args:
        to (str): Recipient address (channel).
        subject (str): Subject of the message.
        content (str): Message body.

    Returns:
        dict: Encrypted message payload for inclusion in a batch.
    """
    config = load_config()
    from_address = get_active_address()

    if not from_address:
        raise Exception("⚠️ Active address not set. Use 'evrmail wallet use <address>'.")

    # Build the raw message
    message = {
        "to": to,
        "from": from_address,
        "subject": subject,
        "content": content
    }

    # Get private key for signing
    privkey = get_private_key_for_address(from_address)
    print("Signing message")
    signature = sign_message(json.dumps(message), privkey)
    print("message signed")
    message["signature"] = signature

    # Encrypt using recipient pubkey
    try:
        encrypted_payload = encrypt_message(message, to)
        encrypted_payload["to"] = to
        encrypted_payload["from"] = from_address
        encrypted_payload["signature"] = signature
        return encrypted_payload
    except Exception as e:
        print("Failed to encrypt message", e)
        raise e
