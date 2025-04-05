from cryptography.hazmat.primitives.asymmetric import ec
import json
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from evrmail.config import load_config

config = load_config()


import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def decrypt_message(encrypted: dict, recipient_privkey_hex: str) -> dict:
    """
    Decrypts an encrypted EvrMail payload using the recipient's private key.

    Args:
        encrypted (dict): The encrypted message payload.
        recipient_privkey_hex (str): The recipient's private key in hex.

    Returns:
        dict: The decrypted message as a JSON object.
    """
    try:
        # Decode base64-encoded fields
        def safe_b64decode(data):
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            return base64.b64decode(data)

        ephemeral_pubkey_bytes = safe_b64decode(encrypted["ephemeral_pubkey"])
        nonce = safe_b64decode(encrypted["nonce"])
        ciphertext = safe_b64decode(encrypted["ciphertext"])

        # Reconstruct ephemeral public key
        ephemeral_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256K1(), ephemeral_pubkey_bytes
        )

        # Load recipient's private key from hex (not WIF!)
        recipient_privkey_bytes = bytes.fromhex(recipient_privkey_hex)
        recipient_private_key = ec.derive_private_key(
            int.from_bytes(recipient_privkey_bytes, 'big'),
            ec.SECP256K1()
        )

        # Derive shared secret
        shared_key = recipient_private_key.exchange(ec.ECDH(), ephemeral_pubkey)

        # Derive AES key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"evrmail-encryption"
        ).derive(shared_key)

        # Decrypt with AES-GCM
        aesgcm = AESGCM(derived_key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        # Convert to JSON
        decrypted_str = decrypted_bytes.decode("utf-8")
        message_json = json.loads(decrypted_str.replace("'", "\""))

        # Decode base64 content if needed
        if isinstance(message_json.get("content"), str):
            message_json["content"] = base64.b64decode(message_json["content"]).decode("utf-8")

        return message_json

    except Exception as e:
        raise ValueError(f"Failed to decrypt message: {e}")
