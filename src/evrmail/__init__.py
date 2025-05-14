"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 📦 evrmail.__init__
#
# 📌 PURPOSE:
#   - 📦 evrmail.cli
#   - 📦 evrmail.config
#   - 🔌 evrmore_rpc
#   - 🔌 evrmore_rpc.zmq
# ─────────────────────────────────────────────────────────────

import os
from pathlib import Path
import sys
import logging

# Setup default logging at import time
from evrmail.utils.logger import configure_logging, APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG
log_dir = configure_logging(level=logging.INFO)
print(f"Logs directory configured: {log_dir}")

__version__ = "0.1.0"
__author__ = "Cymos"
__license__ = "MIT"

# Create data directories if they don't exist
HOME_DIR = Path.home() / ".evrmail"
WALLETS_DIR = HOME_DIR / "wallets"
KEYS_DIR = HOME_DIR / "keys"
LOGS_DIR = HOME_DIR / "logs"

for directory in [HOME_DIR, WALLETS_DIR, KEYS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# ─── 🧩 MODULE IMPORTS ──────────────────────────────────────────────────────────

# 🌐 CLI entrypoint and configuration loader
from .cli import evrmail_cli_app, evrmail_gui_app
from .config import load_config, save_config

# 🔌 Evrmore RPC and ZeroMQ clients
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import ZMQTopic, EvrmoreZMQClient

# ─── ⚙️ CONFIGURATION & CLIENT INITIALIZATION ──────────────────────────────────

# 📁 Load the EvrMail config from ~/.evrmail/config.json
evrmail_config = load_config()

# 🔐 Initialize RPC + ZMQ clients using cookie-based or explicit auth
if evrmail_config.get('rpc_user') and evrmail_config.get('rpc_password'):
    # ⚠️ Less secure: using explicit RPC credentials
    #print("⚠️ WARNING! You are using RPC username and password for authentication.")
    #print("🔐 Tip: For better security, use cookie-based auth by removing rpc_user and rpc_password from your config.")
    
    rpc_client = EvrmoreClient(
        url=evrmail_config.get('rpc_host'),
        rpcuser=evrmail_config.get('rpc_user'),
        rpcpassword=evrmail_config.get('rpc_password'),
        rpcport=evrmail_config.get('rpc_port')
    )
    zmq_client = EvrmoreZMQClient(
        topics=[ZMQTopic.RAW_TX, ZMQTopic.RAW_BLOCK],
        zmq_host=evrmail_config.get('rpc_host').split('tcp://')[1]
    )
else:
    # ✅ Recommended: use cookie-based authentication
    #print("✅ Using cookie-based authentication for evrmore_rpc — best practice!")
    rpc_client = EvrmoreClient()
    zmq_client = EvrmoreZMQClient()


# 🧪 Test connection to Evrmore node
try:
    rpc_client.getblockchaininfo()
except Exception as e:
    print("❌ Failed to connect to evrmore_rpc. Is your node running locally?\n", e)
    exit(1)
else:
    pass
    #print("✅ evrmore_rpc client initialized successfully.")

# ─── 📤 EXPORTS ────────────────────────────────────────────────────────────────

__all__ = [
    "evrmail_config", 
    "rpc_client", 
    "zmq_client", 
    "main",
    "__version__", 
    "__author__", 
    "__license__",
    "HOME_DIR",
    "WALLETS_DIR",
    "KEYS_DIR",
    "LOGS_DIR"
]

# ─── 🚀 MAIN ENTRYPOINT ────────────────────────────────────────────────────────

def main():
    """Launch the EvrMail CLI app."""
    evrmail_cli_app()

def gui():
    """Launch Qt-based GUI app."""
    evrmail_gui_app()

# 🧪 Allow `python -m evrmail` to work
if __name__ == "__main__":
    main()
