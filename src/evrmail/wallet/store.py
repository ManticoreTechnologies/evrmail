# 💼 Wallet Manager — EvrMail HD Wallet System (Multiwallet Mode)

import os
import json
from datetime import datetime
from pathlib import Path

import typer
from hdwallet import HDWallet
from hdwallet.derivations import BIP44Derivation
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.mnemonics.bip39 import BIP39Mnemonic

from . import WALLET_DIR
from .utils import wallet_file_path, generate_mnemonic

# 📂 New Map Storage Directory
WALLET_DIR = Path(WALLET_DIR)
MAP_DIR = WALLET_DIR / "maps"
MAP_DIR.mkdir(parents=True, exist_ok=True)

# 🤔 Create new HD wallet and store to disk
def create_wallet(name: str, mnemonic: str = None, passphrase: str = "", address_count: int = 1000) -> dict:
    mnemonic = mnemonic or generate_mnemonic()
    passphrase = passphrase or ""

    hdwallet = HDWallet(cryptocurrency=Evrmore, passphrase=passphrase)
    hdwallet.from_mnemonic(BIP39Mnemonic(mnemonic=mnemonic))

    addresses = {}
    by_index, by_path, by_name, by_pubkey = {}, {}, {}, {}

    for i in range(address_count):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)

        address_data = {
            "index": i,
            "path": hdwallet.path(),
            "address": hdwallet.address(),
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key(),
            "friendly_name": f"address_{name}_{i}"
        }
        addr = address_data["address"]
        addresses[addr] = address_data

        by_index[str(i)] = {"address": addr, "wallet": name}
        by_path[address_data["path"]] = {"address": addr, "wallet": name}
        by_name[address_data["friendly_name"]] = {"address": addr, "wallet": name}
        by_pubkey[address_data["public_key"]] = {"address": addr, "wallet": name}

    # 📆 Save maps to global map files
    _update_map_file("by-index.json", by_index)
    _update_map_file("by-path.json", by_path)
    _update_map_file("by-friendly-name.json", by_name)
    _update_map_file("by-pubkey.json", by_pubkey)

    # 📆 Save the wallet itself
    wallet_data = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "mnemonic": mnemonic,
        "mnemonic_passphrase": passphrase,
        "extended_public_key": hdwallet.xpublic_key(),
        "extended_private_key": hdwallet.xprivate_key(),
        "HD_seed": hdwallet.seed(),
        "addresses": addresses
    }

    with open(wallet_file_path(name), "w") as f:
        json.dump(wallet_data, f, indent=2)

    return wallet_data

# 📄 Save a wallet object to file
def save_wallet(wallet: dict):
    with open(wallet_file_path(wallet["name"]), "w") as f:
        json.dump(wallet, f, indent=2)

# 📅 Load a wallet by name
def load_wallet(name: str) -> dict | None:
    path = wallet_file_path(name)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

# 📃 List all wallets
def list_wallets() -> list[str]:
    return [f.replace(".json", "") for f in os.listdir(WALLET_DIR) if f.endswith(".json")]

# 📆 Global Map Helpers
def _update_map_file(filename: str, new_data: dict):
    path = MAP_DIR / filename
    if path.exists():
        with open(path, "r") as f:
            existing = json.load(f)
    else:
        existing = {}

    existing.update(new_data)

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

# 🗘️ Update global address maps with new entries.
def update_map_files(updates: dict):
    """
    🗘️ Update global address maps with new entries.
    `updates` should be a dictionary with keys:
      - "by-index"
      - "by-path"
      - "by-friendly-name"
      - "by-pubkey"
    Each maps to a dictionary of { key: {address, wallet} }
    """
    import json
    from pathlib import Path
    from evrmail.wallet import WALLET_DIR

    map_dir = Path(WALLET_DIR) / "maps"
    map_dir.mkdir(parents=True, exist_ok=True)

    for map_type, new_entries in updates.items():
        path = map_dir / f"{map_type}.json"
        if path.exists():
            with open(path, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        existing.update(new_entries)

        with open(path, "w") as f:
            json.dump(existing, f, indent=2)

# 📄 Export Wallet Backup
def export_wallet(name: str, include_addresses: bool = True):
    wallet = load_wallet(name)
    if wallet is None:
        typer.echo(f"❌ Wallet '{name}' not found.")
        raise typer.Exit()

    export_data = {
        "name": wallet.get("name"),
        "created_at": wallet.get("created_at"),
        "mnemonic": wallet.get("mnemonic"),
        "passphrase": wallet.get("mnemonic_passphrase", "")
    }

    if include_addresses:
        export_data["addresses"] = wallet.get("addresses", {})

    export_path = typer.prompt("📅 Export file path", default=f"./{name}_backup.json")

    try:
        with open(os.path.expanduser(export_path), "w") as f:
            json.dump(export_data, f, indent=2)
        typer.echo(f"✅ Wallet exported to: {export_path}")
    except Exception as e:
        typer.echo(f"❌ Failed to export wallet: {e}")
        raise typer.Exit()

# 📅 Restore Wallet from Mnemonic (like init)
def restore_wallet(name: str="", mnemonic: str=None, passphrase: str = "", address_count: int = 1000):
    """
    🔄 Restore wallet from existing mnemonic phrase and update maps.
    """
    from evrmail.wallet.utils import generate_mnemonic
    import random

    def random_wallet_name():
        words = generate_mnemonic().split()
        name = f"wallet_{random.choice(words)}_{random.choice(words)}_{random.randint(1000, 9999)}"
        return name

    if not name:
        name = random_wallet_name()
        
    return create_wallet(name=name, mnemonic=mnemonic, passphrase=passphrase, address_count=address_count)

# 📅 Import Wallet Backup and update global maps
def import_wallet(path: str):
    try:
        with open(os.path.expanduser(path), "r") as f:
            data = json.load(f)
    except Exception as e:
        typer.echo(f"❌ Failed to read backup file: {e}")
        raise typer.Exit()

    mnemonic = data.get("mnemonic")
    passphrase = data.get("passphrase", "")
    wallet_name = typer.prompt("📝 Name this imported wallet")

    if not mnemonic:
        typer.echo("❌ Backup file missing mnemonic.")
        raise typer.Exit()

    return create_wallet(wallet_name, mnemonic, passphrase, address_count=len(data.get("addresses", {})))
