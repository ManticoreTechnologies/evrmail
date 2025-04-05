"""

wallet.pubkey.to_hash(pubkey) # Hash a pubkey
wallet.pubkeyhash.to_address(pubkeyhash) # Get an address from a pubkeyhash
wallet.script.decode_script(scripthex) # Decode a transaction script


"""

import os
from .pubkeyhash import * 
from .p2sh import *
import json
import os
from datetime import datetime
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.mnemonics.bip39 import BIP39Mnemonic
from hdwallet.derivations import BIP44Derivation
from mnemonic import Mnemonic
import typer
mnemo = Mnemonic("english")

WALLET_DIR = os.path.expanduser("~/.evrmail/wallets")
CONFIG_FILE = os.path.expanduser("~/.evrmail/config.json")
os.makedirs(WALLET_DIR, exist_ok=True)

def wallet_file_path(name: str) -> str:
    return os.path.join(WALLET_DIR, f"{name}.json")

def load_wallet(name: str):
    path = wallet_file_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def create_wallet(mnemonic: str, passphrase: str = "") -> HDWallet:
    hdwallet = HDWallet(cryptocurrency=Evrmore, passphrase=passphrase)
    hdwallet.from_mnemonic(BIP39Mnemonic(mnemonic=mnemonic))
    return hdwallet

def list_wallets():
    return [f.replace(".json", "") for f in os.listdir(WALLET_DIR) if f.endswith(".json")]
def save_wallet(name: str, hdwallet: HDWallet, address_count: int=1000):
    addresses = []
    for i in range(address_count):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)
        addr = hdwallet.address()
        addresses.append({
            "index": i,
            "path": f"m/44'/175'/0'/0/{i}",
            "address": addr,
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key()
        })
        hdwallet.clean_derivation()
    mnemonic = hdwallet.mnemonic()
    passphrase = hdwallet.passphrase()
    wallet_data = {
        "name": name,
        "created_at": datetime.utcnow().isoformat(),
        "mnemonic": mnemonic,
        "passphrase": passphrase,
        "coin_type": 175,
        "root_xprv": hdwallet.root_xprivate_key(),
        "root_xpub": hdwallet.root_xpublic_key(),
        "first_address": addresses[0]['address'],
        "addresses": addresses
    }

    with open(wallet_file_path(name), "w") as f:
        json.dump(wallet_data, f, indent=2)




def import_wallet(path: str):
    """Import a wallet from a backup file."""
    try:
        with open(os.path.expanduser(path), "r") as f:
            data = json.load(f)
    except Exception as e:
        typer.echo(f"❌ Failed to read backup file: {e}")
        raise typer.Exit()

    mnemonic = data.get("mnemonic")
    passphrase = data.get("passphrase", "")
    wallet_name = typer.prompt("📝 Name this imported wallet")

    try:
        hdwallet = create_wallet(mnemonic, passphrase)
    except Exception as e:
        typer.echo(f"❌ Failed to reconstruct HD wallet: {e}")
        raise typer.Exit()

    addresses = []
    for i in range(len(data.get("addresses", []))):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)
        addresses.append({
            "index": i,
            "path": f"m/44'/175'/0'/0/{i}",
            "address": hdwallet.address(),
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key(),
        })
        hdwallet.clean_derivation()

    hdwallet.name = wallet_name
    hdwallet.created_at = data.get("created_at", datetime.utcnow().isoformat())
    hdwallet.first_address = addresses[0]["address"] if addresses else ""
    hdwallet.addresses = addresses

    save_wallet(wallet_name, hdwallet)
    typer.echo(f"✅ Wallet '{wallet_name}' imported successfully.")


__all__=[
    "wallet_file_path"
    "create_wallet",
    "load_wallet",
    "save_wallet",
    "list_wallets",
    "WALLET_DIR", "pubkeyhash", "p2sh"]