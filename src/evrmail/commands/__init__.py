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
#   🏷️ addresses   — Manage addresses and keys
#   💳 balance     — Show EVR or asset balances
#   📥 receive     — Get a fresh receive address
#   🚀 send        — Send EVR, assets, or encrypted messages
#   🔧 dev         — Developer & debug tools
#   📱 contacts    — Manage your address book
#   🔄 ipfs        — Manage IPFS
#   📜 logs        — View and manage logs
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from .addresses import addresses_app
from .contacts import contacts_app
from .wallets import wallets_app
from .balance import balance_app
from .receive import receive_app
from .send import send_app
from .ipfs import ipfs_app
from .dev import dev_app
from .logs import logs_app

# 🌐 Exported CLI apps
__all__ = [
    "addresses_app",
    "contacts_app",
    "wallets_app",
    "balance_app",
    "receive_app",
    "send_app",
    "ipfs_app",
    "dev_app",
    "logs_app",
]
