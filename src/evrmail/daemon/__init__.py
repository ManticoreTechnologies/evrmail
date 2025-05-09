# ─── 📦 EvrMail Daemon Init ──────────────────────────────────────────────────

import json
import os
import subprocess
import threading
import time
import logging
from pathlib import Path

from evrmail.config import load_config, save_config
from evrmail.utils import (
    configure_logging, register_callback,
    DAEMON, WALLET, CHAIN, NETWORK
)
from evrmail.crypto import wif_to_pubkey
from evrmail.wallet.addresses import validate as validate_evr_address, get_address

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

class EVRMailDaemon:
    def __init__(self):
        self.config = load_config()
        self.running = False
        self.threads = []
        
    def process_contact_request(self, message):
        """Process an incoming contact request message."""
        try:
            from evrmail.utils import daemon as daemon_log
            
            daemon_log("debug", f"Processing contact request message: {json.dumps(message, default=str)}")
            
            # Get sender address - might be at different levels depending on message format
            sender = None
            if isinstance(message, dict):
                # Try different possible locations for the sender address
                sender = message.get("from")
                
                # If sender not found, try nested 'content'
                if not sender and isinstance(message.get("content"), dict):
                    sender = message.get("content", {}).get("from")
                
                # If sender still not found, try nested 'raw'
                if not sender and isinstance(message.get("raw"), dict):
                    sender = message.get("raw", {}).get("from")
            
            if not sender:
                daemon_log("error", f"No sender address found in contact request: {message}")
                return False
                
            # Extract contact info from message
            name = None
            pubkey = None
            
            # Try to get name from different possible locations
            if isinstance(message, dict):
                name = message.get("name")
                if not name and isinstance(message.get("content"), dict):
                    name = message.get("content", {}).get("name")
                if not name and isinstance(message.get("raw"), dict):
                    name = message.get("raw", {}).get("name")
            
            # Try to get pubkey from different possible locations
            if isinstance(message, dict):
                pubkey = message.get("pubkey")
                if not pubkey and isinstance(message.get("content"), dict):
                    pubkey = message.get("content", {}).get("pubkey")
                if not pubkey and isinstance(message.get("raw"), dict):
                    pubkey = message.get("raw", {}).get("pubkey")
            
            contact_info = {
                "name": name or "Unnamed",
                "pubkey": pubkey,
                "status": "pending"
            }
            
            # Validate the sender's address
            if not sender or not validate_evr_address(sender)["isvalid"]:
                daemon_log("error", f"Invalid sender address in contact request: {sender}")
                return False
                
            # Check if we already have this address in our wallet
            from evrmail.wallet.addresses import get_all_addresses
            addresses = get_all_addresses()
            our_addresses = []
            
            # Handle both string and dict address formats
            for addr in addresses:
                if isinstance(addr, dict):
                    our_addresses.append(addr.get("address"))
                else:
                    our_addresses.append(addr)
                    
            if sender in our_addresses:
                daemon_log("info", f"Ignoring contact request from our own address: {sender}")
                return False
                
            # Store the contact request
            requests = self.config.get("contact_requests", {})
            
            # Check if we already have this contact
            contacts = self.config.get("contacts", {})
            if sender in contacts:
                daemon_log("info", f"Contact request from {sender} ignored - already in contacts")
                return False
                
            # Add to requests if not already there
            if sender in requests:
                daemon_log("info", f"Contact request from {sender} already pending")
                return False
                
            # Store the new request
            requests[sender] = contact_info
            self.config["contact_requests"] = requests
            save_config(self.config)
            
            daemon_log("info", f"Stored contact request from {sender}")
            return True
            
        except Exception as e:
            from evrmail.utils import daemon as daemon_log
            daemon_log("error", f"Error processing contact request: {e}")
            import traceback
            daemon_log("error", traceback.format_exc())
            return False
            
    def send_contact_request(self, recipient_address: str, name: str = None, from_address: str = None):
        """Send a contact request to another user."""
        try:
            from evrmail.utils import daemon as daemon_log
            from evrmail.wallet.addresses import get_all_addresses
            from evrmail.commands.send.send_msg import send_contact_request_core
            
            # Get our address and pubkey if not specified
            if not from_address:
                addresses = get_all_addresses()
                if not addresses:
                    daemon_log("error", "No addresses available to send contact request")
                    return False
                our_address = addresses[0]
            else:
                our_address = from_address
                
            # Validate recipient address
            if not validate_evr_address(recipient_address)["isvalid"]:
                daemon_log("error", f"Invalid recipient address for contact request: {recipient_address}")
                return False
            
            # Use the dedicated contact request function
            daemon_log("info", f"Sending contact request from {our_address} to {recipient_address}")
            
            # Call our new dedicated function for contact requests
            txid = send_contact_request_core(
                to_address=recipient_address,
                from_address=our_address,
                name=name,
                fee_rate=0.01,
                dry_run=False,
                debug=True  # Set to True for more verbose logging
            )
            
            if not txid:
                daemon_log("error", "Failed to send contact request")
                return False
                
            daemon_log("info", f"Sent contact request to {recipient_address} from {our_address}", details={
                "txid": txid
            })
            
            return True
            
        except Exception as e:
            from evrmail.utils import daemon as daemon_log
            import traceback
            daemon_log("error", f"Error sending contact request: {e}")
            daemon_log("error", traceback.format_exc())
            return False
            
    def run(self):
        """Main daemon loop."""
        from evrmail.utils import daemon as daemon_log
        self.running = True
        
        while self.running:
            try:
                # Process any pending messages
                # TODO: Implement message processing loop
                
                time.sleep(1)  # Prevent busy waiting
                
            except Exception as e:
                daemon_log("error", f"Error in daemon loop: {e}")
                time.sleep(5)  # Back off on error
                
    def stop(self):
        """Stop the daemon."""
        self.running = False
        for thread in self.threads:
            thread.join()
            
    def start(self):
        """Start the daemon in a new thread."""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
        return thread
