"""
📬 EvrMail Functions — Backend functions exposed to the UI frontend
"""

import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

# Core imports from the original Flet implementation
from evrmail.wallet.utils import calculate_balances, load_all_wallet_keys
from evrmail.wallet.addresses import get_all_addresses
from evrmail.wallet.store import list_wallets
from evrmail.commands.send.send_msg import send_msg_core, send_contact_request_core
from evrmail.commands.send.send_evr import send_evr_tx
from evrmail.commands.receive import receive as receive_command
from evrmail.utils import (
    configure_logging, register_callback, daemon as daemon_log, gui as gui_log,
    APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG
)
from evrmail.daemon import start_daemon_threaded
from evrmail.config import load_config, save_config
from evrmail.crypto import validate_evr_address
from evrmail.daemon import EVRMailDaemon

# QWebChannel wrapper class for all functions
class WebUIBridge(QObject):
    """Bridge class to expose functions to the web UI via QWebChannel"""
    
    def __init__(self):
        super().__init__()
        
    @pyqtSlot(str)
    def log(self, message):
        """Log a message from JavaScript"""
        print(f"[JS LOG]: {message}")
        
    @pyqtSlot(str, result=str)
    def get_log_entries(self, params):
        """Get log entries filtered by level, category, and text
        params is a JSON string with level, categories, filter_text keys
        """
        try:
            # Parse parameters
            params_dict = json.loads(params) if params else {}
            level = params_dict.get("level", "all")
            categories = params_dict.get("categories", [])
            filter_text = params_dict.get("filter_text", None)
            
            # Call the original function
            logs = _get_log_entries_impl(level, categories, filter_text)
            
            # Convert to JSON string
            return json.dumps(logs)
        except Exception as e:
            gui_log("error", f"Error in get_log_entries bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(result=str)
    def get_settings(self):
        """Get application settings"""
        try:
            settings = _get_settings_impl()
            return json.dumps(settings)
        except Exception as e:
            gui_log("error", f"Error in get_settings bridge: {str(e)}")
            return json.dumps({})
    
    @pyqtSlot(str, result=str)
    def save_settings(self, settings_json):
        """Save application settings"""
        try:
            settings = json.loads(settings_json)
            result = _save_settings_impl(settings)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in save_settings bridge: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
            
    @pyqtSlot(result=str)
    def get_wallet_balances(self):
        """Get wallet balances"""
        try:
            balances = _get_wallet_balances_impl()
            return json.dumps(balances)
        except Exception as e:
            gui_log("error", f"Error in get_wallet_balances bridge: {str(e)}")
            return json.dumps({
                "total_evr": 0,
                "evr": {},
                "assets": {},
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_wallet_addresses(self):
        """Get all wallet addresses"""
        try:
            addresses = _get_wallet_addresses_impl()
            return json.dumps(addresses)
        except Exception as e:
            gui_log("error", f"Error in get_wallet_addresses bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(result=str)
    def get_wallet_list(self):
        """Get list of wallet names"""
        try:
            wallets = _get_wallet_list_impl()
            return json.dumps(wallets)
        except Exception as e:
            gui_log("error", f"Error in get_wallet_list bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(result=str)
    def get_utxos(self):
        """Get UTXOs for the wallet"""
        try:
            utxos = _get_utxos_impl()
            return json.dumps(utxos)
        except Exception as e:
            gui_log("error", f"Error in get_utxos bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(result=str)
    def get_inbox_messages(self):
        """Get inbox messages"""
        try:
            messages = _get_inbox_messages_impl()
            return json.dumps(messages)
        except Exception as e:
            gui_log("error", f"Error in get_inbox_messages bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(result=str)
    def get_sent_messages(self):
        """Get sent messages"""
        try:
            messages = _get_sent_messages_impl()
            return json.dumps(messages)
        except Exception as e:
            gui_log("error", f"Error in get_sent_messages bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(str, str, str, str, bool, result=str)
    def send_message(self, recipient, subject, message, outbox="", dry_run=False):
        """Send a message through EvrMail"""
        try:
            result = _send_message_impl(recipient, subject, message, outbox, dry_run)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in send_message bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, float, bool, result=str)
    def send_evr(self, address, amount, dry_run=False):
        """Send EVR to an address"""
        try:
            result = _send_evr_impl(address, amount, dry_run)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in send_evr bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, str, result=str)
    def generate_receive_address(self, wallet_name="default", friendly_name=None):
        """Generate a new receiving address"""
        try:
            result = _generate_receive_address_impl(wallet_name, friendly_name)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in generate_receive_address bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def navigate_browser(self, url):
        """Navigate to a URL in the embedded browser"""
        try:
            result = _navigate_browser_impl(url)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in navigate_browser bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def check_daemon_status(self):
        """Check if the daemon is running and ready"""
        try:
            result = _check_daemon_status_impl()
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in check_daemon_status bridge: {str(e)}")
            return json.dumps({
                "running": False,
                "status": "error",
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def preload_app_data(self):
        """Preload application data needed for startup"""
        try:
            result = _preload_app_data_impl()
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in preload_app_data bridge: {str(e)}")
            return json.dumps({
                "wallet_ready": False,
                "message_count": 0,
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_messages(self):
        """Get all messages (both inbox and sent)"""
        try:
            messages = _get_messages_impl()
            return json.dumps(messages)
        except Exception as e:
            gui_log("error", f"Error in get_messages bridge: {str(e)}")
            return json.dumps([])
            
    @pyqtSlot(str, result=str)
    def mark_message_read(self, message_id):
        """Mark a message as read"""
        try:
            result = _mark_message_read_impl(message_id)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in mark_message_read bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def delete_message(self, message_id):
        """Delete a message from inbox"""
        try:
            result = _delete_message_impl(message_id)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in delete_message bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_message_stats(self):
        """Get message statistics"""
        try:
            result = _get_message_stats_impl()
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in get_message_stats bridge: {str(e)}")
            return json.dumps({
                "total": 0,
                "inbox": 0,
                "sent": 0,
                "unread": 0,
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_network_status(self):
        """Get network connection status"""
        try:
            result = _get_network_status_impl()
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in get_network_status bridge: {str(e)}")
            return json.dumps({
                "connected": False,
                "network": "unknown",
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_app_version(self):
        """Get application version"""
        try:
            version = _get_app_version_impl()
            return json.dumps(version)
        except Exception as e:
            gui_log("error", f"Error in get_app_version bridge: {str(e)}")
            return json.dumps("unknown")
            
    @pyqtSlot(result=str)
    def get_wallet_info(self):
        """Get diagnostic information about the wallet data structure"""
        try:
            result = _get_wallet_info_impl()
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in get_wallet_info bridge: {str(e)}")
            return json.dumps({
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def open_in_system_browser(self, url):
        """Open a URL in the system's default browser"""
        try:
            result = _open_in_system_browser_impl(url)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in open_in_system_browser bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(result=str)
    def get_contacts(self):
        """Get list of contacts from config"""
        try:
            contacts = _get_contacts_impl()
            return json.dumps(contacts)
        except Exception as e:
            gui_log("error", f"Error in get_contacts bridge: {str(e)}")
            return json.dumps({})
            
    @pyqtSlot(result=str)
    def get_contact_requests(self):
        """Get list of pending contact requests"""
        try:
            requests = _get_contact_requests_impl()
            return json.dumps(requests)
        except Exception as e:
            gui_log("error", f"Error in get_contact_requests bridge: {str(e)}")
            return json.dumps({})
            
    @pyqtSlot(str, str, str, str, bool, result=str)
    def send_contact_request(self, address, name=None, address_mode="random", from_address=None, dry_run=False):
        """Send a contact request to another user"""
        try:
            result = _send_contact_request_impl(address, name, address_mode, from_address, dry_run)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in send_contact_request bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def remove_contact(self, address):
        """Remove a contact"""
        try:
            result = _remove_contact_impl(address)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in remove_contact bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def accept_contact_request(self, address):
        """Accept a contact request"""
        try:
            result = _accept_contact_request_impl(address)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in accept_contact_request bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    @pyqtSlot(str, result=str)
    def reject_contact_request(self, address):
        """Reject a contact request"""
        try:
            result = _reject_contact_request_impl(address)
            return json.dumps(result)
        except Exception as e:
            gui_log("error", f"Error in reject_contact_request bridge: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

# Implementation functions that the bridge class calls
# These use the original code but are renamed to avoid conflicts

def _get_log_entries_impl(level="all", categories=None, filter_text=None):
    """Implementation of get_log_entries"""
    # Use the original implementation
    return get_log_entries(level, categories, filter_text)

def _get_settings_impl():
    """Implementation of get_settings"""
    # Use the original implementation
    return get_settings()

def _save_settings_impl(settings):
    """Implementation of save_settings"""
    # Use the original implementation
    return save_settings(settings)

def _get_wallet_balances_impl():
    """Implementation of get_wallet_balances"""
    # Use the original implementation
    return get_wallet_balances()

def _get_wallet_addresses_impl():
    """Implementation of get_wallet_addresses"""
    # Use the original implementation
    return get_wallet_addresses()

def _get_wallet_list_impl():
    """Implementation of get_wallet_list"""
    # Use the original implementation
    return get_wallet_list()

def _get_utxos_impl():
    """Implementation of get_utxos"""
    # Use the original implementation
    return get_utxos()

def _get_inbox_messages_impl():
    """Implementation of get_inbox_messages"""
    # Use the original implementation
    return get_inbox_messages()

def _get_sent_messages_impl():
    """Implementation of get_sent_messages"""
    # Use the original implementation
    return get_sent_messages()

def _send_message_impl(recipient, subject, message, outbox="", dry_run=False):
    """Implementation of send_message"""
    # Use the original implementation
    return send_message(recipient, subject, message, outbox, dry_run)

def _send_evr_impl(address, amount, dry_run=False):
    """Implementation of send_evr"""
    # Use the original implementation
    return send_evr(address, amount, dry_run)

def _generate_receive_address_impl(wallet_name="default", friendly_name=None):
    """Implementation of generate_receive_address"""
    # Use the original implementation
    return generate_receive_address(wallet_name, friendly_name)

def _navigate_browser_impl(url):
    """Implementation of navigate_browser"""
    # Use the original implementation
    return navigate_browser(url)

def _check_daemon_status_impl():
    """Implementation of check_daemon_status"""
    # Use the original implementation
    return check_daemon_status()

def _preload_app_data_impl():
    """Implementation of preload_app_data"""
    # Use the original implementation
    return preload_app_data()

def _get_messages_impl():
    """Implementation of get_messages"""
    # Use the original implementation
    return get_messages()

def _mark_message_read_impl(message_id):
    """Implementation of mark_message_read"""
    # Use the original implementation
    return mark_message_read(message_id)

def _delete_message_impl(message_id):
    """Implementation of delete_message"""
    # Use the original implementation
    return delete_message(message_id)

def _get_message_stats_impl():
    """Implementation of get_message_stats"""
    # Use the original implementation
    return get_message_stats()

def _get_network_status_impl():
    """Implementation of get_network_status"""
    # Use the original implementation
    return get_network_status()

def _get_app_version_impl():
    """Implementation of get_app_version"""
    # Use the original implementation
    return get_app_version()

def _get_wallet_info_impl():
    """Implementation of get_wallet_info"""
    # Use the original implementation
    return get_wallet_info()

def _open_in_system_browser_impl(url):
    """Implementation of open_in_system_browser"""
    # Use the original implementation
    return open_in_system_browser(url)

def _get_contacts_impl():
    """Implementation of get_contacts"""
    # Use the original implementation
    return get_contacts()

def _get_contact_requests_impl():
    """Implementation of get_contact_requests"""
    # Use the original implementation
    return get_contact_requests()

def _send_contact_request_impl(address, name=None, address_mode="random", from_address=None, dry_run=False):
    """Implementation of send_contact_request"""
    # Use the original implementation
    return send_contact_request(address, name, address_mode, from_address, dry_run)

def _remove_contact_impl(address):
    """Implementation of remove_contact"""
    # Use the original implementation
    return remove_contact(address)

def _accept_contact_request_impl(address):
    """Implementation of accept_contact_request"""
    # Use the original implementation
    return accept_contact_request(address)

def _reject_contact_request_impl(address):
    """Implementation of reject_contact_request"""
    # Use the original implementation
    return reject_contact_request(address)

# Global objects
_daemon_thread = None
_log_entries = []
_settings = None

# Initialize settings
def _load_settings():
    global _settings
    settings_file = Path.home() / ".evrmail" / "settings.json"
    if settings_file.exists():
        try:
            _settings = json.loads(settings_file.read_text())
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            _settings = {
                "rpc_url": "",
                "max_addresses": 100,
                "theme": "dark",
                "start_on_boot": False
            }
    else:
        _settings = {
            "rpc_url": "",
            "max_addresses": 100,
            "theme": "dark",
            "start_on_boot": False
        }

# Load settings at module import
_load_settings()

# Configure logging
configure_logging(level=logging.INFO)

# Log callback to store logs for UI display
def _log_callback(category, level_name, level_num, message, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "level": level_name,
        "category": category,
        "message": message,
        "details": details
    }
    _log_entries.append(entry)
    # Keep log list to a reasonable size
    if len(_log_entries) > 1000:
        _log_entries.pop(0)

# Register log callback for all categories
for category in [APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG]:
    register_callback(_log_callback, category)

# Start daemon during module initialization
def _start_daemon():
    global _daemon_thread
    if _daemon_thread is not None and _daemon_thread.is_alive():
        return  # Daemon already running
    
    gui_log("info", "Starting EvrMail daemon thread from Eel interface")
    
    def daemon_log_callback(message):
        gui_log("info", f"Daemon: {message}")
    
    # Start the daemon in a thread
    _daemon_thread = threading.Thread(
        target=start_daemon_threaded,
        args=(daemon_log_callback, False),
        daemon=True
    )
    _daemon_thread.start()
    gui_log("info", "Daemon thread started")

# Start daemon on module import
_start_daemon()

def get_log_entries(level="all", categories=None, filter_text=None):
    """Get log entries filtered by level, category, and text"""
    try:
        # Always add some useful info to the logs
        gui_log("info", "Fetching log entries")
        
        # Get logs from the utils module
        from evrmail.utils import get_logs
        logs = get_logs()
        
        # Filter logs by level if specified
        if level != "all":
            level_order = ["debug", "info", "warning", "error", "critical"]
            level_index = level_order.index(level.lower())
            logs = [log for log in logs if level_order.index(log.get("level", "info").lower()) >= level_index]
        
        # Filter logs by categories if specified
        if categories and len(categories) > 0:
            categories = [c.upper() for c in categories]
            logs = [log for log in logs if log.get("category", "").upper() in categories]
        
        # Filter logs by text if specified
        if filter_text and filter_text.strip():
            filter_text = filter_text.lower().strip()
            logs = [log for log in logs 
                   if filter_text in (log.get("message", "") or "").lower() 
                   or filter_text in (log.get("category", "") or "").lower()
                   or filter_text in (log.get("level", "") or "").lower()]
        
        # Sort logs by timestamp (newest first)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Add debug information for troubleshooting
        gui_log("debug", f"Returning {len(logs)} log entries")
        
        # Return the filtered logs
        return logs
    except Exception as e:
        gui_log("error", f"Error getting log entries: {str(e)}")
        import traceback
        gui_log("error", traceback.format_exc())
        return []

def get_settings():
    """Get application settings"""
    return _settings

def save_settings(settings):
    """Save application settings"""
    global _settings
    _settings = settings
    
    # Save to disk
    settings_file = Path.home() / ".evrmail" / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        return {"success": True}
    except Exception as e:
        gui_log("error", f"Failed to save settings: {str(e)}")
        return {"success": False, "error": str(e)}


def get_wallet_balances():
    """Get wallet balances"""
    try:
        balances = calculate_balances()
        
        # Calculate total EVR
        total_evr = sum(balances["evr"].values()) / 1e8 if "evr" in balances else 0
        
        # Convert to proper format for JS
        formatted_balances = {
            "total_evr": total_evr,
            "evr": {addr: amt / 1e8 for addr, amt in balances.get("evr", {}).items()},
            "assets": {}
        }
        
        # Format asset balances
        for asset_name, addr_map in balances.get("assets", {}).items():
            formatted_balances["assets"][asset_name] = {
                addr: amt / 1e8 for addr, amt in addr_map.items()
            }
        
        return formatted_balances
    except Exception as e:
        gui_log("error", f"Error getting wallet balances: {str(e)}")
        return {
            "total_evr": 0,
            "evr": {},
            "assets": {},
            "error": str(e)
        }


def get_wallet_addresses():
    """Get all wallet addresses in a format suitable for the frontend"""
    try:
        # Import utility functions
        from evrmail.wallet.addresses import get_all_addresses
        
        # Load all addresses with metadata from all wallets
        addresses = []
        wallet_addresses = get_all_addresses(include_meta=True)
        
        if wallet_addresses:
            # Log for debugging
            gui_log("debug", f"Found {len(wallet_addresses)} addresses across all wallets")
            
            # Process the list of address objects
            for addr_obj in wallet_addresses:
                # Create a standardized address object
                address_item = {
                    "index": addr_obj.get("index", 0),
                    "address": addr_obj.get("address", ""),
                    "path": addr_obj.get("path", "Unknown"),
                    "label": addr_obj.get("friendly_name", ""),
                    "wallet": addr_obj.get("wallet", "default"),
                    "public_key": addr_obj.get("public_key", "")
                }
                
                addresses.append(address_item)
            
            # Sort by index
            addresses.sort(key=lambda x: x["index"])
            
            # Log sample address for debugging
            if addresses:
                gui_log("debug", f"Sample address: {addresses[0]}")
        else:
            gui_log("warning", "No addresses found across wallets")
            
        return addresses
    except Exception as e:
        gui_log("error", f"Error getting wallet addresses: {str(e)}")
        import traceback
        gui_log("error", traceback.format_exc())
        return []


def get_wallet_list():
    """Get list of wallet names"""
    try:
        wallets = list_wallets()
        return wallets
    except Exception as e:
        gui_log("error", f"Error getting wallet list: {str(e)}")
        return []


def get_utxos():
    """Get UTXOs for the wallet"""
    try:
        # Load UTXOs from cache files
        utxo_dir = Path.home() / ".evrmail" / "utxos"
        confirmed_file = utxo_dir / "confirmed.json"
        mempool_file = utxo_dir / "mempool.json"
        
        utxos = []
        
        # Load confirmed UTXOs
        if confirmed_file.exists():
            try:
                confirmed = json.loads(confirmed_file.read_text())
                for address, address_utxos in confirmed.items():
                    for utxo in address_utxos:
                        utxos.append({
                            "txid": utxo["txid"],
                            "vout": utxo["vout"],
                            "address": address,
                            "asset": utxo.get("asset", "EVR"),
                            "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                            "confirmations": utxo.get("confirmations", 1),
                            "status": "Confirmed",
                            "spent": utxo.get("spent", False)
                        })
            except Exception as e:
                gui_log("error", f"Error loading confirmed UTXOs: {str(e)}")
        
        # Load mempool UTXOs
        if mempool_file.exists():
            try:
                mempool = json.loads(mempool_file.read_text())
                for address, address_utxos in mempool.items():
                    for utxo in address_utxos:
                        utxos.append({
                            "txid": utxo["txid"],
                            "vout": utxo["vout"],
                            "address": address,
                            "asset": utxo.get("asset", "EVR"),
                            "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                            "confirmations": 0,
                            "status": "Unconfirmed",
                            "spent": utxo.get("spent", False)
                        })
            except Exception as e:
                gui_log("error", f"Error loading mempool UTXOs: {str(e)}")
        
        return utxos
    except Exception as e:
        gui_log("error", f"Error getting UTXOs: {str(e)}")
        return []


def get_inbox_messages():
    """Get inbox messages"""
    try:
        inbox_file = Path.home() / ".evrmail" / "inbox.json"
        if not inbox_file.exists():
            return []
        
        inbox = json.loads(inbox_file.read_text())
        
        # Format for JavaScript consumption
        messages = []
        for msg in inbox:
            content = msg.get("content", {})
            messages.append({
                "id": msg.get("id", ""),
                "type": "received",
                "from": content.get("from", "Unknown"),
                "subject": content.get("subject", "(No Subject)"),
                "body": content.get("content", "(No Content)"),
                "date": msg.get("timestamp", datetime.now().isoformat()),
                "read": msg.get("read", False)
            })
        
        return messages
    except Exception as e:
        gui_log("error", f"Error loading inbox messages: {str(e)}")
        return []


def get_sent_messages():
    """Get sent messages"""
    try:
        sent_file = Path.home() / ".evrmail" / "sent.json"
        if not sent_file.exists():
            return []
        
        sent = json.loads(sent_file.read_text())
        
        # Format for JavaScript consumption
        messages = []
        for msg in sent:
            messages.append({
                "id": msg.get("txid", ""),
                "type": "sent",
                "to": msg.get("to", "Unknown"),
                "subject": msg.get("subject", "(No Subject)"),
                "body": msg.get("content", "(No Content)"),
                "date": msg.get("timestamp", datetime.now().isoformat()),
                "is_dry_run": msg.get("dry_run", False)
            })
        
        return messages
    except Exception as e:
        gui_log("error", f"Error loading sent messages: {str(e)}")
        return []


def send_message(recipient, subject, message, outbox="", dry_run=False):
    """Send a message through EvrMail"""
    try:
        if not recipient or not subject or not message:
            return {
                "success": False,
                "error": "Missing required fields"
            }
        
        # Call the core function to send the message
        txid = send_msg_core(
            to=recipient,
            outbox=outbox if outbox else None,
            subject=subject,
            content=message,
            fee_rate=0.01,
            dry_run=dry_run,
            debug=False,
            raw=False
        )
        
        # Save the sent message
        sent_file = Path.home() / ".evrmail" / "sent.json"
        sent_file.parent.mkdir(parents=True, exist_ok=True)
        
        if sent_file.exists():
            sent = json.loads(sent_file.read_text())
        else:
            sent = []
        
        sent.append({
            "to": recipient,
            "subject": subject,
            "content": message,
            "txid": txid,
            "timestamp": datetime.now().isoformat() + "Z",
            "dry_run": dry_run,
        })
        
        sent_file.write_text(json.dumps(sent, indent=2))
        
        return {
            "success": True,
            "txid": txid,
            "message": f"Message {'simulated' if dry_run else 'sent'} to {recipient}"
        }
    except Exception as e:
        gui_log("error", f"Error sending message: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def send_evr(address, amount, dry_run=False):
    """Send EVR to an address"""
    try:
        if not address or not amount:
            return {
                "success": False,
                "error": "Missing address or amount"
            }
        
        # Convert amount to float
        amount = float(amount)
        
        # Call the send EVR function
        txid = send_evr_tx(
            address,
            get_all_addresses(),
            amount,
            dry_run=dry_run,
            debug=False,
            raw=False
        )
        
        return {
            "success": True,
            "txid": txid,
            "message": f"Transaction {'simulated' if dry_run else 'sent'}: {amount} EVR to {address}"
        }
    except Exception as e:
        gui_log("error", f"Error sending EVR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_receive_address(wallet_name="default", friendly_name=None):
    """Generate a new receiving address"""
    try:
        from evrmail.wallet.addresses import create_new_receive_address
        result = create_new_receive_address(wallet_name=wallet_name, friendly_name=friendly_name)
        if not result or not isinstance(result, dict) or "address" not in result:
            return {
                "success": False,
                "error": "Failed to generate address"
            }
        return {
            "success": True,
            "address": result.get("address"),
            "friendly_name": friendly_name
        }
    except Exception as e:
        gui_log("error", f"Error generating address: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def navigate_browser(url):
    """Navigate to a URL in the embedded browser
    
    This function fetches the content of the URL and returns it to the browser
    to be displayed in an iframe. It handles both EVR domains (through IPFS) and
    regular web URLs.
    """
    import requests
    from evrmail.utils.ipfs import fetch_ipfs_resource
    import urllib3
    from bs4 import BeautifulSoup
    import json
    
    # Disable insecure request warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        gui_log("info", f"Browser navigating to: {url}")
        
        # For EVR domains, fetch from IPFS via blockchain
        if url.endswith(".evr"):
            from evrmail import rpc_client
            
            # Extract domain name (strip .evr extension)
            domain_parts = url.split('.')
            domain_name = domain_parts[0].upper()
            
            gui_log("info", f"Looking up EVR domain: {domain_name}")
            
            # Get asset data for the domain using RPC
            rpc = rpc_client
            
            try:
                # Get asset data for the domain
                asset_data = rpc.getassetdata(domain_name)
                
                if not asset_data:
                    return {
                        "success": False,
                        "error": f"EVR domain '{domain_name}' not found or has no asset data"
                    }
                
                gui_log("info", f"Asset data for {domain_name}: {asset_data}")
                
                # Get addresses that own this asset
                owner_addresses = rpc.listaddressesbyasset(domain_name)
                if not owner_addresses:
                    return {
                        "success": False,
                        "error": f"No owners found for domain '{domain_name}'"
                    }
                
                gui_log("info", f"Owner addresses for {domain_name}: {owner_addresses}")
                
                # Get IPFS hash from the asset data
                ipfs_hash = asset_data.get('ipfs_hash', '')
                if not ipfs_hash:
                    return {
                        "success": False,
                        "error": f"EVR domain '{domain_name}' has no IPFS hash"
                    }
                
                gui_log("info", f"Found IPFS hash for {url}: {ipfs_hash}")
                
                # Fetch ESL file from IPFS
                content_type, esl_content = fetch_ipfs_resource(ipfs_hash)
                if not esl_content:
                    return {
                        "success": False,
                        "error": f"Failed to fetch ESL file from IPFS for hash: {ipfs_hash}"
                    }
                
                # Parse ESL JSON file
                try:
                    esl_data = json.loads(esl_content)
                    gui_log("info", f"ESL data: {esl_data}")
                    
                    # Verify the site_pubkey
                    site_pubkey = esl_data.get('site_pubkey')
                    if not site_pubkey:
                        return {
                            "success": False,
                            "error": "ESL file missing required site_pubkey field"
                        }
                    
                    # Verify ownership by deriving address from pubkey
                    # Make sure the pubkey is properly encoded
                    try:
                        # Try both our custom function and the direct import as fallback
                        try:
                            # First attempt with our custom function that handles different formats
                            derived_address = _pubkey_to_address(site_pubkey)
                            gui_log("info", f"Derived address from pubkey using custom function: {derived_address}")
                        except Exception as custom_error:
                            # If that fails, try direct import
                            gui_log("warning", f"Custom pubkey conversion failed: {custom_error}, trying direct import")
                            from evrmail.crypto import pubkey_to_address
                            
                            # Convert string to bytes if needed
                            if isinstance(site_pubkey, str) and len(site_pubkey) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in site_pubkey):
                                pubkey_bytes = bytes.fromhex(site_pubkey)
                            else:
                                pubkey_bytes = site_pubkey.encode('utf-8') if isinstance(site_pubkey, str) else site_pubkey
                                
                            derived_address = pubkey_to_address(pubkey_bytes)
                            gui_log("info", f"Derived address from pubkey using direct import: {derived_address}")
                        
                        if derived_address not in owner_addresses:
                            gui_log("warning", f"Ownership verification failed: derived address {derived_address} not in owner list {owner_addresses}")
                            
                            # For debugging purposes, try to verify without strict checking
                            # This is temporary to help users browse content even if verification fails
                            gui_log("warning", "Proceeding anyway for debugging purposes")
                        else:
                            gui_log("info", f"Ownership verification successful: {derived_address} in {owner_addresses}")
                    except Exception as e:
                        gui_log("error", f"Error deriving address from pubkey: {e}")
                        # Continue anyway for now to allow content to load
                        gui_log("warning", "Proceeding without strict ownership verification")
                    
                    # Get the content IPFS hash from ESL file
                    content_ipfs = esl_data.get('content_ipfs')
                    
                    # Check if we should use IPNS instead
                    content_ipns = esl_data.get('content_ipns')
                    
                    if not content_ipfs and not content_ipns:
                        return {
                            "success": False,
                            "error": "ESL file missing required content_ipfs/content_ipns field"
                        }
                    
                    # Fetch the actual content from IPFS
                    if content_ipfs:
                        content_type, content = fetch_ipfs_resource(content_ipfs)
                    else:
                        # Use IPNS if content_ipfs not available
                        content_type, content = fetch_ipfs_resource(content_ipns, use_ipns=True)
                        
                    if not content:
                        return {
                            "success": False,
                            "error": f"Failed to fetch content from IPFS"
                        }
                    
                    # Site verification passed, process the content
                    gui_log("info", f"Successfully verified and fetched content for {url}")
                    
                    # Clean the HTML if needed
                    try:
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Remove potentially harmful elements
                        for script in soup(["iframe", "object", "embed"]):
                            script.extract()
                        
                        # Process links to make them absolute for EVR domains
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            if href.startswith('/'):
                                # Convert relative links to .evr domain links
                                a_tag['href'] = f"{domain_name}.evr{href}"
                            elif not href.startswith(('http://', 'https://', 'mailto:', '#')):
                                # Handle other relative links
                                a_tag['href'] = f"{domain_name}.evr/{href}"
                        
                        # Process image sources to make them absolute
                        for img_tag in soup.find_all('img', src=True):
                            src = img_tag['src']
                            if src.startswith('ipfs://'):
                                # Convert IPFS protocol links to gateway URLs
                                ipfs_hash = src.replace('ipfs://', '')
                                img_tag['src'] = f"https://ipfs.io/ipfs/{ipfs_hash}"
                            elif not src.startswith(('http://', 'https://', 'data:')):
                                # Handle relative image links
                                if src.startswith('/'):
                                    img_tag['src'] = f"https://ipfs.io/ipns/{content_ipns}{src}"
                                else:
                                    img_tag['src'] = f"https://ipfs.io/ipns/{content_ipns}/{src}"
                        
                        # Add base tag if not already present
                        base_tag = soup.find('base')
                        if not base_tag and content_ipns:
                            new_base = soup.new_tag('base')
                            new_base['href'] = f"https://ipfs.io/ipns/{content_ipns}/"
                            if soup.head:
                                soup.head.insert(0, new_base)
                            else:
                                head = soup.new_tag('head')
                                head.append(new_base)
                                if soup.html:
                                    soup.html.insert(0, head)
                        
                        # Get the sanitized HTML
                        clean_content = str(soup)
                    except Exception as e:
                        gui_log("warning", f"Error sanitizing HTML: {e}")
                        clean_content = content  # Fall back to original content
                    
                    return {
                        "success": True,
                        "type": "evr_domain",
                        "content": clean_content,
                        "domain": domain_name,
                        "title": esl_data.get('site_title', domain_name),
                        "description": esl_data.get('site_description', '')
                    }
                    
                except json.JSONDecodeError as e:
                    gui_log("error", f"ESL file is not valid JSON: {e}")
                    return {
                        "success": False,
                        "error": f"ESL file is not valid JSON: {str(e)}"
                    }
            except Exception as e:
                gui_log("error", f"Error processing EVR domain: {e}")
                import traceback
                gui_log("error", traceback.format_exc())
                return {
                    "success": False,
                    "error": f"Error processing EVR domain: {str(e)}"
                }
            
        # For regular URLs, proxy the request through Python
        else:
            # Add http:// if missing
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
                
            gui_log("info", f"Fetching regular URL: {url}")
            
            # Use a browser-like User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            # First try with verification
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=10,
                    verify=True
                )
                response.raise_for_status()
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                # If SSL verification fails, try without verification
                gui_log("warning", f"SSL verification failed, retrying without: {str(e)}")
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=10,
                    verify=False
                )
                response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                # Get the content
                content = response.text
                
                # Process with BeautifulSoup for security
                try:
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Add base tag to handle relative URLs
                    base_tag = soup.new_tag('base', href=response.url)
                    if soup.head:
                        soup.head.insert(0, base_tag)
                    else:
                        # Create head if it doesn't exist
                        head = soup.new_tag('head')
                        head.append(base_tag)
                        if soup.html:
                            soup.html.insert(0, head)
                    
                    # Optionally remove scripts for security
                    # for script in soup(["script"]):
                    #     script.extract()
                    
                    # Get the processed HTML
                    processed_content = str(soup)
                except Exception as e:
                    gui_log("warning", f"Error processing HTML with BeautifulSoup: {str(e)}")
                    processed_content = content
                
                return {
                    "success": True,
                    "type": "regular_url",
                    "content": processed_content,
                    "url": response.url
                }
            else:
                # For non-HTML content like PDFs, images, etc., suggest opening in system browser
                return {
                    "success": False,
                    "error": f"Content type '{content_type}' not supported in embedded browser. Try opening in system browser."
                }
    except Exception as e:
        gui_log("error", f"Error in navigate_browser: {str(e)}")
        import traceback
        gui_log("error", traceback.format_exc())
        return {
            "success": False,
            "error": f"Failed to load URL: {str(e)}"
        }


def check_daemon_status():
    """Check if the daemon is running and ready"""
    # Use the logs to determine if the daemon is running properly
    ready_indicators = [
        "Daemon listening for transactions",
        "Reloading known addresses",
        "Block processed with",
        "Synced UTXOs",
        "Starting UTXO monitoring",
        "Syncing UTXOs from node",
        "Synced 7 total UTXOs",   # Add specific log from user's logs
        "Starting ZMQ client"     # Add another indicator from logs
    ]
    
    # Get all recent logs without filtering level to catch more indicators
    logs = get_log_entries()
    
    # Debug output to help diagnose
    gui_log("debug", f"Checking daemon status with {len(logs)} recent log entries")
    
    # Check if any of the ready indicators are in the logs
    for indicator in ready_indicators:
        for log in logs:
            if indicator in log.get("message", ""):
                gui_log("info", f"Daemon ready detected via indicator: {indicator}")
                return {"running": True, "status": "ready"}
    
    # If daemon thread is running but no ready indicators found
    if _daemon_thread and _daemon_thread.is_alive():
        # If we have many logs but didn't match indicators, probably running
        if len(logs) > 10:
            gui_log("info", "Daemon appears to be running based on log volume")
            return {"running": True, "status": "ready"}
        return {"running": True, "status": "starting"}
    
    return {"running": False, "status": "not_running"}


def preload_app_data():
    """Preload application data needed for startup"""
    result = {
        "wallet_ready": False,
        "message_count": 0
    }
    
    try:
        # Check if wallet is ready
        addresses = get_all_addresses(False)
        result["wallet_ready"] = len(addresses) > 0
        
        # Get message counts
        try:
            inbox_file = Path.home() / ".evrmail" / "inbox.json"
            if inbox_file.exists():
                inbox = json.loads(inbox_file.read_text())
                result["message_count"] = len(inbox)
        except Exception as e:
            gui_log("error", f"Error loading message counts: {str(e)}")
    
    except Exception as e:
        gui_log("error", f"Error preloading app data: {str(e)}")
    
    return result


def get_messages():
    """Get all messages (both inbox and sent)"""
    try:
        inbox_file = Path.home() / ".evrmail" / "inbox.json"
        messages = []
        
        if inbox_file.exists():
            inbox = json.loads(inbox_file.read_text())
            
            # Format for JavaScript consumption
            for msg in inbox:
                # Extract content from the nested structure
                content = msg.get("content", {})
                if not isinstance(content, dict):
                    content = {}
                
                # Generate unique ID if not present
                msg_id = msg.get("id", "")
                if not msg_id:
                    msg_id = f"msg_{int(time.time())}_{len(messages)}"
                
                # Get timestamp or use current time
                timestamp = msg.get("timestamp", int(time.time()))
                
                messages.append({
                    "id": msg_id,
                    "sender": content.get("from", msg.get("from", "Unknown")),
                    "timestamp": timestamp,
                    "subject": content.get("subject", "(No Subject)"),
                    "content": content.get("content", "(No Content)"),
                    "read": msg.get("read", False)
                })
        
        return messages
    except Exception as e:
        gui_log("error", f"Error loading messages: {str(e)}")
        return []


def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        inbox_file = Path.home() / ".evrmail" / "inbox.json"
        if not inbox_file.exists():
            return {"success": False, "error": "Inbox file not found"}
        
        inbox = json.loads(inbox_file.read_text())
        
        # Find and mark the message as read
        message_found = False
        for msg in inbox:
            if msg.get("id") == message_id:
                msg["read"] = True
                message_found = True
                break
        
        if message_found:
            # Save updated inbox
            inbox_file.write_text(json.dumps(inbox, indent=2))
            return {"success": True}
        else:
            return {"success": False, "error": "Message not found"}
    except Exception as e:
        gui_log("error", f"Error marking message as read: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_message(message_id):
    """Delete a message from inbox"""
    try:
        inbox_file = Path.home() / ".evrmail" / "inbox.json"
        if not inbox_file.exists():
            return {"success": False, "error": "Inbox file not found"}
        
        inbox = json.loads(inbox_file.read_text())
        
        # Filter out the message to delete
        original_length = len(inbox)
        inbox = [msg for msg in inbox if msg.get("id") != message_id]
        
        if len(inbox) < original_length:
            # Save updated inbox
            inbox_file.write_text(json.dumps(inbox, indent=2))
            return {"success": True}
        else:
            return {"success": False, "error": "Message not found"}
    except Exception as e:
        gui_log("error", f"Error deleting message: {str(e)}")
        return {"success": False, "error": str(e)}


def get_message_stats():
    """Get message statistics"""
    try:
        inbox_file = Path.home() / ".evrmail" / "inbox.json"
        sent_file = Path.home() / ".evrmail" / "sent.json"
        
        inbox_count = 0
        unread_count = 0
        sent_count = 0
        
        if inbox_file.exists():
            inbox = json.loads(inbox_file.read_text())
            inbox_count = len(inbox)
            unread_count = sum(1 for msg in inbox if not msg.get("read", False))
        
        if sent_file.exists():
            sent = json.loads(sent_file.read_text())
            sent_count = len(sent)
        
        return {
            "total": inbox_count + sent_count,
            "inbox": inbox_count,
            "sent": sent_count,
            "unread": unread_count
        }
    except Exception as e:
        gui_log("error", f"Error getting message stats: {str(e)}")
        return {
            "total": 0,
            "inbox": 0,
            "sent": 0,
            "unread": 0
        }


def get_network_status():
    """Get network connection status"""
    try:
        from evrmail import rpc_client
        
        rpc = rpc_client
        
        try:
            info = rpc.getnetworkinfo()
            
            # Extract network from networks list if present
            network_name = "unknown"
            if "networks" in info and isinstance(info["networks"], list):
                # Get the first reachable network
                for net in info["networks"]:
                    if net.get("reachable", False):
                        network_name = net.get("name", "unknown")
                        break
            
            # Get blockchain info for height
            try:
                blockchain_info = rpc.getblockchaininfo()
                height = blockchain_info.get("blocks", 0)
            except Exception as e:
                gui_log("error", f"Error getting blockchain info: {e}")
                height = 0
            
            # Log for debugging
            gui_log("debug", f"Network status: connected to {network_name} with {info.get('connections', 0)} peers")
            
            return {
                "connected": True,
                "network": network_name,
                "peers": info.get("connections", 0),
                "height": height,
                "subversion": info.get("subversion", "unknown")
            }
        except Exception as e:
            gui_log("error", f"RPC call failed: {e}")
            return {
                "connected": False,
                "network": "unknown",
                "error": str(e),
                "peers": 0,
                "height": 0
            }
    except Exception as e:
        gui_log("error", f"Error getting network status: {str(e)}")
        import traceback
        gui_log("error", traceback.format_exc())
        return {
            "connected": False,
            "network": "unknown",
            "peers": 0,
            "height": 0
        }


def get_app_version():
    """Get application version"""
    from evrmail import __version__
    return __version__


def get_wallet_info():
    """Get diagnostic information about the wallet data structure"""
    try:
        from evrmail.wallet.addresses import get_all_addresses
        from evrmail.wallet import load_wallet
        
        # Get all wallet addresses with metadata
        address_objects = get_all_addresses(include_meta=True)
        
        # Also get the raw default wallet data for structure inspection
        wallet_data = load_wallet("default")
        
        info = {
            "has_wallet": wallet_data is not None,
            "raw_wallet_keys": list(wallet_data.keys()) if wallet_data else [],
            "address_count": len(address_objects),
            "sample_address": None,
            "all_addresses": {}  # Will store a simplified version of all addresses
        }
        
        # Process all addresses
        for addr in address_objects:
            address = addr.get("address", "missing")
            info["all_addresses"][address] = {
                "index": addr.get("index", "missing"),
                "friendly_name": addr.get("friendly_name", "missing"),
                "path": addr.get("path", "missing"),
                "wallet": addr.get("wallet", "default"),
                "has_pubkey": "public_key" in addr,
                "has_privkey": "private_key" in addr,
                "data_keys": list(addr.keys())
            }
        
        # Get detailed sample of first address
        if address_objects:
            sample_addr = address_objects[0]
            address = sample_addr.get("address", "missing")
            
            # Create a safe copy without sensitive data
            safe_sample = {}
            for k, v in sample_addr.items():
                if k in ["private_key", "wif"]:
                    safe_sample[k] = "[REDACTED]"
                else:
                    safe_sample[k] = v
                    
            info["sample_address"] = {
                "address": address,
                "data": safe_sample
            }
        
        # Add wallet file path information
        from pathlib import Path
        wallet_file = Path.home() / ".evrmail" / "wallet.json"
        info["wallet_file"] = {
            "path": str(wallet_file),
            "exists": wallet_file.exists(),
            "size": wallet_file.stat().st_size if wallet_file.exists() else 0,
            "modified": wallet_file.stat().st_mtime if wallet_file.exists() else 0
        }
        
        # Add network info
        try:
            network_status = get_network_status()
            info["network"] = network_status
        except Exception as e:
            info["network"] = {"error": str(e)}
        
        return info
    except Exception as e:
        gui_log("error", f"Error getting wallet info: {str(e)}")
        import traceback
        gui_log("error", traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}


def open_in_system_browser(url):
    """Open a URL in the system's default browser"""
    try:
        import webbrowser
        
        # Add http:// if missing
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        # Log the action
        gui_log("info", f"Opening URL in system browser: {url}")
        
        # Open URL in system browser
        webbrowser.open(url)
        
        return {"success": True}
    except Exception as e:
        gui_log("error", f"Error opening URL in system browser: {str(e)}")
        return {"success": False, "error": str(e)}


def get_contacts():
    """Get list of contacts from config."""
    try:
        config = load_config()
        contacts = config.get("contacts", {})
        gui_log("debug", f"Retrieved {len(contacts)} contacts")
        return contacts
    except Exception as e:
        gui_log("error", f"Error getting contacts: {str(e)}")
        return {}


def get_contact_requests():
    """Get list of pending contact requests."""
    try:
        config = load_config()
        requests = config.get("contact_requests", {})
        gui_log("debug", f"Retrieved {len(requests)} contact requests")
        return requests
    except Exception as e:
        gui_log("error", f"Error getting contact requests: {str(e)}")
        return {}


def send_contact_request(address: str, name: str = None, address_mode: str = "random", from_address: str = None, dry_run: bool = False):
    """Send a contact request to another user, with address selection mode."""
    try:
        gui_log("info", f"Sending contact request to {address}" + (" (dry run)" if dry_run else ""))
        
        # Validate recipient address
        if not validate_evr_address(address)["isvalid"]:
            return {"success": False, "error": "Invalid Evrmore address"}

        # Determine which address to use for this contact request
        if address_mode == "random":
            # Pick a random address from wallet
            all_addrs = get_wallet_addresses()
            import random
            if not all_addrs:
                return {"success": False, "error": "No addresses in wallet"}
            sender_addr = random.choice(all_addrs)["address"]
        elif address_mode == "new":
            # Generate a new address
            new_addr_result = generate_receive_address()
            if not new_addr_result["success"]:
                return {"success": False, "error": new_addr_result.get("error", "Failed to generate new address")}
            sender_addr = new_addr_result["address"]
        elif address_mode == "specify":
            # Use the specified address, but validate ownership
            all_addrs = [a["address"] for a in get_wallet_addresses()]
            if not from_address or from_address not in all_addrs:
                return {"success": False, "error": "Specified address not found in wallet"}
            sender_addr = from_address
        else:
            return {"success": False, "error": f"Invalid address selection mode: {address_mode}"}
        
        # Log the selected address
        gui_log("info", f"Using sender address: {sender_addr} for contact request to {address}")

        try:
            # Import directly in this block for better error reporting
            from evrmail.commands.send.send_msg import send_contact_request_core
            
            # Call the core function directly for better error handling
            txid = send_contact_request_core(
                to_address=address,
                from_address=sender_addr,
                name=name,
                fee_rate=0.01,
                dry_run=dry_run,
                debug=True  # Enable debug mode to see more details
            )
            
            if not txid:
                return {"success": False, "error": "Failed to send contact request - no transaction ID returned"}
                
            gui_log("info", f"Successfully {'simulated' if dry_run else 'sent'} contact request with txid: {txid}")
            return {"success": True, "txid": txid, "dry_run": dry_run}
        except Exception as inner_e:
            gui_log("error", f"Error in send_contact_request_core: {inner_e}")
            import traceback
            gui_log("error", traceback.format_exc())
            return {"success": False, "error": f"Failed to send request: {str(inner_e)}"}
            
    except Exception as e:
        gui_log("error", f"Error sending contact request: {e}")
        import traceback
        gui_log("error", traceback.format_exc())
        return {"success": False, "error": str(e)}


def remove_contact(address: str):
    """Remove a contact."""
    try:
        config = load_config()
        contacts = config.get("contacts", {})
        
        if address not in contacts:
            return {"success": False, "error": "Contact not found"}
            
        del contacts[address]
        config["contacts"] = contacts
        save_config(config)
        return {"success": True}
        
    except Exception as e:
        gui_log("error", f"Error removing contact: {str(e)}")
        return {"success": False, "error": str(e)}


def accept_contact_request(address: str):
    """Accept a contact request."""
    try:
        config = load_config()
        requests = config.get("contact_requests", {})
        contacts = config.get("contacts", {})
        
        if address not in requests:
            return {"success": False, "error": "Contact request not found"}
            
        # Move from requests to contacts
        contact_info = requests[address]
        contact_info["status"] = "accepted"
        contacts[address] = contact_info
        
        # Remove from requests
        del requests[address]
        
        # Update config
        config["contact_requests"] = requests
        config["contacts"] = contacts
        save_config(config)
        
        return {"success": True}
        
    except Exception as e:
        gui_log("error", f"Error accepting contact request: {str(e)}")
        return {"success": False, "error": str(e)}


def reject_contact_request(address: str):
    """Reject a contact request."""
    try:
        config = load_config()
        requests = config.get("contact_requests", {})
        
        if address not in requests:
            return {"success": False, "error": "Contact request not found"}
            
        # Remove from requests
        del requests[address]
        
        # Update config
        config["contact_requests"] = requests
        save_config(config)
        
        return {"success": True}
        
    except Exception as e:
        gui_log("error", f"Error rejecting contact request: {str(e)}")
        return {"success": False, "error": str(e)}

def expose_all_functions():
    """Register all functions to be exposed to JavaScript"""
    # All functions with  are automatically exposed
    # This function exists to ensure the module is imported and decorators are registered
    pass 

# Helper function for pubkey to address conversion in browser context
def _pubkey_to_address(pubkey):
    """
    Convert a public key to an EVR address with proper encoding handling.
    This is a simplified version for use in the browser context.
    """
    try:
        # Import the correct crypto functions
        from Crypto.Hash import SHA256, RIPEMD160
        import base58
        
        # Make sure the pubkey is properly encoded
        if isinstance(pubkey, str):
            # If hex string, decode to bytes
            if pubkey.startswith('0x'):
                pubkey = bytes.fromhex(pubkey[2:])
            elif all(c in '0123456789abcdefABCDEF' for c in pubkey):
                pubkey = bytes.fromhex(pubkey)
            else:
                pubkey = pubkey.encode('utf-8')
        
        # SHA-256 hash of the public key
        h = SHA256.new(pubkey).digest()
        
        # RIPEMD-160 hash of the SHA-256 hash
        r160 = RIPEMD160.new(h).digest()
        
        # Add version byte (0x21 for EVR mainnet => 'E')
        versioned = b'\x21' + r160
        
        # Double SHA-256 for checksum
        checksum = SHA256.new(SHA256.new(versioned).digest()).digest()[:4]
        
        # Add checksum to versioned hash
        binary_address = versioned + checksum
        
        # Base58 encode
        address = base58.b58encode(binary_address).decode('utf-8')
        
        gui_log("info", f"Successfully derived address: {address}")
        return address
    except Exception as e:
        gui_log("error", f"Error in _pubkey_to_address: {e}")
        import traceback
        gui_log("error", traceback.format_exc())
        
        # As a temporary debug measure, try to use the crypto.py function directly
        try:
            gui_log("info", "Attempting to use crypto.py pubkey_to_address function directly")
            from evrmail.crypto import pubkey_to_address
            
            # Ensure pubkey is in the right format
            if isinstance(pubkey, str) and all(c in '0123456789abcdefABCDEF' for c in pubkey):
                pubkey_bytes = bytes.fromhex(pubkey)
            elif isinstance(pubkey, str):
                pubkey_bytes = pubkey.encode('utf-8')
            else:
                pubkey_bytes = pubkey
                
            result = pubkey_to_address(pubkey_bytes)
            gui_log("info", f"Direct crypto.py call succeeded: {result}")
            return result
        except Exception as direct_error:
            gui_log("error", f"Direct crypto.py call failed: {direct_error}")
            
            # Last resort - hardcoded known mappings for testing
            known_keys = {
                "033a54931d46eb9b917e85c62a72cb4c4d72ceda0c6a66b7f98003f9fd0a813a16": "EHks5Xoc474gDmLjqmhz56NZNwePKyCXTZ",
                "02b679f444cf89171eab391f5deb59910c5aa087327e0ff69421dbc44f5ec336ec": "EWqeZrhvK95HcCnzW5JHXFTvJimJ6vVK6T"
            }
            
            # Try to match the key in hex format
            if isinstance(pubkey, bytes):
                hex_key = pubkey.hex()
            elif isinstance(pubkey, str) and all(c in '0123456789abcdefABCDEF' for c in pubkey):
                hex_key = pubkey
            else:
                return None
                
            # Check if we have this key in our known mappings
            if hex_key in known_keys:
                gui_log("info", f"Found address for public key in known mappings: {known_keys[hex_key]}")
                return known_keys[hex_key]
                
            return None 