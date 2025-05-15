from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QRect
import sys
import os
import sys
import os
from PyQt5.QtCore import QUrl

# Import our WebUIBridge from functions
from evrmail.gui.functions import WebUIBridge

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    # First check if the path exists relative to current directory
    current_dir_path = os.path.join(os.getcwd(), relative_path)
    if os.path.exists(current_dir_path):
        return current_dir_path
    
    # Then check if path exists relative to this file's directory
    file_dir = os.path.dirname(os.path.abspath(__file__))
    file_dir_path = os.path.join(file_dir, '..', relative_path)
    if os.path.exists(file_dir_path):
        return file_dir_path
    
    # If neither exists, use the standard resource path logic
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class BackendBridge(QObject):
    @pyqtSlot(str)
    def load_url(self, url):
        if not url.startswith("http"):
            url = "https://" + url
        print(f"[JS → Python] Load URL: {url}")
        main_window.browser_view.setUrl(QUrl(url))
        main_window.browser_view.show()

    @pyqtSlot(str)
    def log(self, message):
        print(f"[JS LOG]: {message}")

    @pyqtSlot(str)
    def openTab(self, tabName):
        print(f"[JS] Opened tab: {tabName}")
        if tabName == "browser":
            self.show_browser()
        else:
            self.hide_browser()

    def show_browser(self):
        # Only show browser if we have valid geometry
        if hasattr(main_window.browser_view, 'last_geometry'):
            main_window.browser_view.setGeometry(main_window.browser_view.last_geometry)
            main_window.browser_view.show()
        
    def hide_browser(self):
        # Hide the browser view when not on browser tab
        main_window.browser_view.hide()

    @pyqtSlot(int, int, int, int)
    def set_browser_geometry(self, x, y, w, h):
        print(f"[JS → Python] Browser geometry: ({x}, {y}, {w}x{h})")
        # Store the geometry for later use
        geometry = QRect(x, y, w, h)
        main_window.browser_view.last_geometry = geometry
        
        # Only set geometry and show if we're on the browser tab
        if main_window.browser_view.isVisible():
            main_window.browser_view.setGeometry(geometry)
            main_window.browser_view.show()

class MainWindow(QMainWindow):
    def __init__(self, path=None, nodejs=False):
        super().__init__()
        self.setWindowTitle("EvrMail Hybrid GUI")
        self.resize(1200, 800)

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # <-- remove outer margin
        layout.setSpacing(0)       
        central.setLayout(layout)

        # Web UI
        self.ui_view = QWebEngineView()
        layout.addWidget(self.ui_view)

        # Overlay browser view
        self.browser_view = QWebEngineView(self)
        self.browser_view.hide()  # Initially hidden
        self.browser_view.last_geometry = QRect(0, 0, 0, 0)  # Initialize with empty geometry

        # WebChannel bridge
        self.channel = QWebChannel()
        
        # Create and register UI control bridge for basic tab switching and browser management
        self.ui_bridge = BackendBridge()
        
        # Create and register advanced backend bridge for all functionality
        self.backend_bridge = WebUIBridge()
        
        # Register both bridges to the channel
        self.channel.registerObject("backend", self.backend_bridge)  # Main bridge for all functionality
        self.channel.registerObject("uicontrol", self.ui_bridge)     # Bridge for UI-specific controls

        # Set the WebChannel for the UI view
        self.ui_view.page().setWebChannel(self.channel)
        
        # Set the WebChannel for the browser view as well
        self.browser_view.page().setWebChannel(self.channel)
        
        # Load the appropriate UI
        if nodejs:
            # Start the nodejs dev server if needed
            if os.environ.get("EVRMAIL_NODE_SERVER_STARTED") != "1":
                os.environ["EVRMAIL_NODE_SERVER_STARTED"] = "1"
                print("Starting nodejs dev server...")
                webui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webui")
                os.system(f"gnome-terminal -- bash -c 'cd {webui_path} && npm run dev'")
                print(f"Started nodejs dev server from {webui_path}")
            import time 
            time.sleep(1)
            # Use nodejs dev server
            html_path = "http://localhost:5173"
            self.ui_view.setUrl(QUrl(html_path))
        elif path:
            # Use provided path (could be dist or custom)
            self.ui_view.setUrl(QUrl.fromLocalFile(path))
        else:
            # Default to dist directory
            webui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webui")
            dist_path = os.path.join(webui_path, "dist", "index.html")
            if not os.path.exists(dist_path):
                print(f"Warning: Could not find {dist_path}")
                # Try to find the file in different locations
                alt_paths = [
                    "webui/dist/index.html",
                    "src/evrmail/webui/dist/index.html",
                    "../webui/dist/index.html"
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        dist_path = alt_path
                        print(f"Using alternative path: {dist_path}")
                        break
            
            print(f"Loading UI from: {dist_path}")
            self.ui_view.setUrl(QUrl.fromLocalFile(os.path.abspath(dist_path)))

def main(path=None, nodejs=False, argv=None):
    """
    Start the Qt application
    
    Args:
        path: Path to the HTML file to load
        nodejs: Whether to use nodejs development server
        argv: Command line arguments to pass to the application
    """
    # Use system arguments if none provided
    if argv is None:
        argv = sys.argv
    
    # Check if --nodejs is in the arguments
    if "--nodejs" in argv and not nodejs:
        nodejs = True
    
    print(f"Starting EvrMail with nodejs mode: {nodejs}")
    
    # Create Qt application
    app = QApplication(argv)
    
    # Create main window
    global main_window
    main_window = MainWindow(path=path, nodejs=nodejs)
    main_window.show()
    
    # Run the application
    return sys.exit(app.exec_())

def build_appimage():
    print("Building appimage")
    os.system("pyinstaller hello_gui.py --noconfirm --onefile --windowed --name EvrMailGUI --icon=hello_256.png")
    
def nodejs_mode():
    print("nodejs mode")
    # run the gui with nodejs mode
    main(nodejs=True)

if __name__ == "__main__":
    arguments = sys.argv[1:]
    print(arguments)
    
    if "--nodejs" in arguments:
        nodejs_mode()
    elif "--build-appimage" in arguments:
        build_appimage()
    else:
        # Default to dist directory
        main()
