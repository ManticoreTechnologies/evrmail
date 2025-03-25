from cryptography.hazmat.primitives.asymmetric import ec
import json
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from evrmail.config import load_config

config = load_config()

message = "{'to': 'INBOX~CYMOS', 'from': 'INBOX~CYMOS', 'subject': '', 'timestamp': '2025-03-25T05:57:39.001616Z', 'content': '# Delete this and type your message here', 'signature': 'IMROKrP64cO8fPW+13OGqT8kfqmdhntsijkYtXVtELSzB3C4u7LVwQFpZ+JLQMylYqitpIjhvwqv/DZv9bTOuXQ='}"
message2 = '{"to": "0278999378c33cc82140bcbe247167ebb01c7e39439d4a59ffa94830db98010629", "from": "0278999378c33cc82140bcbe247167ebb01c7e39439d4a59ffa94830db98010629", "ephemeral_pubkey": "BGUQ8YDc5eZOUkjxVRpdSIVkLn4Ju/OZUDQ1tSeNAeQuudRrdBYUDGgszPIhNt+N6yZ2vB90heN3NDL7OMjv2L4=", "nonce": "+5WY3egdADe8Ms1F", "ciphertext": "RmJeL9+Pj0s2J24UTtKjoLs/6VhlVZ3PYwbBqJH00cSut3PSoTC0t3yig+35upheE8BvgkyJ9FKkKKdrPvJSu/2GzC7IUw8K03wL6ZlR1Mj21veLtwYp/v87UCHOhKnQPRIB71OR7UbIJG3YKvI3UdZrB+nJrGW08lGE1Ov1VET5g58/WWBDXgoFiHY7ScajExKj1uaUG7WL6gOyQfjIXrWsb1HfQMJyXjfX+vfki8YuXsof8tH0DnnFwTtn63KlblkX7izN80O9bslUHttnYBLRMIJKKV5HzKLUcMrveF9dhwuRIInkDD1vaxYOrcwBogcUl1m6xPqrgDG6C6mroD43UMPUOmjO5CkR1NFrTA9rLb55EnGE", "signature": "IMROKrP64cO8fPW+13OGqT8kfqmdhntsijkYtXVtELSzB3C4u7LVwQFpZ+JLQMylYqitpIjhvwqv/DZv9bTOuXQ="}'
def decrypt_message(encrypted_json, recipient_privkey_hex: str):
    print(encrypted_json)
    print("Decrypting message")
    if isinstance(encrypted_json, str):
        encrypted = json.loads(encrypted_json)
    else:
        encrypted = encrypted_json

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
    return json.loads(decrypted_bytes.decode("utf-8"))

print(decrypt_message(str(message2), config['outbox_privkey']))

