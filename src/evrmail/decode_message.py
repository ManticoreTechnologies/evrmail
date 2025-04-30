"""
🔐 EvrMail Decryption Utility

Decrypt a secure EvrMail message using ECIES (secp256k1 + AES-GCM + HKDF).

📥 Input: 
  - Base64-encoded ephemeral pubkey, nonce, and ciphertext.
  - Recipient's private key (hex format).

📤 Output:
  - Decrypted plaintext message.

🧠 Note: This uses the `outbox_privkey` from config as the recipient's private key.
"""

# ─── 🧩 IMPORTS ────────────────────────────────────────────────────────────────

import json
import base64
import base58
import hashlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec

from evrmail.config import load_config
from evrmail.utils import wif_to_privkey_hex

# ─── ⚙️ LOAD CONFIG ────────────────────────────────────────────────────────────

config = load_config()

# 🧪 Sample encrypted message
encoded_message = {
    "ephemeral_pubkey": "BCGecyiueUgYvfM8Om+sIpvHM8QycFeD4lSJ+Wt/4nXIIg9GzFclpcFcciVu5k7zb6i6o+1zj8TpihdcvVI4/g8=",
    "nonce": "Da1sESeHvloVQS/f",
    "ciphertext": "+ptbKm2uTn9VDxymZdJY+/dKjte7tUI/iUsr7olnaKDbnv8r2FwSHAQ8TGbBXbd6vkNdsa0L7TXEmvUvDgKpa3/03onH3dJJvyeEnWL7SWSt28VO9SP6SEn2Ll5zih/pnMIUhnmjD5dQVBxJiG8TJ24oN4j2FH9wgjGEtdme6pDk5XnhgEzIzXiarmKNeTQOJztRs3ryu4ZsEvtyRlcN+Vh3eMR/GHjhVSh9r6hd1jM2LGQ3H8GJ7THPR9Si2D4Kjp0Y+w+24s33/4r7a6RMgQwKBFZNPq98YOwKN/HDvBH1k7NTiJRfa/9aF0A0sTkK8UACSHNkaS5qKRZOUaoucPZDPlQaaf0/cD+uyRrVGsvj8Wh3+cJOQA44wLFt5scSHQ=="
}

# ─── 🔓 DECRYPTION FUNCTION ────────────────────────────────────────────────────

def decrypt_message(
    encrypted_json: dict = encoded_message,
    recipient_privkey_hex: str = wif_to_privkey_hex(config['outbox_privkey'])
) -> str:
    """
    🧠 Decrypts an encrypted EvrMail message using ECIES.

    📌 Args:
        encrypted_json (dict): The encoded message dict (with base64 keys).
        recipient_privkey_hex (str): Hex-encoded private key for decryption.

    🔓 Returns:
        str: Decrypted plaintext message.
    """
    # 🔓 Decode base64 fields
    ephemeral_pubkey_bytes = base64.b64decode(encrypted_json["ephemeral_pubkey"])
    nonce = base64.b64decode(encrypted_json["nonce"])
    ciphertext = base64.b64decode(encrypted_json["ciphertext"])

    # 🔑 Derive keys
    ephemeral_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256K1(), ephemeral_pubkey_bytes
    )
    recipient_privkey_bytes = bytes.fromhex(recipient_privkey_hex)
    recipient_private_key = ec.derive_private_key(
        int.from_bytes(recipient_privkey_bytes, 'big'), ec.SECP256K1()
    )
    shared_key = recipient_private_key.exchange(ec.ECDH(), ephemeral_pubkey)

    # 🔐 Derive AES key from shared secret
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"evrmail-encryption"
    ).derive(shared_key)

    # 🔓 Decrypt message
    aesgcm = AESGCM(derived_key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

    return decrypted_bytes.decode("utf-8")


# ─── 🚀 ENTRYPOINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔓 Decrypted Message:")
    print(decrypt_message())
