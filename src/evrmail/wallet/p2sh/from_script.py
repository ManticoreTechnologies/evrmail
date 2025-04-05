import hashlib
import base58
from Crypto.Hash import RIPEMD160

def base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()

def from_script(script_hex: str) -> str:
    """
    Given a full scriptPubKey (hex), return its P2SH address for Evrmore.
    """
    script_bytes = bytes.fromhex(script_hex)
    sha256_digest = hashlib.sha256(script_bytes).digest()
    ripemd160_digest = RIPEMD160.new(sha256_digest).digest()

    evr_p2sh_prefix = bytes([0x5c])  # Evrmore mainnet P2SH = 0x5c
    payload = evr_p2sh_prefix + ripemd160_digest
    return base58check_encode(payload)
