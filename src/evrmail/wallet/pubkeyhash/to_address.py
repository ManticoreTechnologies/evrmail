import hashlib
import base58

def base58check_encode(payload: bytes) -> str:
    """Base58Check encoding used by Evrmore for addresses."""
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()

def to_address(pubkey_hash_hex: str, addr_type: str = "p2pkh") -> str:
    """
    Convert a public key hash to a valid Evrmore address.
    
    :param pubkey_hash_hex: hex string (20 bytes)
    :param addr_type: 'p2pkh' or 'p2sh'
    :return: Evrmore base58 address
    """
    pubkey_hash = bytes.fromhex(pubkey_hash_hex)
    prefixes = {
        "p2pkh": b'\x21',  # 0x21 = 33 = P2PKH (starts with E)
        "p2sh": b'\x5c'    # 0x5c = 92 = P2SH (starts with e)
    }
    prefix = prefixes.get(addr_type)
    if prefix is None:
        raise ValueError("Unsupported address type: must be 'p2pkh' or 'p2sh'")
    
    return base58check_encode(prefix + pubkey_hash)

