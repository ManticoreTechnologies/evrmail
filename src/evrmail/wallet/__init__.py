# ─────────────────────────────────────────────────────────────
# 📦 evrmail.wallet.__init__
#
# 📌 PURPOSE:
#   Re-exports core wallet functions:
#   - 📬 pubkey ➜ pubkeyhash ➜ address
#   - 🧠 HD wallet creation, loading, saving
#   - 🔍 Script decoding utilities
#   - 🌐 RPC client & ZMQ event listener
# ─────────────────────────────────────────────────────────────


# 📦 Standard + External Imports
import os
import json
from datetime import datetime

# 🧠 HD Wallet libs
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.mnemonics.bip39 import BIP39Mnemonic
from hdwallet.derivations import BIP44Derivation
from mnemonic import Mnemonic

# 🧰 Typer for CLI integration
import typer

# 🧠 Language seed generator
mnemo = Mnemonic("english")


# ─────────────────────────────────────────────────────────────
# 📁 Wallet File Structure
# ─────────────────────────────────────────────────────────────

# 📁 Wallet save directory
WALLET_DIR = os.path.expanduser("~/.evrmail/wallets")

# ✅ Ensure wallet directory exists
os.makedirs(WALLET_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 🔁 Internal Modules (Public API Exports)
# ─────────────────────────────────────────────────────────────

# 🔗 Hashing & Address Conversion
from .pubkeyhash import *

# 🔐 P2SH / Script-based operations
from .p2sh import *

# 🧪 Script decoding utils (e.g., tx analysis)
#   - wallet.script.decode_script(script_hex)
#   - wallet.pubkeyhash.to_address(pubkeyhash)
#   - wallet.pubkey.to_hash(pubkey)

from .addresses import *
from .store import load_wallet, list_wallets
from .utils import *


__all__ = [
    "WALLET_DIR",
    "addresses",
    "load_wallet",
    "list_wallets",
    "utils",
]