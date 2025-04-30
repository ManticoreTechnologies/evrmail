import json
import base64
import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from evrmore_rpc import EvrmoreClient
from evrmail.config import load_config
from evrmail.wallet.addresses.get_address import get_address 

config = load_config()
def get_channel_pubkey(channel_name):
    """Look up the address that owns a message channel, and fetch its pubkey."""
    client = EvrmoreClient()
    addresses = client.listaddressesbyasset(channel_name)
    if not addresses:
        raise ValueError(f"No addresses found for channel: {channel_name}")
    address = list(addresses.keys())[0]
    address_info = client.validateaddress(address)
    return address_info.get("pubkey", address_info.get("scriptPubKey"))

def encrypt_message(message_json: dict, to_address: str, from_address: str=config.get('active_address')):

    # First we outta encode the content in base64
    message_json["content"] = base64.b64encode(message_json["content"].encode()).decode()
    
    from evrmail.config import load_config
    config = load_config()
    contacts = config.get('contacts')

    if len(contacts) == 0:
        raise Exception("You do not have any contacts. Add one with evrmail blockchain contacts add <address> <pubkey> (friendly_name)")
    from evrmail.wallet.addresses import validate
    to = to_address
    valid = validate(to)
    to_address = None
    if valid.get('isvalid'):
        # user provided an evrmore address
        from evrmail.config import load_config
        config = load_config()
        contacts = config.get("contacts")
        for contact in contacts:
            if contact == to:
                to_address = to
                to_pubkey = contacts.get(contact).get("pubkey")

        if not to_address:
            print(f"{to} is not in your contacts")
            raise Exception(f"{to} is not in your contacts")

    else:
        # user did not provide evrmore address, lets assume its a friendly name
        from evrmail.config import load_config
        config = load_config()
        contacts = config.get("contacts")
        for contact in contacts:
            if contacts.get(contact).get("friendly_name") == to:
                to_address = contact
                to_pubkey = contacts.get(contact).get("pubkey")
        if not to_address:
            print(f"{to} is not in your contacts")
            raise Exception(f"{to} is not in your contacts")
            
    recipient_pubkey_hex = contacts.get(to_address).get('pubkey')
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
    ciphertext = aesgcm.encrypt(nonce, str(message_json).encode(), None)

    # Return ephemeral pubkey, nonce, and ciphertext
    ephemeral_pubkey_bytes = ephemeral_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    address_data = get_address(from_address)
    from_publickey = address_data.get("public_key")

    encrypted_payload = {
        "to": None,
        "from": None,
        "to_pubkey": recipient_pubkey_hex,
        "from_pubkey": from_publickey,
        "ephemeral_pubkey": base64.b64encode(ephemeral_pubkey_bytes).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "signature": message_json.get("signature")
    }
    return encrypted_payload

def encode_message(message):
    """
    Encrypt a message using the pubkey of the recipient's outbox channel.
    """
    pubkey = get_channel_pubkey(message['to'])
    print(f"Using recipient pubkey: {pubkey}")
    message_str = json.dumps(message, sort_keys=True)
    return encrypt_message(message_str, pubkey)

