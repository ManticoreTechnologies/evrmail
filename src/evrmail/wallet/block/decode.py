import struct
import hashlib
from typing import Dict, List

def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def read_varint(f: memoryview, cursor: int) -> (int, int):
    i = f[cursor]
    cursor += 1
    if i < 0xfd:
        return i, cursor
    elif i == 0xfd:
        val = struct.unpack_from('<H', f, cursor)[0]
        cursor += 2
        return val, cursor
    elif i == 0xfe:
        val = struct.unpack_from('<I', f, cursor)[0]
        cursor += 4
        return val, cursor
    else:
        val = struct.unpack_from('<Q', f, cursor)[0]
        cursor += 8
        return val, cursor

def decode(block_hex: str, height: int = None) -> Dict[str, any]:
    block_hex = block_hex.strip().replace('\n', '').replace(' ', '')
    block_bytes = bytes.fromhex(block_hex)
    f = memoryview(block_bytes)

    cursor = 0

    # ─── Block header ───
    version = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    previous_block_hash = f[cursor:cursor+32][::-1].hex()
    cursor += 32

    merkle_root = f[cursor:cursor+32][::-1].hex()
    cursor += 32

    timestamp = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    bits = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    nonce = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    header_bytes = block_bytes[:80]
    block_hash = sha256d(header_bytes)[::-1].hex()
    headerhash = block_hash

    # ─── Mixhash and nonce64 (specific to Evrmore) ───
    mixhash = f[cursor:cursor+32][::-1].hex()
    cursor += 32

    nonce64 = struct.unpack_from('<Q', f, cursor)[0]
    cursor += 8

    # ─── Transaction list ───
    tx_count, cursor = read_varint(f, cursor)
    txs: List[str] = []

    for _ in range(tx_count):
        tx_start = cursor

        # Read version
        _ = struct.unpack_from('<I', f, cursor)[0]
        cursor += 4

        # Peek next two bytes
        marker = f[cursor]
        flag = f[cursor + 1]
        if marker == 0x00 and flag != 0x00:
            # Segwit marker
            segwit = True
            cursor += 2
        else:
            segwit = False

        vin_count, cursor = read_varint(f, cursor)
        for _ in range(vin_count):
            cursor += 32  # prev txid
            cursor += 4   # prev vout
            script_len, cursor = read_varint(f, cursor)
            cursor += script_len
            cursor += 4   # sequence

        vout_count, cursor = read_varint(f, cursor)
        for _ in range(vout_count):
            cursor += 8  # value
            script_len, cursor = read_varint(f, cursor)
            cursor += script_len

        if segwit:
            for _ in range(vin_count):
                wit_count, cursor = read_varint(f, cursor)
                for _ in range(wit_count):
                    wit_size, cursor = read_varint(f, cursor)
                    cursor += wit_size

        cursor += 4  # locktime

        tx_end = cursor
        tx_raw = f[tx_start:tx_end]
        txs.append(tx_raw.hex())

    # ─── Build result ───
    result = {
        "hash": block_hash,
        "strippedsize": len(block_bytes),
        "size": len(block_bytes),
        "weight": len(block_bytes) * 4,
        "height": height,
        "version": version,
        "versionHex": f"{version:08x}",
        "merkleroot": merkle_root,
        "tx": txs,
        "hex": block_hex,
        "time": timestamp,
        "nonce": nonce,
        "bits": f"{bits:08x}",
        "headerhash": headerhash,
        "mixhash": mixhash,
        "nonce64": nonce64,
        "previous_block_hash": previous_block_hash,
    }

    return result