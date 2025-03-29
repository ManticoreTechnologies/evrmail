import os
import json
from pathlib import Path

# === Defaults ===
IPFS_BINARY_PATH = "/usr/local/bin/ipfs"
IPFS_DIR = os.path.expanduser("~/.ipfs")
CONFIG_PATH = Path.home() / ".evrmail_config.json"

DEFAULT_CONFIG = {
    "ipfs_path": IPFS_DIR,
    "ipfs_binary": IPFS_BINARY_PATH,
    "addresses": {},
    "active_address": None,
    "aliases": {},  # For clearnet email aliases like "phoenix@manticore.email"
}

def ensure_config_dir():
    """Make sure config directory exists."""
    config_dir = CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)


def load_config():
    """Load and return the EvrMail config, with defaults filled in."""
    ensure_config_dir()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r") as f:
            config = json.load(f)
    else:
        config = {}

    # Fill in any missing defaults
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)

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
