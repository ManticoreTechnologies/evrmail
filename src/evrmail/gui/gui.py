"""
📬 EvrMail GUI — UI interface for EvrMail
"""

import sys
import os
import threading
from pathlib import Path
import logging
from evrmail.utils import gui as gui_log, configure_logging
from evrmail.wallet.utils import calculate_balances, load_all_wallet_keys
from evrmail.wallet.addresses import get_all_addresses
from evrmail.gui.start_gui import main as start_qt_gui

def start_gui(nodejs=False):
    """
    Launch the EvrMail application using the Qt-based interface
    
    This function replaces the old Eel-based interface with the new Qt WebEngine + QWebChannel setup
    
    Args:
        nodejs: Whether to use nodejs development server
    """
    try:
        # Configure logging
        configure_logging(level=logging.INFO)
        gui_log("info", "Starting EvrMail GUI with Qt WebEngine interface")
        
        # Set web folder location (relative to this file)
        web_folder = Path(__file__).parent.parent / "webui" / "dist"
        if not web_folder.exists():
            gui_log("error", f"Web folder not found at {web_folder}")
            raise FileNotFoundError(f"Web folder not found at {web_folder}")
        
        gui_log("info", f"Using web folder: {web_folder}")
        
        # Pre-load some data that might be needed at startup
        threading.Thread(target=_preload_data, daemon=True).start()
        
        # Start the Qt-based GUI application
        gui_log("info", "Starting Qt WebEngine application...")
        
        # Get the path to the main HTML file
        html_path = web_folder / "index.html"
        
        # Check if we should use nodejs mode for development
        gui_log("info", f"NodeJS mode: {nodejs}")
        
        # Pass the --nodejs flag to sys.argv if needed
        if nodejs and "--nodejs" not in sys.argv:
            sys.argv.append("--nodejs")
        
        # Start the Qt application with appropriate options
        start_qt_gui(
            path=str(html_path.absolute()),
            nodejs=nodejs,
            argv=sys.argv
        )
        
        gui_log("info", "Qt WebEngine application started")
    except SystemExit:
        # Normal exit
        gui_log("info", "EvrMail GUI shutting down normally")
        pass
    except KeyboardInterrupt:
        # Ctrl+C exit
        gui_log("info", "Keyboard interrupt detected, exiting...")
    except Exception as e:
        # If there's an error starting the app, try to open in fallback mode
        import traceback
        error_msg = f"Error starting Qt WebEngine app: {str(e)}"
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