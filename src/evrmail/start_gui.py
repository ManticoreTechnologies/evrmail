"""
📬 EvrMail - Start GUI Application
"""

import sys
import os
from pathlib import Path

# Import the main function from gui module
from evrmail.gui.start_gui import main as start_gui

def main():
    """
    Entry point for starting the EvrMail GUI application
    """
    # Get the path to the webui/dist directory
    base_dir = Path(__file__).parent
    webui_dist_path = base_dir / "webui" / "dist" / "index.html"
    
    # Check if we're in development mode
    nodejs_mode = "--nodejs" in sys.argv
    
    # Start the GUI application
    if nodejs_mode:
        start_gui(nodejs=True)
    else:
        # Use the absolute path to the dist directory
        start_gui(path=str(webui_dist_path.absolute()))

if __name__ == "__main__":
    main() 