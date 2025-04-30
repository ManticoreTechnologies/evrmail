# evrmail/daemon/shared.py

import os
import json
from pathlib import Path

# 📂 Important Paths
STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"
UTXO_DIR = STORAGE_DIR / "utxos"

# 📜 Utilities
def load_inbox():
    if INBOX_FILE.exists():
        return json.loads(INBOX_FILE.read_text())
    return []

def save_inbox(messages):
    INBOX_FILE.write_text(json.dumps(messages, indent=2))

def load_processed_txids():
    if PROCESSED_TXIDS_FILE.exists():
        return json.loads(PROCESSED_TXIDS_FILE.read_text())
    return []

def save_processed_txids(txids):
    PROCESSED_TXIDS_FILE.write_text(json.dumps(txids, indent=2))
