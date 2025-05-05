# ─── 📦 EvrMail Daemon Init ──────────────────────────────────────────────────

import json
import os
import subprocess
import threading
import time
import logging
from pathlib import Path

from evrmail.config import load_config
from evrmail.utils import (
    configure_logging, register_callback,
    APP, GUI, DAEMON, WALLET, CHAIN, NETWORK
)

# 🛠 Filesystem Monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─── 📂 Paths and Config ──────────────────────────────────────────────────────

config = load_config()
STORAGE_DIR = Path.home() / ".evrmail"
UTXO_DIR = STORAGE_DIR / "utxos"
INBOX_FILE = STORAGE_DIR / "inbox.json"
PROCESSED_TXIDS_FILE = STORAGE_DIR / "processed_txids.json"

# Create necessary directories
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UTXO_DIR.mkdir(parents=True, exist_ok=True)

# ─── 🔥 Realtime UTXO Monitoring ──────────────────────────────────────────────

class ConfirmedFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("confirmed.json"):
            from evrmail.utils import daemon as daemon_log
            daemon_log("info", "🔥 confirmed.json modified, reloading addresses...")
            try:
                from .__main__ import reload_known_addresses
                reload_known_addresses()
            except Exception as e:
                daemon_log("error", f"⚠️ Failed to reload addresses: {e}")

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

def start_daemon_threaded(log_callback=None, debug_mode=False):
    """Start the EvrMail daemon in a background thread"""
    # Set up logging
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Configure our logger
    configure_logging(level=log_level)
    
    # Register callbacks to forward logs to the GUI
    if log_callback:
        # Register callback for all daemon-related categories
        unsubscribe_funcs = []
        
        # Helper to adapt logger callback format to simpler format expected by GUI
        def adapter(category, level_name, level_num, message, details=None):
            # If we have details, add them to the message
            if details:
                log_message = message
                if isinstance(details, dict) and details:
                    details_str = ": " + ", ".join(f"{k}={v}" for k, v in details.items())
                    log_message += details_str
                log_callback(log_message)
            else:
                log_callback(message)
        
        # Register for each category
        for category in [DAEMON, CHAIN, WALLET, NETWORK]:
            unsubscribe = register_callback(adapter, category)
            unsubscribe_funcs.append(unsubscribe)
    
    # Start the daemon in a thread
    def run():
        import evrmail.daemon.__main__ as main_module
        main_module.main(debug_mode=debug_mode)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    
    return thread

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
        from evrmail.utils import network as network_log
        network_log("error", f"IPFS Error: {e}")
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
