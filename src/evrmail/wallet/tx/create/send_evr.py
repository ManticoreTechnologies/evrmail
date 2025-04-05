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
    from_address: str,
    to_address: str,
    evr_amount: int,
    ipfs_hash: str = "",
    fee_rate_per_kb: int = 1_000_000,  # satoshis per KB
) -> Tuple[str, str]:
    rpc_client = EvrmoreClient()

    utxos = rpc_client.getaddressutxos({"addresses": ["EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH"]})
    private_key = get_private_key_for_address("EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH")

    wif_privkey = wif_from_privkey(bytes.fromhex(private_key))

    to_address = "EMuP1QsABQ7ccqis8QwKQoLBDVwnq5LrbX"

    return create_send_evr(utxos, wif_privkey, to_address, 10000)

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

def create_send_evr(
    utxos: list,
    wif_privkey: str,
    to_address: str,
    amount: int,
    fee: int = 10000000,
) -> str:
    """
    Construct and sign a raw EVR transaction using given UTXOs.

    Parameters:
    - utxos: List of dicts with keys: txid (hex), vout (int), scriptPubKey (hex), amount (in sats)
    - wif_privkey: WIF-encoded private key string
    - to_address: destination base58 address
    - amount: amount to send in satoshis
    - fee: flat fee in satoshis (default 1000)

    Returns:
    - hex-encoded signed raw transaction
    """
    secret = CEvrmoreSecret(wif_privkey)
    from Crypto.Hash import RIPEMD160
    from hashlib import sha256
    def hash160(b: bytes) -> bytes:
        return RIPEMD160.new(sha256(b).digest()).digest()

    def pubkey_hash_to_address(pubkey_hash: bytes, prefix: bytes = b'\x3c') -> str:
        payload = prefix + pubkey_hash  # 0x3c is EVR pubkey prefix (might vary by net)
        checksum = sha256(sha256(payload).digest()).digest()[:4]
        return base58.b58encode(payload + checksum).decode()

    # Generate change address
    change_pubkey = secret.pub
    change_pubkey_hash = hash160(change_pubkey)
    change_address = pubkey_hash_to_address(change_pubkey_hash)


    # Prepare outputs
    to_pubkey_hash = address_to_pubkey_hash(to_address)
    to_script_pubkey = CScript([
        OP_DUP, OP_HASH160, to_pubkey_hash, OP_EQUALVERIFY, OP_CHECKSIG
    ])
    txout = CMutableTxOut(amount, to_script_pubkey)

    # Prepare UTXO inputs
    txins = []
    total_input = 0
    for u in utxos:
        txid = lx(u["txid"])
        vout = u["outputIndex"]
        txins.append(CMutableTxIn(COutPoint(txid, vout)))
        total_input += u["satoshis"]

    if total_input < amount + fee:
        raise ValueError(f"Insufficient funds: have {total_input}, need {amount + fee}")

    txouts = [txout]

    # Add change output if needed
    change = total_input - amount - fee
    if change > 0:
        change_pubkey_hash = address_to_pubkey_hash(change_address)
        change_script = CScript([
            OP_DUP, OP_HASH160, change_pubkey_hash, OP_EQUALVERIFY, OP_CHECKSIG
        ])
        txouts.append(CMutableTxOut(change, change_script))

    # Create unsigned transaction
    tx = CMutableTransaction(txins, txouts)

    # Sign each input
    for i, u in enumerate(utxos):
        script_pubkey = CScript(bytes.fromhex(u["script"]))
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = secret.sign(sighash) + bytes([SIGHASH_ALL])
        txins[i].scriptSig = CScript([sig, secret.pub])

    return tx.serialize().hex()
