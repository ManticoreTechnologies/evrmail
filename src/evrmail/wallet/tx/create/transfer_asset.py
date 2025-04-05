import math
import hashlib
from typing import List, Tuple

from evrmail.wallet.utils import (
    get_public_key_for_address,
    get_private_key_for_address,
    get_sighash,          # We'll replace this with our version below.
    sign_input,           # We'll replace this with our version below.
    serialize_unsigned_tx,  # We'll replace this with our version below.
    serialize_signed_tx,    # We'll replace this with our version below.
    address_to_pubkey_hash,
)
from evrmail.wallet.script.create import create_transfer_asset_script
import evrmail.wallet.script
from evrmail.wallet import pubkey
from evrmore_rpc import EvrmoreClient

# -----------------------------------------------------------------------------
# Helper: Extract only the base P2PKH script from a full UTXO script.
def get_base_p2pkh(script_hex: str) -> str:
    script = bytes.fromhex(script_hex)
    try:
        # Find the first occurrence of OP_CHECKSIG (0x88 0xac)
        end_index = script.index(b'\x88\xac') + 2
    except ValueError:
        raise ValueError("Script does not contain expected P2PKH ending")
    return script[:end_index].hex()

# -----------------------------------------------------------------------------
# Serialization helpers for transaction (using raw varint encoding for lengths)

def serialize_unsigned_tx(vin, vout, locktime=0) -> bytes:
    version = (2).to_bytes(4, 'little')
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''
    for txin in vin:
        inputs += bytes.fromhex(txin["txid"])[::-1]            # reverse txid
        inputs += txin["vout"].to_bytes(4, 'little')             # output index
        # For unsigned tx, script is empty → varint 0x00
        inputs += (0).to_bytes(1, 'little')
        inputs += txin["sequence"].to_bytes(4, 'little')
    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        satoshis = int(txout["value"] * 1e8)
        outputs += satoshis.to_bytes(8, 'little')
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += len(script_bytes).to_bytes(1, 'little') + script_bytes
    locktime_bytes = locktime.to_bytes(4, 'little')
    return version + input_count + inputs + output_count + outputs + locktime_bytes

def serialize_signed_tx(vin, vout, locktime=0) -> bytes:
    version = (2).to_bytes(4, 'little')
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''
    for txin in vin:
        inputs += bytes.fromhex(txin["txid"])[::-1]
        inputs += txin["vout"].to_bytes(4, 'little')
        script_sig_bytes = bytes.fromhex(txin["scriptSig"]["hex"])
        # For the final transaction, use raw varint encoding for scriptSig length.
        inputs += len(script_sig_bytes).to_bytes(1, 'little') + script_sig_bytes
        inputs += txin["sequence"].to_bytes(4, 'little')
    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        value = int(txout["value"] * 1e8)
        outputs += value.to_bytes(8, 'little')
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += len(script_bytes).to_bytes(1, 'little') + script_bytes
    locktime_bytes = locktime.to_bytes(4, 'little')
    return version + input_count + inputs + output_count + outputs + locktime_bytes

# -----------------------------------------------------------------------------
# Sighash calculation for input signing (using SIGHASH_ALL)

def get_sighash_custom(vin, vout, input_index, script_pubkey_hex, locktime=0) -> bytes:
    version = (2).to_bytes(4, 'little')
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''
    for i, txin in enumerate(vin):
        inputs += bytes.fromhex(txin["txid"])[::-1]
        inputs += txin["vout"].to_bytes(4, 'little')
        if i == input_index:
            # For the input being signed, include the base script (raw varint length)
            script = bytes.fromhex(script_pubkey_hex)
            inputs += len(script).to_bytes(1, 'little') + script
        else:
            # For other inputs, empty script (varint 0)
            inputs += (0).to_bytes(1, 'little')
        inputs += txin["sequence"].to_bytes(4, 'little')
    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        value = int(txout["value"] * 1e8)
        outputs += value.to_bytes(8, 'little')
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += len(script_bytes).to_bytes(1, 'little') + script_bytes
    locktime_bytes = locktime.to_bytes(4, 'little')
    sighash_type = (1).to_bytes(4, 'little')  # SIGHASH_ALL (0x01000000 in little endian)
    preimage = version + input_count + inputs + output_count + outputs + locktime_bytes + sighash_type
    return hashlib.sha256(hashlib.sha256(preimage).digest()).digest()

# -----------------------------------------------------------------------------
# Signature helper: deterministic DER signature with low-S canonicalization.
from ecdsa import SigningKey, SECP256k1
from ecdsa.util import sigencode_der

def sigencode_der_canonize(r, s, order) -> bytes:
    # Enforce low-S values per BIP-62.
    if s > order // 2:
        s = order - s
    return sigencode_der(r, s, order)

def sign_input_custom(private_key_hex: str, sighash: bytes) -> str:
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = sk.sign_digest_deterministic(
        sighash,
        sigencode=sigencode_der_canonize
    )
    # Append SIGHASH_ALL (0x01)
    return (signature + b'\x01').hex()

# -----------------------------------------------------------------------------
# Main transaction builder for asset transfer
def create_transfer_asset_transaction(
    from_address: str,
    to_address: str,
    asset_name: str,
    asset_amount: int,
    ipfs_hash: str = "",
    fee_rate_per_kb: int = 1_000_000,  # satoshis per KB
) -> Tuple[str, str]:
    rpc_client = EvrmoreClient()

    # Step 1: Get asset UTXO (the UTXO that holds the asset)
    asset_utxos = rpc_client.getaddressutxos({"addresses": [from_address], "assetName": asset_name})
    asset_utxo = asset_utxos[0]

    # Step 2: Get EVR UTXOs (for fee funding)
    evr_utxos = rpc_client.getaddressutxos({"addresses": get_all_wallet_addresses()})
    evr_utxos.sort(key=lambda x: x['satoshis'])
    all_utxos = evr_utxos + asset_utxos

    # Step 3: Create the asset-transfer output script (includes asset data such as IPFS hash)
    to_pubkeyhash = address_to_pubkey_hash(to_address).hex()
    print(to_pubkeyhash, asset_name, asset_amount, ipfs_hash)
    asset_script = create_transfer_asset_script(to_pubkeyhash, asset_name, asset_amount, ipfs_hash)

    # Step 4: Build the list of inputs (vin)
    # Ensure the asset UTXO is the first input.
    vin = [{
        "txid": asset_utxo["txid"],
        "vout": asset_utxo["outputIndex"],
        "scriptSig": {"asm": "", "hex": ""},
        "sequence": 0xffffffff,
    }]

    selected = []
    accumulated = 0
    for utxo in evr_utxos:
        selected.append(utxo)
        accumulated += utxo['satoshis']
        vin.append({
            "txid": utxo["txid"],
            "vout": utxo["outputIndex"],
            "scriptSig": {"asm": "", "hex": ""},
            "sequence": 0xffffffff,
        })
        if len(vin) >= 5:  # Limit the number of inputs for now.
            break

    # Step 5: Build outputs (vout)
    # First output is the asset transfer output.
    vout = [{
        "value": 0,  # Asset outputs use value 0.
        "n": 0,
        "scriptPubKey": {"asm": "", "hex": asset_script},
    }]

    # Step 6: Estimate fees (using dummy serialization)
    dummy_tx = serialize_unsigned_tx(vin, vout)
    est_size = len(dummy_tx.hex()) // 2 + len(vin) * 107
    min_fee = max(math.ceil(est_size * fee_rate_per_kb / 1000), est_size * 10)
    if accumulated < min_fee:
        raise Exception(f"Insufficient EVR: need ≥ {min_fee} sat")

    # Step 7: Add a change output for any leftover EVR (if needed)
    change = accumulated - min_fee
    print("CHANGE!=", change)
    if change > 0:
        from_pubkey = get_public_key_for_address(from_address)
        change_script = evr_utxos[0]['script']
        vout.append({
            "value": change / 1e8,
            "n": 1,
            "scriptPubKey": {"asm": "", "hex": change_script},
        })

    # Step 8: Sign each input.
    # For each input, compute the sighash using the base P2PKH script from the UTXO.
    for i, txin in enumerate(vin):
        txid = txin["txid"]
        vout_index = txin["vout"]
        matching_utxo = next(
            u for u in all_utxos if u["txid"] == txid and u["outputIndex"] == vout_index
        )
        address = matching_utxo["address"]
        privkey = get_private_key_for_address(address)
        pubkey_hex = get_public_key_for_address(address)
        # Decode the UTXO script and extract base P2PKH.
        utxo_script = matching_utxo["script"]
        decoded = evrmail.wallet.script.decode(utxo_script)
        if not decoded.get("has_p2pkh"):
            raise ValueError("🚫 Unsupported input: not a P2PKH-style UTXO")
        full_script_pubkey = matching_utxo["script"]
        print(full_script_pubkey)
        sighash = get_sighash(vin, vout, i, full_script_pubkey)
        # Generate signature (DER-encoded, with SIGHASH_ALL appended).
        sig = sign_input_custom(privkey, sighash)
        sig_bytes = bytes.fromhex(sig)
        pubkey_bytes = bytes.fromhex(pubkey_hex)
        # Build scriptSig: <varint len(sig)> <sig> <varint len(pubkey)> <pubkey>
        script_sig = (
            len(sig_bytes).to_bytes(1, "little") + sig_bytes +
            len(pubkey_bytes).to_bytes(1, "little") + pubkey_bytes
        )
        txin["scriptSig"]["hex"] = script_sig.hex()

    # Final serialize the signed transaction.
    final_tx = serialize_signed_tx(vin, vout)
    actual_size = len(final_tx.hex()) // 2
    total_input = sum(u['satoshis'] for u in selected)
    total_output = sum(int(v['value'] * 1e8) for v in vout)
    actual_fee = total_input - total_output
    actual_rate = actual_fee / actual_size

    print("--- Fee summary ---")
    print("utxos:", selected)
    print("total sats:", total_input)
    print("total evr:", (total_input / 100000000))
    print("tx size:", actual_size)
    print("min relay fee:", 0.01, "evr")
    print("min fee required:", (actual_size / 1000) * 0.01, "evr")
    print("fee change:", (total_input / 100000000) - (actual_size / 1000) * 0.01)
    print("-------------------")
    change = (total_input) - (actual_size / 1000) * (0.01 * 100000000)
    if change > 0 and len(vout) > 1:
        vout[1]["value"] = change / 1e8

    final_tx = serialize_signed_tx(vin, vout)
    if actual_rate < 10:
        raise Exception(
            f"🚫 Final fee too low: {actual_rate:.2f} sat/byte (min 10 sat/B). "
            f"Size={actual_size}, Fee={actual_fee} sats"
        )
    return final_tx.hex(), asset_name

# -----------------------------------------------------------------------------
# Note: Ensure that get_sighash_custom and sign_input_custom (defined above)
# are used in place of any other versions.
