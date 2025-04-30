"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 📦 evrmail.config
#
# 📌 PURPOSE:
#   - 📦 evrmail.config
# ─────────────────────────────────────────────────────────────

import os
import json
from pathlib import Path

# === Defaults ===
IPFS_BINARY_PATH = "/usr/local/bin/ipfs"
IPFS_DIR = os.path.expanduser("~/.ipfs")
CONFIG_PATH = Path.home() / ".evrmail" / "config.json"

DEFAULT_CONFIG = {
    "ipfs_path": IPFS_DIR,
    "ipfs_binary": IPFS_BINARY_PATH,
    "addresses": {},
    "active_address": None,
    "aliases": {},  
    "rpc_host": "tcp://77.90.40.55",
    "rpc_port": 8819,
    "rpc_user": "evruser",
    "rpc_password": "changeThisToAStrongPassword123"
}

"""
    Ensure the config directory exists and create a default config if it doesn't.
"""
def ensure_config_dir():
    
    """ Check if config directory exists, create it if it doesn't. """
    config_dir = CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        """ Create a default config if it doesn't exist. """
        with CONFIG_PATH.open("w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

"""
    Load and return the EvrMail config, with defaults filled in.
"""
def load_config():
    """ Ensure the config directory exists and create a default config if it doesn't. """

    ensure_config_dir() # Creates a default config if it doesn't exist

    """ Load the config from disk. """
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r") as f:
            config = json.load(f)
    else:
        config = {}

    # rpc_user and rpc_password are optional, so we need to check if they exist
    if not config.get("rpc_user") or not config.get("rpc_password"):
        print("WARNING! No rpc_user or rpc_password found in config, evrmore_rpc will attempt to use a local cookie file.")

    return config

def save_config(config):
    """Save the EvrMail config to disk."""
    ensure_config_dir()
    with CONFIG_PATH.open("w") as f:
        json.dump(config, f, indent=2)

def get_active_address():
    """Return the active address or raise if not set."""
    config = load_config()
    active = config.get("active_address")
    if not active:
        raise ValueError("No active address is set. Use `evrmail addresses use <addr>`.")
    return active
