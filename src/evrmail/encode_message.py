"""
🔐 EvrMail Encryption Utility

Encrypt a signed EvrMail message using the recipient's public key derived 
from their messaging channel (asset-based identity).

📥 Input:
  - A signed message (JSON)
  - Channel name (e.g., INBOX~CYMOS)

📤 Output:
  - Base64-encoded encrypted payload: ephemeral pubkey, nonce, ciphertext

🧠 Uses:
  - secp256k1 ECDH
  - HKDF (SHA256)
  - AES-GCM
"""

# ─── 🧩 IMPORTS ────────────────────────────────────────────────────────────────

import json
import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec

from evrmore_rpc import EvrmoreClient

# ─── ✉️ SAMPLE SIGNED MESSAGE ──────────────────────────────────────────────────

signed_message = {
    "to": "EdpZbz45Gj9UXrLDJzCSDYa3MW7ZjXAKF1",          # recipient address
    "from": "Eae2fWmwapTa3PqF2t3hbsujZLrYjzdbru",      # sender address
    "subject": "Hey what's up",                        # subject of the message
    "timestamp": "2025-03-24T18:35:00Z",               # timestamp of the message
    "content": "Hey bro, just testing this message system!", # content of the message
    "signature": "H6EwxKzBbpp19G8s81QLtaLbJUwv+HXI+e3V6wM/hveFP9nVI+qWyQjZw9VKdtIxJAmyWSiDZarjgfZUKSu/sBw=" # signature of the message
}

# ─── 🔑 GET RECIPIENT PUBKEY ──────────────────────────────────────────────────

def get_channel_pubkey(channel_name: str) -> str:
    """
    🔍 Look up the Evrmore address that owns a channel and return its public key.
    """
    client = EvrmoreClient()
    addresses = client.listaddressesbyasset(channel_name)
    if not addresses:
        raise ValueError(f"❌ No addresses found for channel: {channel_name}")
    
    address = list(addresses.keys())[0]
    address_info = client.validateaddress(address)
    
    return address_info.get("pubkey", address_info.get("scriptPubKey"))

# ─── 🔐 ENCRYPTION FUNCTION ───────────────────────────────────────────────────

def encrypt_message_with_pubkey(message_json: str, recipient_pubkey_hex: str) -> str:
    """
    🔐 Encrypt a JSON message string with recipient's secp256k1 pubkey.
    """
    recipient_pubkey_bytes = bytes.fromhex(recipient_pubkey_hex)
    recipient_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), recipient_pubkey_bytes)

    # 🧪 Generate ephemeral keypair & ECDH shared secret
    ephemeral_private_key = ec.generate_private_key(ec.SECP256K1())
    shared_key = ephemeral_private_key.exchange(ec.ECDH(), recipient_pubkey)

    # 🧬 Derive AES key via HKDF
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"evrmail-encryption"
    ).derive(shared_key)

    # 🛡️ Encrypt using AES-GCM
    aesgcm = AESGCM(derived_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message_json.encode(), None)

    # 📤 Encode ephemeral pubkey
    ephemeral_pubkey_bytes = ephemeral_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    encrypted_payload = {
        "ephemeral_pubkey": base64.b64encode(ephemeral_pubkey_bytes).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }

    return json.dumps(encrypted_payload, indent=2)

# ─── ✉️ MAIN ENCODER ───────────────────────────────────────────────────────────

def encode_message(message: dict) -> str:
    """
    🔒 Encrypt a message using the recipient's messaging channel pubkey.
    """
    pubkey = get_channel_pubkey(message["to"])
    print(f"🔑 Using recipient pubkey: {pubkey}")
    
    message_str = json.dumps(message, sort_keys=True)
    return encrypt_message_with_pubkey(message_str, pubkey)

# ─── 🚀 ENTRYPOINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    encrypted = encode_message(signed_message)
    print("🔐 Encrypted Message:")
    print(encrypted)
