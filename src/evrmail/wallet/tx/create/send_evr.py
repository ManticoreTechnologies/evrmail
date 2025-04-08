import math
import hashlib
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
# Main transaction builder for asset transfer
def create_send_evr_transaction(
    from_addresses: list,
    to_address: str,
    evr_amount: int,
    fee_rate: int = 1_000_000,  # satoshis per kB (0.01 EVR)
) -> Tuple[str, str]:
    rpc_client = EvrmoreClient()

    utxos = rpc_client.getaddressutxos({"addresses": from_addresses})
    private_keys = {utxo["address"]: get_private_key_for_address(utxo["address"]) for utxo in utxos}
    wif_privkeys = {address: wif_from_privkey(bytes.fromhex(private_key)) for address, private_key in private_keys.items()}

    return create_send_evr(utxos, wif_privkeys, to_address, evr_amount, fee_rate)

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
    for i, u in enumerate(utxos):
        owner = u["address"]
        secret = CEvrmoreSecret(wif_privkeys[owner])
        script_pubkey = CScript(bytes.fromhex(u["script"]))
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = secret.sign(sighash) + bytes([SIGHASH_ALL])
        tx.vin[i].scriptSig = CScript([sig, secret.pub])
    return tx
def create_send_evr(
    utxos: list,
    wif_privkeys: dict,
    to_address: str,
    amount: int,
    fee_rate: int = 1_000_000,  # satoshis per kB (0.01 EVR)
) -> Tuple[str, str]:
    """
    Construct and sign a raw EVR transaction using UTXOs from multiple addresses.
    Dynamically calculates fee based on tx size.

    Parameters:
    - utxos: List of dicts (must include "owner" key for source address)
    - wif_privkeys: dict {address: WIF private key}
    - to_address: Recipient base58 address
    - amount: Amount to send in satoshis
    - fee_rate: Fee per 1000 bytes in satoshis (default 1_000_000 = 0.01 EVR)

    Returns:
    - (raw_tx_hex, txid)
    """
    from Crypto.Hash import RIPEMD160
    from hashlib import sha256

    def hash160(b: bytes) -> bytes:
        return RIPEMD160.new(sha256(b).digest()).digest()

    def pubkey_hash_to_address(pubkey_hash: bytes, prefix: bytes = b'\x3c') -> str:
        payload = prefix + pubkey_hash
        checksum = sha256(sha256(payload).digest()).digest()[:4]
        return base58.b58encode(payload + checksum).decode()

    first_addr = next(iter(wif_privkeys.keys()))
    change_secret = CEvrmoreSecret(wif_privkeys[first_addr])
    change_pubkey = change_secret.pub
    change_pubkey_hash = hash160(change_pubkey)
    change_address = pubkey_hash_to_address(change_pubkey_hash)

    to_pubkey_hash = address_to_pubkey_hash(to_address)
    to_script_pubkey = CScript([
        OP_DUP, OP_HASH160, to_pubkey_hash, OP_EQUALVERIFY, OP_CHECKSIG
    ])
    txouts = [CMutableTxOut(amount, to_script_pubkey)]

    txins = []
    total_input = 0
    for u in utxos:
        txid = lx(u["txid"])
        vout = u["outputIndex"]
        txins.append(CMutableTxIn(COutPoint(txid, vout)))
        total_input += u["satoshis"]

    # ⚠️ Create dummy tx to estimate size (use 0-fee first)
    dummy_tx = CMutableTransaction(txins, txouts)
    for i, u in enumerate(utxos):
        owner = u["address"]
        secret = CEvrmoreSecret(wif_privkeys[owner])
        script_pubkey = CScript(bytes.fromhex(u["script"]))
        sighash = SignatureHash(script_pubkey, dummy_tx, i, SIGHASH_ALL)
        sig = secret.sign(sighash) + bytes([SIGHASH_ALL])
        dummy_tx.vin[i].scriptSig = CScript([sig, secret.pub])

    estimated_size = len(dummy_tx.serialize())
    fee_per_byte = max(1010, fee_rate / 1000)
    estimated_fee = estimated_size * fee_per_byte

    if total_input < amount + estimated_fee:
        raise ValueError(f"Insufficient funds: have {total_input}, need {amount + estimated_fee}")

    change = total_input - amount - estimated_fee
    if change > 0:
        change_script = CScript([
            OP_DUP, OP_HASH160, address_to_pubkey_hash(change_address), OP_EQUALVERIFY, OP_CHECKSIG
        ])
        txouts.append(CMutableTxOut(change, change_script))

    # Final tx
    tx = CMutableTransaction(txins, txouts)
    for i, u in enumerate(utxos):
        owner = u["address"]
        secret = CEvrmoreSecret(wif_privkeys[owner])
        script_pubkey = CScript(bytes.fromhex(u["script"]))
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = secret.sign(sighash) + bytes([SIGHASH_ALL])
        tx.vin[i].scriptSig = CScript([sig, secret.pub])

    size = len(tx.serialize())
    final_fee = size * fee_per_byte

    # update txouts with final fee
    final_change = total_input - amount - final_fee
    txouts[1].nValue = final_change
    tx = sign_transaction(tx, utxos, wif_privkeys)

    return tx.serialize().hex(), (tx.GetTxid())[::-1].hex()
