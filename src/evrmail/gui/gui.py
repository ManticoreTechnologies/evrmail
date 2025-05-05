"""
📬 EvrMail GUI — Eel-based interface for EvrMail
"""

import eel
import sys
import os
import threading
from pathlib import Path
import logging
import time
from evrmail.utils import gui as gui_log, configure_logging
from evrmail.wallet.utils import calculate_balances, load_all_wallet_keys
from evrmail.wallet.addresses import get_all_addresses

def start_gui():
    """Launch the EvrMail application using Eel"""
    try:
        # Configure logging
        configure_logging(level=logging.INFO)
        gui_log("info", "Starting EvrMail GUI with Eel interface")
        
        # Set web folder location (relative to this file)
        web_folder = Path(__file__).parent / "web"
        if not web_folder.exists():
            gui_log("error", f"Web folder not found at {web_folder}")
            raise FileNotFoundError(f"Web folder not found at {web_folder}")
        
        gui_log("info", f"Using web folder: {web_folder}")
        
        # Initialize Eel with the web folder
        eel.init(str(web_folder))
        
        # Expose Python functions to JavaScript
        from .functions import expose_all_functions
        expose_all_functions()
        gui_log("info", "Exposed Python functions to JavaScript")
        
        # Pre-load some data that might be needed at startup
        threading.Thread(target=_preload_data, daemon=True).start()
        
        # Start the Eel app
        gui_log("info", "Starting Eel application...")
        eel.start('index.html', 
                  size=(1080, 720), 
                  port=0,  # Use any available port
                  cmdline_args=['--disable-features=TranslateUI', '--disable-translation', '--no-cache'],
                  app_mode=True)
        gui_log("info", "Eel application started")
    except SystemExit:
        # Normal exit
        gui_log("info", "EvrMail GUI shutting down normally")
        pass
    except KeyboardInterrupt:
        # Ctrl+C exit
        gui_log("info", "Keyboard interrupt detected, exiting...")
    except Exception as e:
        # If there's an error starting the Eel app, try to open in fallback mode
        import traceback
        error_msg = f"Error starting Eel app: {str(e)}"
        gui_log("error", error_msg)
        traceback.print_exc()
        
        # Fallback to basic browser window
        gui_log("info", "Attempting fallback to basic browser window")
        try:
            if sys.platform.startswith('win'):
                os.system(f'start {web_folder / "index.html"}')
            elif sys.platform.startswith('darwin'):
                os.system(f'open {web_folder / "index.html"}')
            else:
                os.system(f'xdg-open {web_folder / "index.html"}')
            gui_log("info", "Opened fallback browser window")
        except Exception as fallback_error:
            gui_log("error", f"Failed to open fallback browser: {fallback_error}")

def _preload_data():
    """Preload some data that might be needed at startup"""
    try:
        # Perform tasks that might take time but should be ready when the UI loads
        gui_log("info", "Preloading wallet data...")
        
        # Load addresses
        addresses = get_all_addresses(False)
        gui_log("info", f"Preloaded {len(addresses)} wallet addresses")
        
        # Calculate balances
        balances = calculate_balances()
        gui_log("info", "Preloaded wallet balances")
        
        # Additional preloading could be added here
        
    except Exception as e:
        gui_log("error", f"Error preloading data: {str(e)}") 