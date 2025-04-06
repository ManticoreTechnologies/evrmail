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

# ⚙️ EvrMail config path
CONFIG_FILE = os.path.expanduser("~/.evrmail/config.json")

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


# ─────────────────────────────────────────────────────────────
# 🌐 RPC Client & ZMQ Listener
# ─────────────────────────────────────────────────────────────

# 🔌 Evrmore node interaction (RPC)
from evrmore_rpc import EvrmoreClient

# 📡 Real-time events via ZeroMQ
from evrmore_rpc.zmq import EvrmoreZMQClient

# 🧠 Instantiate clients (default hardcoded for now)
rpc_client = EvrmoreClient(
    url="tcp://77.90.40.55",
    rpcuser="evruser",
    rpcpassword="changeThisToAStrongPassword123",
    rpcport=8819,
)

zmq_client = EvrmoreZMQClient(
    zmq_host="77.90.40.55",
    zmq_port=28332,
    rpc_client=rpc_client,
    auto_decode=True,
    auto_create_rpc=False,
)

from .addresses import *
from .store import load_wallet, list_wallets
from .utils import *
__all__ = [
    "WALLET_DIR",
    "CONFIG_FILE",
    "addresses",
    "load_wallet",
    "list_wallets",
    "utils",
]