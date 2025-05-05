import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
from typing import Callable, Optional, Dict, List, Set

# Constants for log categories
APP = "app"        # General application logs
GUI = "gui"        # GUI-related logs
DAEMON = "daemon"  # Daemon operation logs
WALLET = "wallet"  # Wallet/key operations
CHAIN = "chain"    # Blockchain data (transactions, blocks, etc)
NETWORK = "net"    # Network operations (RPC, ZMQ)
DEBUG = "debug"    # Debug information

# Log output styles
STYLES = {
    APP: "\033[0;36m",      # Cyan
    GUI: "\033[0;35m",      # Magenta
    DAEMON: "\033[0;33m",   # Yellow
    WALLET: "\033[0;32m",   # Green
    CHAIN: "\033[1;34m",    # Blue
    NETWORK: "\033[0;37m",  # White
    DEBUG: "\033[0;90m",    # Gray
    "reset": "\033[0m",     # Reset
    "error": "\033[1;31m",  # Red (bold)
    "warning": "\033[0;33m" # Yellow
}

# Log level mapping
LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# Global state
_log_callbacks: Dict[str, List[Callable]] = {}
_enabled_categories: Set[str] = {APP, GUI, DAEMON, WALLET, CHAIN, NETWORK}
_colored_output = True
_log_level = logging.INFO
_daemon_console_output = True

# Configure basic logging
def configure_logging(
    log_dir: str = None,
    level: int = logging.INFO,
    colored: bool = True,
    categories: Set[str] = None,
    daemon_to_console: bool = True
):
    """Configure the logging system with file and console outputs"""
    global _colored_output, _log_level, _enabled_categories, _daemon_console_output
    
    # Store settings
    _colored_output = colored
    _log_level = level
    if categories:
        _enabled_categories = categories
    _daemon_console_output = daemon_to_console
    
    # Set up log directory
    if not log_dir:
        log_dir = Path.home() / ".evrmail" / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create a formatter with timestamps
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    # Add console handler
    console_handler = ColorizedHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Add file handlers for each category
    for category in [APP, GUI, DAEMON, WALLET, CHAIN, NETWORK]:
        # Main log file
        main_log_file = log_dir / f"evrmail_{category}.log"
        file_handler = logging.FileHandler(main_log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CategoryFilter(category))
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    # Add a combined log file for all logs
    all_log_file = log_dir / "evrmail.log"
    all_file_handler = logging.FileHandler(all_log_file)
    all_file_handler.setFormatter(formatter)
    all_file_handler.setLevel(level)
    root_logger.addHandler(all_file_handler)
    
    # Add error log file
    error_log_file = log_dir / "evrmail_errors.log"
    error_file_handler = logging.FileHandler(error_log_file)
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)
    
    return log_dir

# Custom filter to only include logs from a specific category
class CategoryFilter(logging.Filter):
    def __init__(self, category):
        super().__init__()
        self.category = category
        
    def filter(self, record):
        if not hasattr(record, 'category'):
            return False
        return record.category == self.category

# Custom handler for colorized output
class ColorizedHandler(logging.StreamHandler):
    def emit(self, record):
        global _colored_output, _enabled_categories, _daemon_console_output
        
        # Check if this message should be shown based on category
        if hasattr(record, 'category'):
            category = record.category
            if category not in _enabled_categories:
                return
                
            # Check if daemon logs should be shown on console
            if not _daemon_console_output and category in [DAEMON, CHAIN, NETWORK]:
                return
        
        # Colorize if enabled
        if _colored_output and hasattr(record, 'category'):
            category = record.category
            category_color = STYLES.get(category, "")
            level_color = ""
            
            if record.levelno >= logging.ERROR:
                level_color = STYLES["error"]
            elif record.levelno >= logging.WARNING:
                level_color = STYLES["warning"]
                
            if category_color:
                record.msg = f"{category_color}[{category}]{STYLES['reset']} {level_color}{record.msg}{STYLES['reset']}"
        
        super().emit(record)

# Register a callback for log events
def register_callback(callback: Callable[[str, str, int, str, dict], None], category: str = None) -> Callable:
    """
    Register a callback for log events.
    
    Args:
        callback: Function that takes (category, level_name, level, message, details=None)
        category: Specific category to subscribe to (or None for all)
        
    Returns:
        Unsubscribe function
    """
    global _log_callbacks
    
    # Create a key for this subscription
    key = category if category else "all"
    
    if key not in _log_callbacks:
        _log_callbacks[key] = []
    
    _log_callbacks[key].append(callback)
    
    # Return an unsubscribe function
    def unsubscribe():
        if key in _log_callbacks and callback in _log_callbacks[key]:
            _log_callbacks[key].remove(callback)
    
    return unsubscribe

# Set enabled categories
def set_enabled_categories(categories: Set[str]):
    """Set which log categories are enabled"""
    global _enabled_categories
    _enabled_categories = categories

# Enable/disable colored output
def set_colored_output(enabled: bool):
    """Enable or disable colorized console output"""
    global _colored_output
    _colored_output = enabled

# Set daemon console output
def set_daemon_console_output(enabled: bool):
    """Enable or disable daemon logs in console"""
    global _daemon_console_output
    _daemon_console_output = enabled

# Get a logger for a specific category
def get_logger(category: str):
    """Get a logger for a specific category"""
    logger = logging.getLogger(f"evrmail.{category}")
    
    # Define wrapper methods to include category
    def _log(level, msg, *args, **kwargs):
        if args:
            msg = msg % args
        record = logging.LogRecord(
            name=logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=kwargs.get('exc_info'),
        )
        record.category = category
        
        # Extract details if provided
        details = kwargs.get('details', None)
        
        # Call callbacks
        if _log_callbacks:
            level_name = logging.getLevelName(level).lower()
            
            # Call category-specific callbacks
            if category in _log_callbacks:
                for callback in _log_callbacks[category]:
                    try:
                        callback(category, level_name, level, msg, details)
                    except Exception as e:
                        print(f"Error in log callback: {e}")
            
            # Call general callbacks
            if "all" in _log_callbacks:
                for callback in _log_callbacks["all"]:
                    try:
                        callback(category, level_name, level, msg, details)
                    except Exception as e:
                        print(f"Error in log callback: {e}")
        
        logger.handle(record)
    
    # Replace logger methods with our custom ones
    logger.debug = lambda msg, *args, **kwargs: _log(logging.DEBUG, msg, *args, **kwargs)
    logger.info = lambda msg, *args, **kwargs: _log(logging.INFO, msg, *args, **kwargs)
    logger.warning = lambda msg, *args, **kwargs: _log(logging.WARNING, msg, *args, **kwargs)
    logger.error = lambda msg, *args, **kwargs: _log(logging.ERROR, msg, *args, **kwargs)
    logger.critical = lambda msg, *args, **kwargs: _log(logging.CRITICAL, msg, *args, **kwargs)
    
    return logger

# Shortcut functions for each category
def app(level: str, msg: str, *args, **kwargs):
    """Log an application message"""
    _log_with_category(APP, level, msg, *args, **kwargs)

def gui(level: str, msg: str, *args, **kwargs):
    """Log a GUI message"""
    _log_with_category(GUI, level, msg, *args, **kwargs)

def daemon(level: str, msg: str, *args, **kwargs):
    """Log a daemon message"""
    _log_with_category(DAEMON, level, msg, *args, **kwargs)

def wallet(level: str, msg: str, *args, **kwargs):
    """Log a wallet message"""
    _log_with_category(WALLET, level, msg, *args, **kwargs)

def chain(level: str, msg: str, *args, **kwargs):
    """Log a blockchain message"""
    _log_with_category(CHAIN, level, msg, *args, **kwargs)

def network(level: str, msg: str, *args, **kwargs):
    """Log a network message"""
    _log_with_category(NETWORK, level, msg, *args, **kwargs)

def debug_log(msg: str, *args, **kwargs):
    """Log a debug message"""
    _log_with_category(DEBUG, "debug", msg, *args, **kwargs)

# Helper function for the shortcut functions
def _log_with_category(category: str, level: str, msg: str, *args, **kwargs):
    """Log a message with a specific category and level"""
    logger = get_logger(category)
    log_level = LEVELS.get(level.lower(), logging.INFO)
    
    # Pass all kwargs (including details) to the logger methods
    if log_level == logging.DEBUG:
        logger.debug(msg, *args, **kwargs)
    elif log_level == logging.INFO:
        logger.info(msg, *args, **kwargs)
    elif log_level == logging.WARNING:
        logger.warning(msg, *args, **kwargs)
    elif log_level == logging.ERROR:
        logger.error(msg, *args, **kwargs)
    elif log_level == logging.CRITICAL:
        logger.critical(msg, *args, **kwargs) 