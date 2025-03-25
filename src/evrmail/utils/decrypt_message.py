from cryptography.hazmat.primitives.asymmetric import ec
import json
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from evrmail.config import load_config

config = load_config()

import base58
import hashlib



def decrypt_message(encrypted_json: str, recipient_privkey_hex: str):
    """
    Decrypts a message given the recipient's private key in hex.
    """
    encrypted = json.loads(encrypted_json)

    ephemeral_pubkey_bytes = base64.b64decode(encrypted["ephemeral_pubkey"])
    nonce = base64.b64decode(encrypted["nonce"])
    ciphertext = base64.b64decode(encrypted["ciphertext"])

    ephemeral_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256K1(), ephemeral_pubkey_bytes
    )

    recipient_privkey_bytes = bytes.fromhex(recipient_privkey_hex)
    recipient_private_key = ec.derive_private_key(
        int.from_bytes(recipient_privkey_bytes, 'big'),
        ec.SECP256K1()
    )

    shared_key = recipient_private_key.exchange(ec.ECDH(), ephemeral_pubkey)

    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"evrmail-encryption"
    ).derive(shared_key)

    aesgcm = AESGCM(derived_key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    decrypted_json = json.loads(decrypted_bytes.decode("utf-8").replace("'", '"'))
    decrypted_json["content"] = base64.b64decode(decrypted_json["content"]).decode("utf-8")
    return decrypted_json
