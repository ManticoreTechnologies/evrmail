import eel
import sys
import os
from pathlib import Path

def start_gui():
    """Launch the EvrMail application using Eel"""
    
    # Initialize eel with the web directory
    eel_root = Path(__file__).parent / 'web'
    eel.init(str(eel_root))
    
    try:
        # Start the Eel application
        eel.start('index.html', 
                  size=(1080, 720),
                  port=0,  # Use any available port
                  cmdline_args=['--disable-cache', '--disk-cache-size=0'],
                  )
    except (SystemExit, KeyboardInterrupt):
        # Exit gracefully
        pass
    except Exception as e:
        print(f"Error starting Eel: {e}")
        # Fallback to a basic browser window
        import webbrowser
        webbrowser.open(f'file://{os.path.join(eel_root, "index.html")}')

if __name__ == '__main__':
    start_gui()
