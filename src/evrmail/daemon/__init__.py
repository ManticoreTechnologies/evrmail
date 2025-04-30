# ─── 📦 EvrMail Daemon Init ──────────────────────────────────────────────────

import json
import os
import subprocess
import threading
import time
from pathlib import Path

from evrmail.config import load_config

# 🛠 Filesystem Monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─── 📂 Paths and Config ──────────────────────────────────────────────────────

config = load_config()
STORAGE_DIR = Path.home() / ".evrmail"
UTXO_DIR = STORAGE_DIR / "utxos"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─── 🔥 Realtime UTXO Monitoring ──────────────────────────────────────────────

class ConfirmedFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("confirmed.json"):
            print("[Daemon] 🔥 confirmed.json modified, reloading addresses...")
            try:
                from .__main__ import reload_known_addresses
                reload_known_addresses()
            except Exception as e:
                print(f"[Daemon] ⚠️ Failed to reload addresses: {e}")

def monitor_confirmed_utxos_realtime():
    observer = Observer()
    handler = ConfirmedFileHandler()
    observer.schedule(handler, path=str(UTXO_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# ─── 🚀 Daemon Launcher ───────────────────────────────────────────────────────

def start_daemon_threaded(log_callback=None):
    def run():
        import evrmail.daemon.__main__ as main_module
        main_module.main()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# ─── 📬 Inbox & Processed TXIDs ────────────────────────────────────────────────

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

# ─── 🌐 IPFS Support ──────────────────────────────────────────────────────────

def read_message(cid: str):
    try:
        result = subprocess.run(["ipfs", "cat", cid], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[IPFS ERROR] {e}")
        return None

# ─── ✅ Exportable API ─────────────────────────────────────────────────────────

__all__ = [
    "start_daemon_threaded",
    "monitor_confirmed_utxos_realtime",
    "load_inbox",
    "save_inbox",
    "load_processed_txids",
    "save_processed_txids",
    "read_message",
    "STORAGE_DIR",
    "INBOX_FILE",
    "PROCESSED_TXIDS_FILE",
]
