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


# ─── 🧩 MODULE IMPORTS ──────────────────────────────────────────────────────────

# 🌐 CLI entrypoint and configuration loader
from .cli import evrmail_cli_app, evrmail_flet_app
from .config import load_config

# 🔌 Evrmore RPC and ZeroMQ clients
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient

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
        zmq_host=evrmail_config.get('rpc_host'),
        zmq_port=28332,
        rpc_client=rpc_client,
        auto_decode=True,
        auto_create_rpc=False
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

__all__ = ["evrmail_config", "rpc_client", "zmq_client", "main"]

# ─── 🚀 MAIN ENTRYPOINT ────────────────────────────────────────────────────────

def main():
    """Launch the EvrMail CLI app."""
    evrmail_cli_app()

def flet():
    """ Launch qt app """
    evrmail_flet_app()

# 🧪 Allow `python -m evrmail` to work
if __name__ == "__main__":
    main()
