import binascii
from typing import Optional, Dict, Any
from .. import pubkeyhash
from .. import p2sh

def decode(script_hex: str) -> Dict[str, Any]:
    """
    Decode any Evrmore scriptPubKey hex (standard or asset-related).

    Supports:
    - Standard P2PKH outputs
    - OP_EVR_ASSET extensions:
        - Issue Asset ('q')
        - Ownership Token ('o')
        - Reissue Asset ('r')
        - Transfer Asset ('t')
        - New Asset ('p')
    - Null Asset Tags (qualifier/restricted tag scripts)
    - Verifier Tag Scripts
    - Global Freeze Scripts
    """
    result = {'p2sh': p2sh.from_script(script_hex)}
    script = bytes.fromhex(script_hex)
    i = 0

    # Step 1: Optional P2PKH wrapper
    if script[i:i+1] == b'\x76':  # OP_DUP
        i += 1
        if script[i] != 0xa9: raise ValueError("Expected OP_HASH160")
        i += 1
        push_len = script[i]
        i += 1
        result['pubkey_hash'] = script[i:i+push_len].hex()
        result['address'] = pubkeyhash.to_address(result["pubkey_hash"])
        i += push_len
        if script[i:i+2] != b'\x88\xac':
            raise ValueError("Expected OP_EQUALVERIFY OP_CHECKSIG")
        i += 2
        result['has_p2pkh'] = True

        # ⛔ No more data? Then it's a pure EVR payment, not an asset
        if i >= len(script):
            result['script_type'] = 'p2pkh'
            return result
    else:
        result['has_p2pkh'] = False

    # Step 2: Check OP_EVR_ASSET (0xc0)
    if i >= len(script) or script[i] != 0xc0:
        raise ValueError("Missing OP_EVR_ASSET (0xc0)")
    i += 1

    # Step 3: Handle reserved types (verifier/global/tag scripts)
    if script[i:i+2] == b'\x50\x50':
        # Global Freeze
        i += 2
        asset_len = script[i]
        i += 1
        name_len = script[i]
        i += 1
        name = script[i:i+name_len].decode()
        i += name_len
        flag = script[i]
        result.update({
            'script_type': 'global_restriction',
            'asset_name': name,
            'freeze_flag': bool(flag)
        })
        return result

    elif script[i] == 0x50:
        # Verifier Tag
        i += 1
        asset_len = script[i]
        i += 1
        name_len = script[i]
        i += 1
        name = script[i:i+name_len].decode()
        i += name_len
        result.update({
            'script_type': 'verifier_tag',
            'qualifier_requirements': name
        })
        return result

    elif script[i] == 0x14:  # PubkeyHash for Null Tag
        # Step 3: Parse standard asset operations (q/o/r/t)
        push_len = script[i]
        i += 1
        asset_data = script[i:i+push_len]
        i += push_len

        if asset_data[:3] != b'evr':
            raise ValueError("Missing 'evr' prefix")
        result['prefix'] = 'evr'
        asset_data = asset_data[3:]

        op_type = asset_data[0:1]
        type_map = {
            b'q': 'issue_asset',
            b'o': 'ownership_token',
            b'r': 'reissue_asset',
            b't': 'transfer_asset',
        }
        result['script_type'] = type_map.get(op_type, f'unknown ({op_type.hex()})')
        asset_data = asset_data[1:]

        # Read asset name
        name_len = asset_data[0]
        asset_data = asset_data[1:]
        name = asset_data[:name_len].decode()
        result['asset_name'] = name
        asset_data = asset_data[name_len:]

        # Parse amounts and flags
        if result['script_type'] in ('transfer_asset', 'issue_asset', 'reissue_asset'):
            result['amount'] = int.from_bytes(asset_data[:8], 'little') / 1e8
            asset_data = asset_data[8:]

        if result['script_type'] == 'issue_asset':
            result['divisions'] = asset_data[0]
            result['reissuable'] = bool(asset_data[1])
            has_assoc = asset_data[2]
            result['has_associated_data'] = bool(has_assoc)
            asset_data = asset_data[3:]
            if has_assoc and len(asset_data) >= 34:
                result['associated_data'] = asset_data[:34].hex()

        elif result['script_type'] == 'reissue_asset':
            result['new_divisions'] = asset_data[0]
            result['updated_reissuable'] = bool(asset_data[1])
            asset_data = asset_data[2:]
            if len(asset_data) >= 34:
                result['associated_data'] = asset_data[:34].hex()

        elif result['script_type'] == 'transfer_asset':
            if len(asset_data) >= 34 and asset_data[:2] == b'\x12\x20':
                result['ipfs_hash'] = asset_data[2:34].hex()

        return result
    # Step 4: Standard OP_EVR_ASSET data payload
    push_len = script[i]
    i += 1
    asset_data = script[i:i+push_len]
    i += push_len

    # Validate prefix
    if asset_data[:3] != b'evr':
        raise ValueError("Missing 'evr' prefix")
    result['prefix'] = 'evr'
    asset_data = asset_data[3:]

    op_type = asset_data[0:1]
    type_map = {
        b'q': 'issue_asset',
        b'o': 'ownership_token',
        b'r': 'reissue_asset',
        b't': 'transfer_asset',
        b'p': 'new_asset',
    }
    result['script_type'] = type_map.get(op_type, f'unknown ({op_type.hex()})')
    asset_data = asset_data[1:]

    # Read asset name
    name_len = asset_data[0]
    asset_data = asset_data[1:]
    name = asset_data[:name_len].decode()
    result['asset_name'] = name
    asset_data = asset_data[name_len:]

    if result['script_type'] in ('transfer_asset', 'issue_asset', 'reissue_asset', 'new_asset'):
        result['amount'] = int.from_bytes(asset_data[:8], 'little') / 1e8
        asset_data = asset_data[8:]

    if result['script_type'] == 'issue_asset':
        result['divisions'] = asset_data[0]
        result['reissuable'] = bool(asset_data[1])
        has_assoc = asset_data[2]
        result['has_associated_data'] = bool(has_assoc)
        asset_data = asset_data[3:]
        if has_assoc and len(asset_data) >= 34:
            result['associated_data'] = asset_data[2:34].hex()

    elif result['script_type'] == 'reissue_asset':
        result['new_divisions'] = asset_data[0]
        result['updated_reissuable'] = bool(asset_data[1])
        asset_data = asset_data[2:]
        if len(asset_data) >= 34:
            result['associated_data'] = asset_data[2:34].hex()

    elif result['script_type'] == 'new_asset':
        result['expire_time'] = asset_data[0]
        result['units'] = asset_data[1]
        result['reissuable'] = asset_data[2] == 1

    elif result['script_type'] == 'transfer_asset':
        if len(asset_data) >= 34 and asset_data[0:2] == b'\x12\x20':
            result['ipfs_hash'] = asset_data[2:34].hex()

    return result
