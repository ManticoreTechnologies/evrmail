import os
import json


IPFS_BINARY_PATH = "/usr/local/bin/ipfs"
IPFS_DIR = os.path.expanduser("~/.ipfs")

CONFIG_FILE = os.path.expanduser("~/.evrmail_config.json")

def load_config():
    """Load the config file."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    return config

def save_config(config):
    """Save the config file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

 