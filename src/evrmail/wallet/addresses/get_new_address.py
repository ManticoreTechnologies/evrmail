from evrmail.wallet.store import load_wallet, save_wallet, update_map_files
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.derivations import BIP44Derivation
from hdwallet.mnemonics.bip39 import BIP39Mnemonic

import typer
import json
from pathlib import Path

# 📍 Global map path for friendly names
from evrmail.wallet.store import MAP_DIR

def get_new_address(wallet_name: str, friendly_name: str = "") -> dict:
    """📬 Generate a new address in the given wallet."""
    wallet = load_wallet(wallet_name)

    # 🧠 Reconstruct HDWallet
    passphrase = wallet.get("mnemonic_passphrase", "")
    hdwallet = HDWallet(cryptocurrency=Evrmore, passphrase=passphrase)
    hdwallet.from_mnemonic(BIP39Mnemonic(mnemonic=wallet["mnemonic"]))
    index = len(wallet["addresses"])
    derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=index)
    hdwallet.update_derivation(derivation)

    # 🛡️ Check for duplicate friendly name in global map
    if friendly_name:
        map_path = MAP_DIR / "by-friendly-name.json"
        if map_path.exists():
            with open(map_path, "r") as f:
                friendly_map = json.load(f)
            if friendly_name in friendly_map:
                existing = friendly_map[friendly_name]
                raise ValueError(f"Friendly name '{friendly_name}' already exists globally -> Address: {existing['address']} (Wallet: {existing['wallet']})")

    # 🧾 Build address data
    address_data = {
        "index": index,
        "path": hdwallet.path(),
        "address": hdwallet.address(),
        "public_key": hdwallet.public_key(),
        "private_key": hdwallet.private_key(),
        "friendly_name": friendly_name or f"address_{index}"
    }

    # 📚 Save to wallet and update maps
    wallet["addresses"][address_data["address"]] = address_data
    save_wallet(wallet)

    # 🗺️ Update global maps
    update_map_files({
        "by-index": {str(index): {"address": address_data["address"], "wallet": wallet_name}},
        "by-path": {address_data["path"]: {"address": address_data["address"], "wallet": wallet_name}},
        "by-friendly-name": {address_data["friendly_name"]: {"address": address_data["address"], "wallet": wallet_name}}
    })

    return address_data
