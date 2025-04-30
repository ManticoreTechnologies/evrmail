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

def create_transfer_asset_script(pubkey_hash: bytes, asset_name: str, amount: int, ipfs_cidv0: Optional[str] = None) -> str:
    """
    Constructs a P2PKH + OP_EVR_ASSET transfer script, including proper handling of ownership tokens (!).
    """

    asset_name_bytes = asset_name.encode()
    if asset_name.endswith("!"):
        # ── 🏷️ Ownership token: must be exactly 1 and use OP_TRANSFER_OWNER (0x74)
        if amount != 1e8:
            raise ValueError("Ownership tokens (ending in '!') must be sent with amount = 1")

        asset_payload = (
            b"evr" +
            b"t" +  # transfer
            encode_pushdata(asset_name_bytes) +
            (amount).to_bytes(8, "little")  # fixed to 1
        )

        if ipfs_cidv0:
            multihash_bytes = custom_base58_decode(ipfs_cidv0)
            asset_payload += multihash_bytes
        # Final script with OP_TRANSFER_OWNER (0x74)
        script = (
            bytes.fromhex("76a914") +
            pubkey_hash +
            bytes.fromhex("88ac") +
            b"\xc0" +
            encode_pushdata(asset_payload) +
            b"\x74"  # OP_TRANSFER_OWNER
        )

    else:
        # ── 🪙 Regular asset transfer
        asset_payload = (
            b"evr" +
            b"t" +
            encode_pushdata(asset_name_bytes) +
            amount.to_bytes(8, "little")
        )

        if ipfs_cidv0:
            multihash_bytes = custom_base58_decode(ipfs_cidv0)
            asset_payload += multihash_bytes

        script = (
            bytes.fromhex("76a914") +
            pubkey_hash +
            bytes.fromhex("88ac") +
            b"\xc0" +
            encode_pushdata(asset_payload) +
            b"\x75"  # OP_TRANSFER
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

from typing import Optional
from evrmail.wallet.utils import encode_pushdata

def create_swap_script(
    hash_of_secret_hex: str,
    recipient_pubkey_hash_hex: str,
    refund_pubkey_hash_hex: str,
    locktime: int,
    asset_name: Optional[str] = None,
    asset_amount: Optional[int] = None,
    is_ownership_token: bool = False,
    ipfs_cidv0: Optional[str] = None
) -> str:
    # Construct the asset payload
    asset_payload = b'evr' + b't' + encode_pushdata(asset_name.encode()) + asset_amount.to_bytes(8, 'little')
    if ipfs_cidv0:
        asset_payload += custom_base58_decode(ipfs_cidv0)
    asset_script = b'\xc0' + encode_pushdata(asset_payload) + b'\x75'  # OP_EVR_ASSET <data> OP_DROP

    # Construct the HTLC script
    htlc_script = (
        b'\xa9' + b'\x14' + bytes.fromhex(hash_of_secret_hex) + b'\x87' +  # OP_HASH160 <hash> OP_EQUAL
        b'\x63' +  # OP_IF
            b'\x76\xa9\x14' + bytes.fromhex(recipient_pubkey_hash_hex) + b'\x88\xac' +  # P2PKH
        b'\x67' +  # OP_ELSE
            locktime.to_bytes(4, 'little') + b'\xb1\x75' +  # <locktime> OP_CHECKLOCKTIMEVERIFY OP_DROP
            b'\x76\xa9\x14' + bytes.fromhex(refund_pubkey_hash_hex) + b'\x88\xac' +  # P2PKH
        b'\x68'  # OP_ENDIF
    )

    # Combine asset script and HTLC script
    full_script = asset_script + htlc_script
    return full_script.hex()
