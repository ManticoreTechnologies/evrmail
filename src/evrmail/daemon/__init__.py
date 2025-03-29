
import json
import os
import subprocess
import time
from pathlib import Path
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmail.config import load_config   
from evrmail.utils.decrypt_message import decrypt_message

config = load_config()

STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def load_inbox():
    if INBOX_FILE.exists():
        with open(INBOX_FILE, "r") as f:
            return json.load(f)
    return []

def save_inbox(messages):
    with open(INBOX_FILE, "w") as f:
        json.dump(messages, f, indent=2)

def read_message(cid: str):
    try:
        result = subprocess.run(["ipfs", "cat", cid], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[IPFS ERROR] {e}")
        return None

def load_processed_txids():
    if PROCESSED_TXIDS_FILE.exists():
        with open(PROCESSED_TXIDS_FILE, "r") as f:
            return json.load(f)
    return []

def save_processed_txids(txids):
    with open(PROCESSED_TXIDS_FILE, "w") as f:
        json.dump(txids, f, indent=2)



__all__ = ["INBOX_FILE", "PROCESSED_TXIDS_FILE", "STORAGE_DIR"]