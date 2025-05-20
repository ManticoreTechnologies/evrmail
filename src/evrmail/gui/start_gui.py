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
        from .functions import get_evr_url, navigate_browser
        
        try:
            # Sanitize and validate URL
            url = url.strip()
            if not url:
                self._show_error_page("Empty URL", "Please enter a valid URL.")
                return
            
            # Signal loading state to the UI
            self._signal_loading_state(True, url)
            
            # Show loading indicator first
            self._show_loading_page(url)
            
            # Special handling for EVR domains
            if url.endswith(".evr"):
                # Process EVR domain URLs
                processed_url = get_evr_url(url)
                print(f"[JS → Python] Load URL: {url} → {processed_url}")
                
                # Check if processed_url is a dictionary (error response)
                if isinstance(processed_url, dict):
                    error_msg = processed_url.get('error', 'Unknown error')
                    print(f"Error processing EVR URL: {error_msg}")
                    
                    # Signal loading finished to the UI
                    self._signal_loading_state(False, url, success=False)
                    
                    # Display a generic error page
                    self._show_error_page("Error Processing EVR Domain", error_msg, domain=url)
                else:
                    # Normal case - use the processed URL
                    main_window.browser_view.setUrl(QUrl(processed_url))
                    main_window.browser_view.show()
            else:
                # For regular URLs, format them and load directly
                if not url.startswith("http://") and not url.startswith("https://"):
                    # Handle spaces and special characters
                    url = url.replace(" ", "%20")
                    url = "https://" + url
                
                print(f"[JS → Python] Load URL: {url}")
                main_window.browser_view.setUrl(QUrl(url))
                main_window.browser_view.show()
        except Exception as e:
            print(f"Error navigating to URL: {str(e)}")
            # Signal loading error to UI
            self._signal_loading_state(False, url, success=False)
            self._show_error_page("Navigation Error", f"An error occurred: {str(e)}", domain=url)
    
    def _signal_loading_state(self, is_loading, url="", success=True):
        """Signal loading state to the UI via JavaScript"""
        try:
            script = f"""
            if (window.updateBrowserLoadingState) {{
                window.updateBrowserLoadingState({str(is_loading).lower()}, "{url}", {str(success).lower()});
            }}
            """
            main_window.ui_view.page().runJavaScript(script)
        except Exception as e:
            print(f"Error signaling loading state: {e}")
    
    def _show_loading_page(self, url):
        """Display a loading indicator while the page is being loaded"""
        domain = url.split("://")[-1].split("/")[0] if "://" in url else url.split("/")[0]
        loading_html = f"""
        <html>
        <head>
            <title>Loading {domain}...</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #333;
                }}
                .loading-container {{
                    text-align: center;
                    padding: 30px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    max-width: 80%;
                }}
                h2 {{
                    margin-bottom: 20px;
                    color: #2c3e50;
                }}
                .spinner {{
                    display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 5px solid rgba(0,0,0,0.1);
                    border-radius: 50%;
                    border-top-color: #3498db;
                    animation: spin 1s ease-in-out infinite;
                    margin-bottom: 20px;
                }}
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                .url {{
                    color: #3498db;
                    word-break: break-all;
                    font-size: 16px;
                    margin-top: 15px;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="loading-container">
                <div class="spinner"></div>
                <h2>Loading...</h2>
                <div class="url">{url}</div>
            </div>
        </body>
        </html>
        """
        main_window.browser_view.setHtml(loading_html)
        main_window.browser_view.show()
    
    def _show_error_page(self, title, message, domain=None):
        """Display a simple error page in the browser view"""
        domain_info = f"<div class='domain'>Address: <span>{domain}</span></div>" if domain else ""
        suggestions = """
        <div class='suggestions'>
            <h3>Suggestions:</h3>
            <ul>
                <li>Check that the domain name is spelled correctly</li>
                <li>Make sure your internet connection is working</li>
                <li>Try visiting a popular website like <a href='https://google.com'>Google</a></li>
            </ul>
        </div>
        """
        
        error_html = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    text-align: center;
                    background-color: #f5f5f5;
                    margin: 0;
                }}
                .error-container {{
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    background-color: white;
                }}
                h1 {{
                    color: #e74c3c;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #333;
                    line-height: 1.6;
                    font-size: 16px;
                }}
                .domain {{
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    color: #666;
                }}
                .domain span {{
                    color: #2980b9;
                    font-weight: bold;
                    word-break: break-all;
                }}
                .suggestions {{
                    text-align: left;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }}
                .suggestions h3 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                }}
                .suggestions ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .suggestions li {{
                    margin-bottom: 10px;
                    color: #555;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>{title}</h1>
                <p>{message}</p>
                {domain_info}
                {suggestions}
            </div>
        </body>
        </html>
        """
        self._show_error_content(error_html)
    
    def _show_error_content(self, html_content):
        """Display custom HTML content in the browser view"""
        main_window.browser_view.setHtml(html_content)
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
        
        # Connect load status signals to track page loading
        self.browser_view.loadStarted.connect(self.on_page_load_started)
        self.browser_view.loadFinished.connect(self.on_page_load_finished)

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

    def on_page_load_started(self):
        """Called when a page starts loading"""
        print("[Browser] Page loading started")
        url = self.browser_view.url().toString()
        # Signal loading state to the UI
        self.ui_bridge._signal_loading_state(True, url)

    def on_page_load_finished(self, success):
        """Called when a page finishes loading, whether successful or not"""
        url = self.browser_view.url().toString()
        if success:
            print(f"[Browser] Page loaded successfully: {url}")
            # Signal loading state to the UI
            self.ui_bridge._signal_loading_state(False, url, success=True)
        else:
            print(f"[Browser] Page failed to load: {url}")
            # Signal loading state to the UI
            self.ui_bridge._signal_loading_state(False, url, success=False)
            # Show a custom error page if the load failed
            # but only if we're still on the same URL (user didn't navigate away)
            if url not in ["about:blank", ""]:
                self.ui_bridge._show_error_page(
                    "Page Failed to Load",
                    "The requested web page failed to load. This could be due to network issues or the site may be unavailable.",
                    domain=url
                )

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
