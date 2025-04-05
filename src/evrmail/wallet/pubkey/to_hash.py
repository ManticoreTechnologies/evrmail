from Crypto.Hash import RIPEMD160
import hashlib

def to_hash(pubkey_hex: str) -> str:
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    sha256 = hashlib.sha256(pubkey_bytes).digest()
    ripemd160 = RIPEMD160.new(sha256).digest()
    return ripemd160.hex()
