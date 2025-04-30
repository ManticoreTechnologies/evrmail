"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 🧱 evrmail wallets create
#
# 📌 USAGE:
#   $ evrmail wallets create [<name>] [-p|--pass <passphrase>] [--raw]
#
# 🛠️ DESCRIPTION:
#   Creates a new wallet using a generated mnemonic phrase.
#   An optional BIP39 passphrase can be provided for extra security.
#
#   📂 The wallet is saved to: ~/.evrmail/wallets/<name>.json
#   ⚠️  If a wallet with that name already exists, creation is aborted.
#   📄 Use --raw to get the full mnemonic and xpub in JSON
# ─────────────────────────────────────────────────────────────

""" Tested and working! """

# 📦 Imports
import typer
import json
import random
from evrmail import wallet
from evrmail.wallet import utils

create_app = typer.Typer()

from evrmail.wallet.utils import generate_mnemonic
import random

def random_wallet_name():
    words = generate_mnemonic().split()
    name = f"wallet_{random.choice(words)}_{random.choice(words)}_{random.randint(1000, 9999)}"
    return name
# ─────────────────────────────────────────────────────────────
# 🛠️ Create Command
# ─────────────────────────────────────────────────────────────
@create_app.command(name="create", help="🛠️  Create a new wallet (with optional passphrase)")
def create(
    name: str = typer.Argument(None, help="🆕 Name for the wallet (optional, random if omitted)"),
    passphrase: str = typer.Option("", "--pass", "-p", help="🔐 Optional BIP39 passphrase"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output wallet details as JSON")
):
    # 🎲 Generate a name if none provided
    name = name or random_wallet_name()

    # 🔍 Check if wallet already exists
    if wallet.store.load_wallet(name) is not None:
        if raw:
            typer.echo(json.dumps({"error": f"Wallet `{name}` already exists."}, indent=2))
        else:
            typer.echo(f"⚠️  Wallet `{name}` already exists. Choose another name.")
        raise typer.Exit(1)

    # 🧠 Generate mnemonic & create wallet
    mnemonic = utils.generate_mnemonic()
    new_wallet = wallet.store.create_wallet(name, mnemonic, passphrase)

    # 📤 Output
    if raw:
        typer.echo(json.dumps(new_wallet, indent=2))
    else:
        typer.echo(f"✅ Wallet `{name}` created and saved to {wallet.WALLET_DIR}/{name}.json")
