import eel
import json
import os
from pathlib import Path
import time
import base64
import hashlib
import threading

# Initialize Eel with the web directory
eel.init('web')

# Configuration and global variables
INBOX_FILE = Path.home() / ".evrmail" / "inbox.json"
SENT_FILE = Path.home() / ".evrmail" / "sent.json"
LOG_ENTRIES = []

# ---- Helper Functions ----
def load_messages(file_path):
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_sent_message(to, subject, content, txid, dry_run=False):
    SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SENT_FILE.exists():
        sent = json.loads(SENT_FILE.read_text())
    else:
        sent = []

    from datetime import datetime
    sent.append({
        "to": to,
        "subject": subject,
        "content": content,
        "txid": txid,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
    })

    SENT_FILE.write_text(json.dumps(sent, indent=2))

# ---- Exposed Functions ----

@eel.expose
def get_inbox_messages():
    """Get all inbox messages"""
    inbox_msgs = load_messages(INBOX_FILE)
    formatted_msgs = []
    
    for msg in inbox_msgs:
        content = msg.get("content", {})
        sender = content.get("from", "Unknown")
        subject = content.get("subject", "(No Subject)")
        body = content.get("content", "(No Content)")
        
        formatted_msgs.append({
            "type": "received",
            "subject": subject,
            "from": sender,
            "body": body
        })
    
    return formatted_msgs

@eel.expose
def get_sent_messages():
    """Get all sent messages"""
    sent_msgs = load_messages(SENT_FILE)
    formatted_msgs = []
    
    for msg in sent_msgs:
        is_dry_run = msg.get("dry_run", False)
        recipient = msg.get("to", "Unknown")
        subject = msg.get("subject", "(No Subject)")
        body = msg.get("content", "(No Content)")
        
        formatted_msgs.append({
            "type": "sent",
            "subject": subject,
            "to": recipient,
            "body": body,
            "is_dry_run": is_dry_run
        })
    
    return formatted_msgs

@eel.expose
def send_message(to, subject, content, outbox=None, dry_run=False):
    """Send a new message"""
    try:
        # Simulate sending a message
        print(f"Sending message to: {to}")
        print(f"Subject: {subject}")
        print(f"Content: {content}")
        print(f"Outbox: {outbox}")
        print(f"Dry Run: {dry_run}")
        
        # Generate a fake txid
        import hashlib
        fake_txid = hashlib.sha256(f"{to}{subject}{content}{time.time()}".encode()).hexdigest()
        
        # Save the sent message
        save_sent_message(to, subject, content, fake_txid, dry_run)
        
        return {
            "success": True, 
            "txid": fake_txid,
            "message": "Message sent successfully!" if not dry_run else "Dry-run successful (no broadcast)"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@eel.expose
def get_wallet_balances():
    """Get wallet balances (simulated)"""
    # Simulate wallet balances
    evr_balances = {
        "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx": 1250000000, # 12.5 EVR
        "EcLDQHzh7GKGk1NQP3C5bCCCCCC4MESxZT": 890000000,  # 8.9 EVR
    }
    
    asset_balances = {
        "MAIL": {
            "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx": 1000000000, # 10 MAIL
        },
        "CHANNEL/TWITTER": {
            "EcLDQHzh7GKGk1NQP3C5bCCCCCC4MESxZT": 100000000, # 1 CHANNEL/TWITTER
        }
    }
    
    total_evr = sum(evr_balances.values()) / 1e8
    
    return {
        "total_evr": total_evr,
        "evr": {addr: amount / 1e8 for addr, amount in evr_balances.items()},
        "assets": {
            asset: {addr: amount / 1e8 for addr, amount in addr_map.items()}
            for asset, addr_map in asset_balances.items()
        }
    }

@eel.expose
def get_wallet_addresses():
    """Get wallet addresses (simulated)"""
    # Simulate addresses
    addresses = [
        {"address": "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx", "friendly_name": "Primary", "index": 0, "path": "m/44'/175'/0'/0/0"},
        {"address": "EcLDQHzh7GKGk1NQP3C5bCCCCCC4MESxZT", "friendly_name": "Savings", "index": 1, "path": "m/44'/175'/0'/0/1"},
        {"address": "EPyZEULEXGCiWyRdVwDMJFsQCY2qQxU8QP", "friendly_name": "address_2", "index": 2, "path": "m/44'/175'/0'/0/2"},
        {"address": "EdZGtMBnEiauvALrsd7Vtf6ARMWXPdgfJQ", "friendly_name": "address_3", "index": 3, "path": "m/44'/175'/0'/0/3"},
    ]
    return addresses

@eel.expose
def get_utxos():
    """Get UTXOs (simulated)"""
    utxos = [
        {
            "spent": False,
            "status": "✅ Confirmed",
            "address": "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx",
            "asset": "EVR",
            "amount": 12.5,
            "txid": "aef5d6ad1c8f1a4c4eebd0b0fe549c06fd8c5cd0d1b9e4c71c8e46b82e4aa102",
            "vout": 1,
            "confirmations": 15
        },
        {
            "spent": False,
            "status": "✅ Confirmed",
            "address": "EcLDQHzh7GKGk1NQP3C5bCCCCCC4MESxZT", 
            "asset": "EVR",
            "amount": 8.9,
            "txid": "bef5d6ad1c8f1a4c4eebd0b0fe549c06fd8c5cd0d1b9e4c71c8e46b82e4aa103",
            "vout": 0,
            "confirmations": 10
        },
        {
            "spent": False,
            "status": "✅ Confirmed",
            "address": "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx",
            "asset": "MAIL",
            "amount": 10.0,
            "txid": "cef5d6ad1c8f1a4c4eebd0b0fe549c06fd8c5cd0d1b9e4c71c8e46b82e4aa104",
            "vout": 1,
            "confirmations": 12
        }
    ]
    return utxos

@eel.expose
def add_log_entry(category, level, message, details=None):
    """Add a log entry"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    entry = {
        "category": category,
        "level": level,
        "timestamp": timestamp,
        "message": message,
        "details": details
    }
    
    LOG_ENTRIES.append(entry)
    print(f"[{category}] [{level}] {message}")
    return True

@eel.expose
def get_log_entries(level_filter="all", category_filter=None, text_filter=None):
    """Get log entries with optional filtering"""
    filtered_entries = LOG_ENTRIES.copy()
    
    # Apply level filter
    if level_filter != "all":
        level_order = ["debug", "info", "warning", "error", "critical"]
        level_index = level_order.index(level_filter)
        filtered_entries = [e for e in filtered_entries if level_order.index(e["level"]) >= level_index]
    
    # Apply category filter
    if category_filter:
        filtered_entries = [e for e in filtered_entries if e["category"] in category_filter]
    
    # Apply text filter
    if text_filter:
        filtered_entries = [e for e in filtered_entries if text_filter.lower() in e["message"].lower()]
        
    return filtered_entries

@eel.expose
def navigate_browser(url):
    """Simulate browser navigation"""
    import webbrowser
    if url.endswith('.evr'):
        # For demonstration purposes, just log the EVR domain lookup
        add_log_entry("BROWSER", "info", f"Looking up EVR domain: {url}")
        return {
            "success": True,
            "type": "evr_domain",
            "content": f"<html><body><h1>EVR Domain: {url}</h1><p>This is a simulated EVR domain page</p></body></html>"
        }
    else:
        # Open in system browser
        webbrowser.open(url)
        return {"success": True, "opened_in_system": True}

@eel.expose
def get_settings():
    """Get application settings"""
    settings = {
        "rpc_url": "https://rpc.evrmore.exchange",
        "max_addresses": 1000,
        "theme": "dark",
        "start_on_boot": False
    }
    return settings

@eel.expose
def save_settings(settings):
    """Save application settings"""
    print(f"Saving settings: {settings}")
    # In a real application, this would save to a config file
    return {"success": True}

# Start the daemon in a background thread
def start_daemon():
    """Simulate starting the EvrMail daemon"""
    add_log_entry("DAEMON", "info", "Starting EvrMail daemon...")
    time.sleep(1)
    add_log_entry("DAEMON", "info", "Connecting to Evrmore node...")
    time.sleep(1)
    add_log_entry("WALLET", "info", "Loading wallet...")
    time.sleep(0.5)
    add_log_entry("DAEMON", "info", "Daemon listening for transactions")
    add_log_entry("WALLET", "info", "Reloading known addresses")
    add_log_entry("CHAIN", "info", "Block processed with 5 transactions")

# Initialize application with some log entries
add_log_entry("APP", "info", "EvrMail application starting")

# Start daemon in background
threading.Thread(target=start_daemon, daemon=True).start()

# Start the Eel application
eel.start('index.html', size=(1080, 720))
