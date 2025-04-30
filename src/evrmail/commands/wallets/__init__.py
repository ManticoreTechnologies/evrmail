"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 💼 evrmail wallets [COMMAND]
# Manage wallets and keys for EvrMail.
# 
# 📌 Subcommands:
# 
#   🛠️  create   — Create a new wallet (with optional passphrase)
#   📂  list     — List all saved wallets
#   📄  show     — Show metadata for a specific wallet
#   💾  export   — Export a wallet to file
#   📥  import   — Import a wallet from file
#   🔄  init     — Create or restore wallet from mnemonic
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer

wallets_app = typer.Typer(
    name="wallets",
    help="💼 Manage your Evrmore wallets"
)

# 🔌 Subcommands
from .create import create_app
from .list import list_app
from .show import show_app
from .export import export_app
from .lmport import import_app  # 🍝 nice typo recovery 😄

# 🔗 Register Subcommands
wallets_app.add_typer(create_app)
wallets_app.add_typer(list_app)
wallets_app.add_typer(show_app)
wallets_app.add_typer(export_app)
wallets_app.add_typer(import_app)

# 📤 Export
__all__ = ["wallets_app"]
