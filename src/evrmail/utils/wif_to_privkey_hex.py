import base58
import hashlib

def wif_to_privkey_hex(wif: str) -> str:
    """Convert a WIF key to a raw private key hex (for secp256k1 curve)."""
    decoded = base58.b58decode(wif)
    if decoded[0] != 0x80:
        raise ValueError("Invalid WIF version byte (expected 0x80)")
    
    # Check for compressed flag (last byte = 0x01) → 34 bytes + 4 byte checksum = 38
    if len(decoded) == 38 and decoded[-5] == 0x01:
        privkey_bytes = decoded[1:-5]
    else:
        privkey_bytes = decoded[1:-4]

    # Validate checksum
    checksum = decoded[-4:]
    expected_checksum = hashlib.sha256(hashlib.sha256(decoded[:-4]).digest()).digest()[:4]
    if checksum != expected_checksum:
        raise ValueError("Invalid WIF checksum")

    return privkey_bytes.hex()