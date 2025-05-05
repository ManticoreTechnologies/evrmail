from .wif_to_privkey_hex import wif_to_privkey_hex
from .create_message_payload import create_message_payload
from .create_batch_payload import create_batch_payload
from .ipfs import add_to_ipfs
from .decrypt_message import decrypt_message
from .logger import (
    configure_logging, 
    get_logger,
    register_callback,
    app, gui, daemon, wallet, chain, network, debug_log,
    APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG,
    set_enabled_categories,
    set_colored_output,
    set_daemon_console_output
)

# Log entry storage - for use by the GUI
_log_entries = []

# Get logs function for the GUI
def get_logs():
    """Get the stored log entries for GUI display"""
    global _log_entries
    return _log_entries

# Log callback function to store logs for GUI display
def _store_log_entry(category, level_name, level_num, message, details=None):
    """Store log entries for retrieval by the GUI"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "level": level_name.lower(),
        "category": category,
        "message": message,
        "details": details
    }
    _log_entries.append(entry)
    # Keep log list to a reasonable size
    if len(_log_entries) > 1000:
        _log_entries.pop(0)

# Register the log callback for all categories
for category in [APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG]:
    register_callback(_store_log_entry, category)

__all__ = [
    "wif_to_privkey_hex",
    "create_message_payload",
    "create_batch_payload",
    "add_to_ipfs",
    "decrypt_message",
    # Logs and logging
    "get_logs",
    "configure_logging",
    "get_logger",
    "register_callback",
    "app", "gui", "daemon", "wallet", "chain", "network", "debug_log",
    "APP", "GUI", "DAEMON", "WALLET", "CHAIN", "NETWORK", "DEBUG",
    "set_enabled_categories",
    "set_colored_output",
    "set_daemon_console_output"
]