from typing import Optional
import typer

dev_app = typer.Typer(name="dev", help="🔧 Developer tools")

__all__ = ["dev_app"]


@dev_app.command(name="create-message-payload")
def create_message_payload(from_address: str, to: str, subject: str, content: str):
    """Create a message payload."""
    from evrmail.utils.create_message_payload import create_message_payload
    print(create_message_payload(to, subject, content))

@dev_app.command(name="get-pubkey-hash")
def get_pubkey_hash(address: str):
    """Get the pubkey hash from an address."""
    from evrmail.wallet.utils import address_to_pubkey_hash
    print(address_to_pubkey_hash(address))

@dev_app.command(name="list-all-unspent")
def list_all_unspent(
    raw: bool = typer.Option(False, "--raw", help="Print raw JSON instead of a table")
):
    """List all unspent transactions."""
    from evrmail import rpc_client, wallet
    import json
    addresses = wallet.addresses.get_all_addresses()
    utxos = rpc_client.getaddressutxos({"addresses": addresses})
    if raw:
        print(json.dumps(utxos, indent=2))
    else:
        for u in utxos:
            print(f"{u['address']}, {u['txid']}, {u['satoshis']/100000000}, {u['height']}, {u['outputIndex']}")

@dev_app.command(name="get-public-key-for-address")
def get_public_key_for_address(address: str):
    """Get the public key for an address."""
    from evrmail.wallet.utils import get_public_key_for_address
    print(get_public_key_for_address(address))

@dev_app.command(name="get-private-key-for-address")
def get_private_key_for_address(address: str):
    """Get the private key for an address."""
    from evrmail.wallet.utils import get_private_key_for_address
    print(get_private_key_for_address(address))
import os
import hashlib
import base58
import typer
from evrmore_rpc import EvrmoreClient
from evrmail.wallet.utils import address_to_pubkey_hash, wif_from_privkey, get_private_key_for_address
from evrmore.wallet import CEvrmoreSecret
from evrmore.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint, lx
from evrmore.core.script import CScript, OP_HASH160, OP_EQUAL
from evrmore.core.scripteval import SignatureHash, SIGHASH_ALL
from Crypto.Hash import RIPEMD160
from hashlib import sha256

# Assuming this exists and returns a hex string of the swap locking script
from evrmail.wallet.script.create import create_swap_script

def create_p2sh_address(script: bytes) -> str:
    redeem_script_hash = RIPEMD160.new(sha256(script).digest()).digest()
    versioned_payload = b'\x32' + redeem_script_hash  # P2SH prefix for Evrmore mainnet
    checksum = sha256(sha256(versioned_payload).digest()).digest()[:4]
    return base58.b58encode(versioned_payload + checksum).decode()

@dev_app.command(name="decode-script")
def decode_raw_script(
    raw_script: str = typer.Argument(..., help="The script to decode")
):
    from evrmail.wallet.script.decode import decode as decode_script
    print(decode_script(raw_script))

@dev_app.command(name="decode-block")
def decode_block(
    raw_block_hash: str = typer.Argument(..., help="The raw hash of the block to decode")
):
    from evrmail.wallet import block
    print(block.decode(raw_block_hash))
    return block.decode(raw_block_hash)

@dev_app.command(name="create-swap-tx")
def create_swap_tx(
    to: str = typer.Option(..., help="Recipient's address"),
    from_address: str = typer.Option(..., help="Sender's address"),
    want: int = typer.Option(..., help="Amount of the asset to swap"),
    asset: str = typer.Option(..., help="Name of the asset to swap"),
    ipfs: Optional[str] = typer.Option(None, help="IPFS CIDv0 hash for metadata"),
    locktime: Optional[int] = typer.Option(None, help="Locktime for the swap"),
    ownership: bool = typer.Option(False, help="Is the asset an ownership token?")
):
    from evrmail import rpc_client
    import time
    # Generate secret and hash
    secret = os.urandom(32)
    sha = hashlib.sha256(secret).digest()
    hash160 = RIPEMD160.new(sha).digest()
    hash160_hex = hash160.hex()

    typer.echo("🔐 Generated Swap Secret")
    typer.echo(f"   • Secret (hex)  : {secret.hex()}")
    typer.echo(f"   • Secret (b58)  : {base58.b58encode(secret).decode()}")
    typer.echo(f"   • HASH160       : {hash160_hex}")

    recipient_pubkey_hash = address_to_pubkey_hash(to).hex()
    refund_pubkey_hash = address_to_pubkey_hash(from_address).hex()

    # Determine locktime
    if locktime is None:
        locktime = int(time.time()) + 3600  # Default to 1 hour from now

    # Create the swap script
    swap_script_hex = create_swap_script(
        hash_of_secret_hex=hash160_hex,
        recipient_pubkey_hash_hex=recipient_pubkey_hash,
        refund_pubkey_hash_hex=refund_pubkey_hash,
        locktime=locktime,
        asset_name=asset,
        asset_amount=want,
        is_ownership_token=ownership,
        ipfs_cidv0=ipfs
    )
    swap_script = bytes.fromhex(swap_script_hex)
    swap_p2sh_address = create_p2sh_address(swap_script)

    typer.echo(f"\n🎯 Swap P2SH Address: {swap_p2sh_address}")

    # Gather UTXOs
    utxos = rpc_client.getaddressutxos({"addresses": [from_address]})
    inputs = []
    total = 0
    for u in utxos:
        inputs.append(u)
        total += u["satoshis"]
        if total >= want + 1000:
            break
    if total < want + 1000:
        typer.echo("❌ Not enough EVR to fund the swap.")
        raise typer.Exit()

    # Build transaction
    txins = [CMutableTxIn(COutPoint(lx(u["txid"]), u["outputIndex"])) for u in inputs]
    swap_script_hash = RIPEMD160.new(sha256(swap_script).digest()).digest()
    txouts = [CMutableTxOut(want, CScript([OP_HASH160, swap_script_hash, OP_EQUAL]))]

    fee = 10000000
    change = total - want - fee
    if change > 0:
        change_script = CScript([OP_HASH160, address_to_pubkey_hash(from_address), OP_EQUAL])
        txouts.append(CMutableTxOut(change, change_script))

    tx = CMutableTransaction(txins, txouts)

    # Sign transaction
    privkey = get_private_key_for_address(from_address)
    secret_obj = CEvrmoreSecret(wif_from_privkey(bytes.fromhex(privkey)))
    for i, u in enumerate(inputs):
        script_pubkey = CScript(bytes.fromhex(u["script"]))
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = secret_obj.sign(sighash) + bytes([SIGHASH_ALL])
        tx.vin[i].scriptSig = CScript([sig, secret_obj.pub])

    typer.echo(f"\n📦 Raw TX Hex:\n{tx.serialize().hex()}")
    typer.echo("\n✅ Fund the P2SH address and wait for confirmations.")
    typer.echo("   Provide the secret hash and P2SH address to your counterparty.")
