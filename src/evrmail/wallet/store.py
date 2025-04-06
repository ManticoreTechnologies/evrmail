
# 📦 Imports
import os
import json
from datetime import datetime
from hdwallet import HDWallet
from hdwallet.derivations import BIP44Derivation
from . import WALLET_DIR
from .utils import wallet_file_path

def load_wallet(name: str):
    path = wallet_file_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
    
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