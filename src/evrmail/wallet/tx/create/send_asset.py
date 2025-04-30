import math
import hashlib
from re import S
from typing import List, Tuple
import base58
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
from ecdsa import SigningKey, SECP256k1
from ecdsa.util import sigencode_der
from evrmore.core import (
    CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint, lx
)
from evrmore.core.script import (
    CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG
)
from evrmore.wallet import CEvrmoreSecret
from evrmore.core.scripteval import SignatureHash, SIGHASH_ALL
import base58
import base58
from hashlib import sha256
def filter_utxos_by_asset(utxo_data: dict, asset_name: str) -> dict:
    filtered = []
    print('--------------Filtering UTXOS---------------')
    for address, utxos in utxo_data.items():
        matching_utxos = [u for u in utxos if u.get("asset") == asset_name and u.get("spent") == False]
        if matching_utxos:
            filtered.extend(matching_utxos)
    print(matching_utxos)
    print('--------------------------------------------')

    return filtered
    
def flatten_utxos(utxo_data: dict) -> list:
    flat_list = []
    for utxos in utxo_data.values():
        flat_list.extend(utxos)
    return flat_list

def combine_utxos(all_utxos):
    utxos = {}
    mempool = all_utxos['mempool']
    confirmed = all_utxos['confirmed']
    for address in mempool:
        utxos[address] = mempool[address]
    for address in confirmed:
        if address in list(utxos.keys()):
            utxos[address].append(confirmed[address])
        else:
            utxos[address] = confirmed[address]
    return utxos
# Main transaction builder for asset transfer
def create_send_asset_transaction(
    from_addresses: list,
    to_address: str,
    asset_name: str,
    asset_amount: int,
    fee_rate: int = 1_000_000,  # sat/kB
    ipfs_cidv0: str = None,
) -> Tuple[str, str]:
    from evrmail import rpc_client
    from evrmail.daemon.__main__ import load_utxos
    utxos = combine_utxos(load_utxos())
    print(utxos)
    asset_utxos =  filter_utxos_by_asset(utxos, asset_name)
    evr_utxos = filter_utxos_by_asset(utxos, None)
    if len(asset_utxos) == 0:
        raise Exception(f"No matching asset utxos found for {asset_name} across {len(from_addresses)} addresses.")
    private_keys = {
        utxo["address"]: get_private_key_for_address(utxo["address"]) for utxo in flatten_utxos(utxos)
    }
    wif_privkeys = {
        addr: wif_from_privkey(bytes.fromhex(key))
        for addr, key in private_keys.items()
    }

    return create_send_asset(evr_utxos, asset_utxos, wif_privkeys, to_address, asset_name, asset_amount, fee_rate, ipfs_cidv0)

def address_to_pubkey_hash(address: str) -> bytes:
    """Convert base58 address to pubkey hash (RIPEMD-160 of SHA-256 pubkey)."""
    decoded = base58.b58decode_check(address)
    return decoded[1:]  # Skip version byte

def wif_from_privkey(privkey_bytes: bytes, compressed: bool = True, mainnet: bool = True) -> str:
    """
    Convert raw private key bytes into WIF format for Evrmore.
    
    Parameters:
    - privkey_bytes: 32-byte private key
    - compressed: whether to encode as compressed key (default True)
    - mainnet: True for mainnet (EVR), False for testnet (tEVR)

    Returns:
    - WIF-encoded private key string
    """
    if len(privkey_bytes) != 32:
        raise ValueError("Private key must be 32 bytes")

    prefix = b'\x80' if mainnet else b'\xef'
    payload = prefix + privkey_bytes
    if compressed:
        payload += b'\x01'

    checksum = sha256(sha256(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()
def sign_transaction(tx: CMutableTransaction, utxos: list, wif_privkeys: dict):
    import json
    for i, u in enumerate(utxos):
        owner = u["address"]

        print(u)
        print(type(u))
        secret = CEvrmoreSecret(wif_privkeys[owner])
        print(type(u.get("script")) is str)
        if type(u.get("script")) is str:
            script_hex = u.get("script")
        else:
            script_hex = u.get("script").get("hex")
            


        script_pubkey = CScript(bytes.fromhex(script_hex))
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = secret.sign(sighash) + bytes([SIGHASH_ALL])
        tx.vin[i].scriptSig = CScript([sig, secret.pub])
    return tx
def create_send_asset(
    utxos: list,
    asset_utxos: list,
    wif_privkeys: dict,
    to_address: str,
    asset_name: str,
    asset_amount: int,
    fee_rate: int = 1_000_000,
    ipfs_cidv0: str = None
) -> Tuple[str, str]:
    from Crypto.Hash import RIPEMD160
    from hashlib import sha256

    def hash160(b: bytes) -> bytes:
        return RIPEMD160.new(sha256(b).digest()).digest()

    def pubkey_hash_to_address(pubkey_hash: bytes, prefix: bytes = b'\x3c') -> str:
        payload = prefix + pubkey_hash
        checksum = sha256(sha256(payload).digest()).digest()[:4]
        return base58.b58encode(payload + checksum).decode()

    # ─── Change address setup ─────────────────────────────────────────────────────
    print(wif_privkeys)
    first_addr = next(iter(wif_privkeys))
    change_secret = CEvrmoreSecret(wif_privkeys[first_addr])
    change_pubkey = change_secret.pub
    change_pubkey_hash = hash160(change_pubkey)
    change_address = pubkey_hash_to_address(change_pubkey_hash)

    # ─── Step 1: Add ONLY asset inputs (required for asset transfer) ──────────────
    asset_inputs = []
    for u in asset_utxos:
        asset_inputs.append(CMutableTxIn(COutPoint(lx(u["txid"]), u["vout"])))

    asset_script = create_transfer_asset_script(
        address_to_pubkey_hash(to_address),
        asset_name,
        asset_amount,
        ipfs_cidv0
    )
    asset_script_bytes = bytes.fromhex(asset_script)
    txouts = [CMutableTxOut(0, asset_script_bytes)]  # value = 0 for asset vout

    # ─── Step 2: Estimate size and fee using dummy EVR inputs ─────────────────────
    dummy_fee_inputs = []
    dummy_utxos = []
    fee_input_total = 0

    for u in utxos:
        print(u)
        if u in asset_utxos:
            continue
        dummy_fee_inputs.append(CMutableTxIn(COutPoint(lx(u["txid"]), u["vout"])))
        dummy_utxos.append(u)
        fee_input_total += u["amount"]
        if fee_input_total >= 1_000_000:  # rough high buffer
            break

    dummy_tx = CMutableTransaction(asset_inputs + dummy_fee_inputs, txouts)
    dummy_tx = sign_transaction(dummy_tx, asset_utxos + dummy_utxos, wif_privkeys)
    estimated_size = len(dummy_tx.serialize())
    fee_per_byte = max(1010, fee_rate / 1000)
    estimated_fee = int(estimated_size * fee_per_byte)

    # ─── Step 3: Select actual EVR inputs for fee ─────────────────────────────────
    fee_inputs = []
    fee_utxos = []
    fee_input_total = 0

    for u in utxos:
        if u in asset_utxos:
            continue
        fee_inputs.append(CMutableTxIn(COutPoint(lx(u["txid"]), u["vout"])))
        fee_utxos.append(u)
        fee_input_total += u["amount"]
        if fee_input_total >= estimated_fee:
            break

    if fee_input_total < estimated_fee:
        raise ValueError("Insufficient EVR for transaction fee")

    # ─── Step 4: Add change output (if needed) ────────────────────────────────────
    change = fee_input_total - estimated_fee
    if change > 0:
        change_script = CScript([
            OP_DUP, OP_HASH160, address_to_pubkey_hash(change_address),
            OP_EQUALVERIFY, OP_CHECKSIG
        ])
        txouts.append(CMutableTxOut(change, change_script))

    # ─── Step 5: Build final transaction ──────────────────────────────────────────
    all_inputs = asset_inputs + fee_inputs
    all_utxos = asset_utxos + fee_utxos

    final_tx = CMutableTransaction(all_inputs, txouts)
    final_tx = sign_transaction(final_tx, all_utxos, wif_privkeys)
    
    size = len(final_tx.serialize())
    final_fee = size * fee_per_byte

    # update txouts with final fee
    final_change = fee_input_total - estimated_fee - final_fee
    txouts[1].nValue = final_change
    final_tx = sign_transaction(final_tx, all_utxos, wif_privkeys)



    return final_tx.serialize().hex(), final_tx.GetTxid()[::-1].hex()
