signed_message = {
  "to": "INBOX~CYMOS",
  "from": "INBOX~PHOENIX",
  "subject": "Hey what's up",
  "timestamp": "2025-03-24T18:35:00Z",
  "content": "Hey bro, just testing this message system!",
  "signature": "H6EwxKzBbpp19G8s81QLtaLbJUwv+HXI+e3V6wM/hveFP9nVI+qWyQjZw9VKdtIxJAmyWSiDZarjgfZUKSu/sBw="
}

import json
import base64
import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from evrmore_rpc import EvrmoreClient

def get_channel_pubkey(channel_name):
    """Look up the address that owns a message channel, and fetch its pubkey."""
    client = EvrmoreClient()
    addresses = client.listaddressesbyasset(channel_name)
    if not addresses:
        raise ValueError(f"No addresses found for channel: {channel_name}")
    address = list(addresses.keys())[0]
    address_info = client.validateaddress(address)
    return address_info.get("pubkey", address_info.get("scriptPubKey"))

def encrypt_message_with_pubkey(message_json: str, recipient_pubkey_hex: str):
    recipient_pubkey_bytes = bytes.fromhex(recipient_pubkey_hex)
    recipient_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), recipient_pubkey_bytes)

    # Generate ephemeral private key
    ephemeral_private_key = ec.generate_private_key(ec.SECP256K1())
    shared_key = ephemeral_private_key.exchange(ec.ECDH(), recipient_pubkey)

    # Derive a symmetric key
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"evrmail-encryption"
    ).derive(shared_key)

    aesgcm = AESGCM(derived_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message_json.encode(), None)

    # Return ephemeral pubkey, nonce, and ciphertext
    ephemeral_pubkey_bytes = ephemeral_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    encrypted_payload = {
        "ephemeral_pubkey": base64.b64encode(ephemeral_pubkey_bytes).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }
    return json.dumps(encrypted_payload)

def encode_message(message):
    """
    Encrypt a message using the pubkey of the recipient's outbox channel.
    """
    pubkey = get_channel_pubkey(message['to'])
    print(f"Using recipient pubkey: {pubkey}")
    message_str = json.dumps(message, sort_keys=True)
    return encrypt_message_with_pubkey(message_str, pubkey)

if __name__ == "__main__":
    encoded = encode_message(signed_message)
    print("Encrypted Message:")
    print(encoded)
