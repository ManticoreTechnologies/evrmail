"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 📦 evrmail.commands
#
# 🧩 CLI Command Modules:
#   💼 wallets     — Manage your Evrmore wallets
#   🏷️  addresses   — Manage addresses and keys
#   💳 balance     — Show EVR or asset balances
#   🚀 send        — Send EVR, assets, or encrypted messages
#   📥 receive     — Get a fresh receive address
#   📱 contacts    — Manage your address book
#   🔧 dev         — Developer & debug tools
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from .wallets import wallets_app
from .addresses import addresses_app
from .balance import balance_app
from .send import send_app
from .receive import receive_app
from .contacts import contacts_app
from .dev import dev_app
from .ipfs import ipfs_app

# 🌐 Exported CLI apps
__all__ = [
    "wallets_app",
    "addresses_app",
    "balance_app",
    "send_app",
    "receive_app",
    "contacts_app",
    "dev_app",
    "ipfs_app"
]
