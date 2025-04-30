import binascii
from typing import Dict, Any
from .. import pubkeyhash
from .. import p2sh

def decode(script_hex: str) -> Dict[str, Any]:
    """
    Decode Evrmore scriptPubKey hex into detailed fields.

    Supports:
    - Standard P2PKH outputs
    - Standard P2SH outputs
    - OP_RETURN (nulldata)
    - OP_EVR_ASSET (with asset fields parsed)
    """
    result: Dict[str, Any] = {}
    print("SCRIPTHEX---")
    print(script_hex)
    print("SCRIPTHEXEND")
    script = bytes.fromhex(script_hex)

    if not script:
        result.update({
            'type': 'nonstandard',
            'hex': script_hex,
            'asm': '',
        })
        return result

    # ─── Handle OP_RETURN (nulldata) ───
    if script[0] == 0x6a:  # OP_RETURN
        try:
            if len(script) > 1:
                push_opcode = script[1]
                if push_opcode <= 75:
                    data = script[2:2+push_opcode]
                    asm = f"OP_RETURN {data.hex()}"
                elif push_opcode == 0x4c:  # OP_PUSHDATA1
                    real_len = script[2]
                    data = script[3:3+real_len]
                    asm = f"OP_RETURN {data.hex()}"
                else:
                    asm = "OP_RETURN"
            else:
                asm = "OP_RETURN"
        except Exception:
            asm = "OP_RETURN"

        result.update({
            'type': 'nulldata',
            'hex': script_hex,
            'asm': asm,
        })
        return result

    # ─── Handle P2PKH ───
    if len(script) >= 25 and script[0] == 0x76 and script[1] == 0xa9 and script[2] == 0x14 and script[23] == 0x88 and script[24] == 0xac:
        pubkey_hash = script[3:23].hex()
        address = pubkeyhash.to_address(pubkey_hash)
        asm = f"OP_DUP OP_HASH160 {pubkey_hash} OP_EQUALVERIFY OP_CHECKSIG"

        result.update({
            'type': 'pubkeyhash',
            'hex': script_hex,
            'asm': asm,
            'reqSigs': 1,
            'addresses': [address],
        })

        # 🛠 NEW! Check if extra OP_EVR_ASSET follows
        if len(script) > 25:
            asset_script = script[25:]
            if asset_script[0] == 0xc0:
                asset_info = parse_op_evr_asset(asset_script)
                result.update(asset_info)

        return result

    # ─── Handle P2SH ───
    if (
        script[0] == 0xa9 and
        script[1] == 0x14 and
        len(script) >= 23 and
        script[-1] == 0x87
    ):
        script_hash = script[2:22].hex()
        address = p2sh.to_address(script_hash)
        asm = f"OP_HASH160 {script_hash} OP_EQUAL"

        result.update({
            'type': 'scripthash',
            'hex': script_hex,
            'asm': asm,
            'reqSigs': 1,
            'addresses': [address],
        })

        return result

    # ─── Handle Pure OP_EVR_ASSET (no P2PKH prefix) ───
    if script[0] == 0xc0:
        asset_info = parse_op_evr_asset(script)
        result.update(asset_info)
        return result

    # ─── Unknown ───
    result.update({
        'type': 'unknown',
        'hex': script_hex,
        'asm': '',
    })
    return result


def parse_op_evr_asset(script: bytes) -> Dict[str, Any]:
    """
    Parse an OP_EVR_ASSET script payload into asset info fields.
    """
    result = {}

    try:
        i = 1
        push_opcode = script[i]
        i += 1
        payload = script[i:i+push_opcode]

        if not payload.startswith(b'evr'):
            raise ValueError("Missing 'evr' prefix")

        op_type = payload[3:4]
        op_map = {
            b'q': 'issue_asset',
            b'o': 'ownership_token',
            b'r': 'reissue_asset',
            b't': 'transfer_asset',
            b'p': 'new_asset',
        }
        decoded_type = op_map.get(op_type, f'unknown_asset_op ({op_type.hex()})')

        i = 4

        # Asset Name
        name_len = payload[i]
        i += 1
        asset_name = payload[i:i+name_len].decode('utf-8')
        i += name_len

        # Amount (int LE)
        amount = int.from_bytes(payload[i:i+8], 'little')
        i += 8

        # Optional IPFS hash
        ipfs_hash = None
        if len(payload) > i:
            if payload[i] == 0x12 and payload[i+1] == 0x20:
                ipfs_hash = payload[i+2:i+34].hex()
                try:
                    # Convert back to base58 CIDv0
                    import base58
                    ipfs_cidv0 = base58.b58encode(b'\x12\x20' + bytes.fromhex(ipfs_hash)).decode()
                    ipfs_hash = ipfs_cidv0
                except Exception:
                    pass

        result.update({
            'type': decoded_type,
            'asset': {
                'name': asset_name,
                'amount': amount / 1e8,
                'message': ipfs_hash,
            },
            'asset_name': asset_name,
            'amount': amount / 1e8,
            'message': ipfs_hash,
        })
    except Exception as e:
        result.update({
            'type': 'unknown',
            'error': str(e),
        })

    return result
