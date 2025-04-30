import struct
import hashlib
from typing import Dict, List, Tuple
from evrmail.wallet import script as script_decoder

def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def read_varint(f: memoryview, cursor: int) -> Tuple[int, int]:
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

def decode_transaction(tx_hex: str) -> Dict[str, any]:
    tx_bytes = bytes.fromhex(tx_hex)
    f = memoryview(tx_bytes)
    cursor = 0

    version = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    # Detect Segwit
    segwit = False
    marker = f[cursor]
    flag = f[cursor + 1]
    if marker == 0x00 and flag != 0x00:
        segwit = True
        marker_flag_cursor = cursor
        cursor += 2

    vin = []
    vin_count, cursor = read_varint(f, cursor)
    vin_start_cursor = cursor

    for _ in range(vin_count):
        txid = f[cursor:cursor+32][::-1].hex()
        cursor += 32
        vout = struct.unpack_from('<I', f, cursor)[0]
        cursor += 4
        script_len, cursor = read_varint(f, cursor)
        script_sig = f[cursor:cursor+script_len].hex()
        cursor += script_len
        sequence = struct.unpack_from('<I', f, cursor)[0]
        cursor += 4

        if txid == "0" * 64:
            vin.append({
                "coinbase": script_sig,
                "sequence": sequence
            })
        else:
            vin.append({
                "txid": txid,
                "vout": vout,
                "scriptSig": {"hex": script_sig},
                "sequence": sequence
            })

    vout = []
    vout_count, cursor = read_varint(f, cursor)
    for n in range(vout_count):
        value = struct.unpack_from('<q', f, cursor)[0]
        cursor += 8
        script_len, cursor = read_varint(f, cursor)
        script_pubkey_bytes = f[cursor:cursor+script_len]
        script_pubkey_hex = script_pubkey_bytes.hex()
        cursor += script_len

        try:
            decoded_script = script_decoder.decode(script_pubkey_hex)
            script_pubkey = decoded_script
            script_pubkey["hex"] = script_pubkey_hex
        except Exception:
            script_pubkey = {
                "hex": script_pubkey_hex,
                "asm": '',
                "type": "unknown"
            }

        vout.append({
            "value": round(value, 8),
            "n": n,
            "scriptPubKey": script_pubkey
        })

    no_witness_cursor = cursor

    if segwit:
        for _ in range(vin_count):
            item_count, cursor = read_varint(f, cursor)
            for _ in range(item_count):
                item_size, cursor = read_varint(f, cursor)
                cursor += item_size

    locktime = struct.unpack_from('<I', f, cursor)[0]
    cursor += 4

    size = cursor

    if segwit:
        stripped_tx = (
            tx_bytes[:marker_flag_cursor] +
            tx_bytes[marker_flag_cursor+2:no_witness_cursor] +
            tx_bytes[cursor-4:cursor]
        )
    else:
        stripped_tx = tx_bytes[:cursor]

    txid = sha256d(stripped_tx)[::-1].hex()

    if segwit:
        txhash = sha256d(tx_bytes[:cursor])[::-1].hex()
    else:
        txhash = txid

    if segwit:
        vsize = (len(stripped_tx) * 3 + size) // 4
    else:
        vsize = size

    return {
        "version": version,
        "locktime": locktime,
        "size": size,
        "vsize": vsize,
        "txid": txid,
        "hash": txhash,
        "vin": vin,
        "vout": vout
    }
