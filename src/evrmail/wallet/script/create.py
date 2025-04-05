"""

Transaction scripts found in the wild for reference:

============================== New Asset ==============================
"scriptPubKey": {
    "asm": "OP_DUP OP_HASH160 47c96b6fd7c4e0666963a4a50a1f3c68b320290c OP_EQUALVERIFY OP_CHECKSIG OP_EVR_ASSET 146576727104534d545000e1f5050000000000010075",
    "hex": "76a91447c96b6fd7c4e0666963a4a50a1f3c68b320290c88acc0146576727104534d545000e1f5050000000000010075",
    "reqSigs": 1,
    "type": "new_asset",
    "asset": {
        "name": "SMTP",
        "amount": 1.00000000,
        "expire_time": 3,
        "units": 0,
        "reissuable": 1
    },
    "addresses": [
        "EPhUm668y6CZ9hJABgBbCMqjDXrM1FLWf2"
    ]
}

"""



from typing import Optional
from evrmail.wallet.utils import encode_pushdata
def custom_base58_decode(s: str) -> bytes:
    """ Decodes base58 string (e.g., IPFS CIDv0) into exact multihash bytes (typically 34 bytes) """
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    base = 58

    num = 0
    for char in s:
        num *= base
        num += alphabet.index(char)

    # Convert number to bytes
    full_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')

    # Handle leading zeroes (from base58 '1')
    n_pad = len(s) - len(s.lstrip('1'))
    decoded = b'\x00' * n_pad + full_bytes

    if len(decoded) != 34:
        raise ValueError(f"Invalid multihash length: expected 34 bytes, got {len(decoded)}")

    return decoded



def create_p2pkh_script(pubkey_hash_hex: str) -> str:
    # Standard format: OP_DUP OP_HASH160 <pubkeyhash> OP_EQUALVERIFY OP_CHECKSIG
    return (
        "76" +                      # OP_DUP
        "a9" +                      # OP_HASH160
        "14" +                      # push 20 bytes
        pubkey_hash_hex.lower() +
        "88" +                      # OP_EQUALVERIFY
        "ac"                        # OP_CHECKSIG
    )

def create_transfer_asset_script(pubkey_hash_hex: str, asset_name: str, amount: int, ipfs_cidv0: Optional[str] = None) -> str:
    """
    Properly constructs a P2PKH + OP_EVR_ASSET transfer script using valid pushdata encoding.
    """
    asset_name_bytes = asset_name.encode()
    asset_payload = (
        b"evr" +
        b"t" +
        encode_pushdata(asset_name_bytes) +
        amount.to_bytes(8, "little")
    )

    if ipfs_cidv0:
        multihash_bytes = custom_base58_decode(ipfs_cidv0)
        asset_payload += multihash_bytes

    # Final script = standard P2PKH + OP_EVR_ASSET + pushdata
    script = (
        bytes.fromhex("76a914") +
        bytes.fromhex(pubkey_hash_hex.lower()) +
        bytes.fromhex("88ac") +
        b"\xc0" +
        encode_pushdata(asset_payload) +
        b"\x75"  # OP_DROP
    )

    return script.hex()



def create_issue_asset_script(pubkey_hash_hex: str, asset_name: str, amount: int, divisions: int, reissuable: bool, ipfs_hash_hex: Optional[str] = None) -> str:
    asset_name_bytes = asset_name.encode()
    asset_payload = (
        b"evr" +
        b"q" +  # 'q' = issue
        bytes([len(asset_name_bytes)]) +
        asset_name_bytes +
        amount.to_bytes(8, "little") +
        bytes([divisions]) +
        bytes([1 if reissuable else 0]) +
        bytes([1 if ipfs_hash_hex else 0])
    )
    if ipfs_hash_hex:
        asset_payload += b'\x12\x20' + bytes.fromhex(ipfs_hash_hex)

    pushdata_len = len(asset_payload)
    script = (
        "76a914" + pubkey_hash_hex.lower() + "88ac" +
        "c0" +
        f"{pushdata_len:02x}" +
        asset_payload.hex()
    )
    return script
