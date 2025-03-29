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
        ephemeral_pubkey_bytes = base64.b64decode(encrypted["ephemeral_pubkey"])
        nonce = base64.b64decode(encrypted["nonce"])
        ciphertext = base64.b64decode(encrypted["ciphertext"])

        # Reconstruct ephemeral public key
        ephemeral_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256K1(), ephemeral_pubkey_bytes
        )

        # Load recipient's private key
        from evrmail.utils.wif_to_privkey_hex import wif_to_privkey_hex  # or include the function above directly
        recipient_privkey_bytes = bytes.fromhex(wif_to_privkey_hex(recipient_privkey_hex))
        recipient_private_key = ec.derive_private_key(
            int.from_bytes(recipient_privkey_bytes, 'big'),
            ec.SECP256K1()
        )

        # Derive shared secret
        shared_key = recipient_private_key.exchange(ec.ECDH(), ephemeral_pubkey)

        # Use HKDF to derive AES key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"evrmail-encryption"
        ).derive(shared_key)

        # Decrypt message
        aesgcm = AESGCM(derived_key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        # Convert to string and parse JSON
        decrypted_str = decrypted_bytes.decode("utf-8")
        message_json = json.loads(decrypted_str.replace("'", '"'))

        # Decode the base64 content field
        if isinstance(message_json.get("content"), str):
            message_json["content"] = base64.b64decode(message_json["content"]).decode("utf-8")

        return message_json

    except Exception as e:
        raise ValueError(f"Failed to decrypt message: {e}")
