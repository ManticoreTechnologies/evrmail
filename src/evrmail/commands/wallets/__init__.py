
"""
evrmail wallets [COMMAND]

💼 Manage wallets and keys

Subcommand	Description
create	🛠️ Create a new wallet (with optional passphrase)
list	📂 List all saved wallets
show	📄 Show metadata for a specific wallet
export	💾 Export wallet to file
import	📥 Import wallet from file
init	🔄 Create or restore wallet from mnemonic
"""

import typer

wallets_app = typer.Typer(name="wallets", help="💼 Manage your Evrmore wallets")

from .create import create_app
from .list import list_app
from .show import show_app
from .export import export_app
from .lmport import import_app
from .init import init_app

wallets_app.add_typer(create_app)
wallets_app.add_typer(list_app)
wallets_app.add_typer(show_app)
wallets_app.add_typer(export_app)
wallets_app.add_typer(import_app)
wallets_app.add_typer(init_app)



from typing import Optional
import typer
import os
import json
from evrmail.wallet.utils import (
    generate_mnemonic,
    create_wallet,
    get_public_key_for_address,
    save_wallet,
    load_wallet,
    get_private_key_for_address,
    set_active_address,
    get_active_address,
    get_sighash,
    serialize_unsigned_tx,
    WALLET_DIR
)



from datetime import datetime
from evrmail.config import load_config
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from hdwallet.derivations import BIP44Derivation


evrmail_config = load_config()

""" You can now use a public node! Using simply rpc_client=EVrmoreClient() will use your local evrmore node! """
EVRMORE_RPC_HOST = "tcp://77.90.40.55"
EVRMORE_RPC_PORT = 8819
RPC_USER = "evruser"
RPC_PASSWORD = "changeThisToAStrongPassword123"
rpc_client = EvrmoreClient()#EvrmoreClient(url="tcp://77.90.40.55", rpcuser="evruser", rpcpassword="changeThisToAStrongPassword123", rpcport=8819)

from .init import init_app
from .list import list_app
from .show import show_app
from .create import create_app

#wallets_app.add_typer(init_app)
#wallets_app.add_typer(list_app)
#wallets_app.add_typer(show_app)
#wallets_app.add_typer(create_app)
#wallets_app.add_typer(balance_app)
#wallets_app.add_typer(createtransaction_app)

import hashlib

EVR_MAIN_PUBKEY_HASH = 0x21  # Evrmore mainnet P2PKH prefix
EVR_MAIN_SCRIPT_HASH = 0x5C  # Evrmore mainnet P2SH prefix

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58_encode(b: bytes) -> str:
    num = int.from_bytes(b, byteorder='big')
    enc = ""
    while num > 0:
        num, rem = divmod(num, 58)
        enc = _B58_ALPHABET[rem] + enc
    n_leading_zeros = len(b) - len(b.lstrip(b'\x00'))
    return "1" * n_leading_zeros + enc

def base58_decode(s: str) -> bytes:
    num = 0
    for char in s:
        num *= 58
        if char not in _B58_ALPHABET:
            raise ValueError(f"Invalid Base58 character: '{char}'")
        num += _B58_ALPHABET.index(char)
    byte_length = (num.bit_length() + 7) // 8
    result = num.to_bytes(byte_length, 'big') if byte_length > 0 else b'\x00'
    n_leading_ones = len(s) - len(s.lstrip('1'))
    return b'\x00' * n_leading_ones + result

def encode_address(version: int, payload: bytes) -> str:
    data = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return base58_encode(data + checksum)

def decode_address(address: str):
    data = base58_decode(address)
    if len(data) < 5:
        raise ValueError("Address too short")
    version = data[0]
    payload = data[1:-4]
    checksum = data[-4:]
    calc_checksum = hashlib.sha256(hashlib.sha256(data[:-4]).digest()).digest()[:4]
    if calc_checksum != checksum:
        raise ValueError("Invalid address checksum")
    return version, payload

def create_p2pkh_script(address: str = None, pubkey_hash: bytes = None) -> str:
    if address is None and pubkey_hash is None:
        raise ValueError("Must provide either an address or a pubkey_hash")
    if address:
        ver, payload = decode_address(address)
        if ver != EVR_MAIN_PUBKEY_HASH:
            raise ValueError("Address is not a P2PKH address")
        if len(payload) != 20:
            raise ValueError("Decoded address payload is not 20 bytes")
        pubkey_hash = payload
    else:
        if len(pubkey_hash) != 20:
            raise ValueError("pubkey_hash must be 20 bytes")
    script_bytes = bytearray()
    script_bytes.append(0x76)  # OP_DUP
    script_bytes.append(0xA9)  # OP_HASH160
    script_bytes.append(0x14)  # push 20 bytes
    script_bytes.extend(pubkey_hash)
    script_bytes.append(0x88)  # OP_EQUALVERIFY
    script_bytes.append(0xAC)  # OP_CHECKSIG
    return script_bytes.hex()

def create_p2sh_script(address: str = None, script_hash: bytes = None) -> str:
    if address is None and script_hash is None:
        raise ValueError("Must provide either an address or a script_hash")
    if address:
        ver, payload = decode_address(address)
        if ver != EVR_MAIN_SCRIPT_HASH:
            raise ValueError("Address is not a P2SH address")
        if len(payload) != 20:
            raise ValueError("Decoded address payload is not 20 bytes")
        script_hash = payload
    else:
        if len(script_hash) != 20:
            raise ValueError("script_hash must be 20 bytes")
    script_bytes = bytearray()
    script_bytes.append(0xA9)         # OP_HASH160
    script_bytes.append(0x14)         # push 20 bytes
    script_bytes.extend(script_hash)  # script hash
    script_bytes.append(0x87)         # OP_EQUAL
    return script_bytes.hex()

import base58
import hashlib

import base58

def address_to_pubkey_hash(address: str) -> bytes:
    """
    Decode a base58check Evrmore address and return the 20-byte pubkey hash (in hex).
    Supports:
      - P2PKH (version byte 0x21)
      - P2SH  (version byte 0x05)
    """
    decoded = base58.b58decode_check(address)
    version_byte = decoded[0]
    pubkey_hash = decoded[1:]
    
    print(f"Address: {address}")
    print(f"Version byte: {version_byte} (hex: {hex(version_byte)})")
    print(f"Pubkey hash (hex): {pubkey_hash.hex()}")

    if version_byte in (0x21, 0x05):
        return pubkey_hash
    else:
        raise ValueError(f"Unsupported address version: {version_byte}")


def encode_pushdata(data: bytes) -> bytes:
    if len(data) < 0x4c:
        return bytes([len(data)]) + data
    elif len(data) <= 0xff:
        return b'\x4c' + bytes([len(data)]) + data
    elif len(data) <= 0xffff:
        return b'\x4d' + struct.pack('<H', len(data)) + data
    else:
        return b'\x4e' + struct.pack('<I', len(data)) + data

def evr_transfer_asset_script(
    asset_name: str,
    amount: int,
    recipient_pubkey_hash: bytes,
    precision: int = 8
) -> str:
    """
    Construct a standard Evrmore transfer_asset scriptPubKey.

    :param asset_name: The name of the asset (e.g., "HANDLE!")
    :param amount: The asset amount to transfer (in satoshis, scaled by 1e8)
    :param recipient_pubkey_hash: 20-byte RIPEMD160 hash of the recipient's public key
    :param precision: The precision of the asset (default is 8)
    :return: Hex-encoded scriptPubKey
    """
    if len(recipient_pubkey_hash) != 20:
        raise ValueError("Invalid recipient_pubkey_hash length; expected 20 bytes.")

    asset_bytes = asset_name.encode("utf-8")
    asset_name_length = len(asset_bytes)

    if asset_name_length > 30:
        raise ValueError("Asset name is too long; maximum length is 30 bytes.")

    script = bytearray()

    # Standard P2PKH
    script += b'\x76\xa9'  # OP_DUP OP_HASH160
    script += bytes([len(recipient_pubkey_hash)]) + recipient_pubkey_hash
    script += b'\x88\xac'  # OP_EQUALVERIFY OP_CHECKSIG

    # Asset transfer section
    script += b'\xc0'      # OP_EVR_ASSET
    script += b'\x74'      # OP_TRANSFER

    # Asset data payload
    script += bytes([asset_name_length]) + asset_bytes
    script += bytes([precision])
    script += amount.to_bytes(8, byteorder="little")

    return script.hex()





#@wallets_app.command("assets")
def wallet_assets():
    """Show total asset balances across all wallet addresses."""
    all_addresses = []
    for fname in os.listdir(WALLET_DIR):
        if fname.endswith(".json"):
            data = load_wallet(fname.replace(".json", ""))
            addresses = data.get("addresses", [])
            all_addresses.extend([entry["address"] for entry in addresses])

    if not all_addresses:
        typer.echo("⚠️ No addresses found across all wallets.")
        return

    try:
        balance_info = rpc_client.getaddressbalance({"addresses": all_addresses}, include_assets=True)
        typer.echo(f"\n💰 Total asset balances across all wallets:")
        typer.echo(json.dumps(balance_info, indent=2))
    except Exception as e:
        typer.echo(f"❌ Failed to fetch balance: {e}")

#@wallets_app.command("address-balance")
def single_address_balance(address: str):
    """Get balance of a single address."""
    try:
        result = rpc_client.getaddressbalance(address)
        typer.echo(f"\n💳 Balance for {address}: {result} EVR")
    except Exception as e:
        typer.echo(f"❌ Failed to get balance: {e}")

#@wallets_app.command("send")
def send_evr(from_addr: str, to_addr: str, amount: float):
    """Send EVR from one address to another."""
    try:
        txid = rpc_client.sendtoaddress(from_addr, to_addr, amount)
        typer.echo(f"✅ Transaction sent! TXID: {txid}")
    except Exception as e:
        typer.echo(f"❌ Failed to send EVR: {e}")


#@wallets_app.command("list-addresses")
def list_addresses():
    """List all derived addresses from all wallets."""
    from evrmail.wallet.addresses import get_all_addresses
    typer.echo(get_all_addresses())

#@wallets_app.command("address")
def get_address_by_index(name: str, index: int = typer.Option(0, "--index", "-i", help="Index of the address")):
    """Retrieve a specific address by index from a named wallet."""
    try:
        data = load_wallet(name)
    except FileNotFoundError:
        typer.echo("❌ Wallet not found.")
        return

    addresses = data.get("addresses", [])
    if not addresses:
        typer.echo("⚠️ No addresses found in this wallet.")
        return

    if index < 0 or index >= len(addresses):
        typer.echo(f"❌ Invalid index. Valid range is 0 to {len(addresses) - 1}")
        return

    addr = addresses[index]
    typer.echo(f"\n📌 Wallet: {name} [Index {index}]")
    typer.echo(f"🏠 Address:  {addr['address']}")
    typer.echo(f"🔓 PubKey:   {addr['public_key']}")
    typer.echo(f"🔐 PrivKey:  {addr['private_key']}")
    typer.echo(f"📍 Path:     {addr['path']}")

#@wallets_app.command("addresses")
def wallet_addresses(name: str):
    """List all derived addresses in a wallet."""
    try:
        data = load_wallet(name)
    except FileNotFoundError:
        typer.echo("❌ Wallet not found")
        return

    if "addresses" not in data or not data["addresses"]:
        typer.echo("⚠️ No addresses found in this wallet.")
        return

    typer.echo(f"\n📬 Addresses for wallet: '{name}'\n")
    for entry in data["addresses"]:
        typer.echo(f"  ┌─ Index [{entry['index']}]")
        typer.echo(f"  │   📍 Path:     {entry['path']}")
        typer.echo(f"  │   🏠 Address:  {entry['address']}")
        typer.echo(f"  │   🔓 PubKey:   {entry['public_key']}")
        typer.echo(f"  │   🔐 PrivKey:  {entry['private_key']}")
        typer.echo("  └────────────────────────────────────────\n")

#@wallets_app.command("dumpprivkey")
def dumpprivkey(address: str):
    """ Dump the private key wif for an address """
    try:
        print(get_private_key_for_address(address))
    except Exception as e:
        typer.echo(f"❌ Failed to get private key: {e}")
    
#@wallets_app.command("use")
def set_active(address: str):
    """Set the active address for message signing or sending."""
    try:
        get_private_key_for_address(address)
        set_active_address(address)
        typer.echo(f"✅ Active address set to: {address}")
    except Exception as e:
        typer.echo(f"❌ Failed to set active address: {e}")

#@wallets_app.command("active")
def show_active():
    """Display the currently active address."""
    active_address = get_active_address()
    if active_address:
        typer.echo(f"📌 Active address: {active_address}")
    else:
        typer.echo("⚠️ No active address is currently set.")

#@wallets_app.command("validate")
def validate_address(address: str):
    """Validate an address."""
    try:
        from evrmail.wallet.addresses import validate
        typer.echo(validate(address))
    except Exception as e:
        typer.echo(f"❌ Invalid address: {e}")

__all__=["address_to_pubkey_hash"]