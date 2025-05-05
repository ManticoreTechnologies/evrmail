# evrmail/gui/browser_panel.py

import flet as ft
import sys
import os
import threading
import time
from pathlib import Path
import tempfile
import webbrowser
import logging
import uuid
import shutil
import subprocess
from urllib.parse import urlparse
from evrmail.utils.ipfs import fetch_ipfs_json, fetch_ipfs_resource, fetch_ipns_resource
from evrmail import rpc_client
import base64
import hashlib
import requests
import urllib3
import ssl
from Crypto.Hash import RIPEMD160
import base58
import json

# Import PyQt components
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrowserPanel")

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a temp directory for content if it doesn't exist
TEMP_DIR = Path(tempfile.gettempdir()) / "evrmail_browser"
TEMP_DIR.mkdir(exist_ok=True)

# Global PyQt objects
qt_app = None
web_view = None
web_widget = None
browser_visible = False
browser_position = (0, 0)
browser_size = (800, 600)

def pubkey_to_address(pubkey: bytes) -> str:
    """
    Hash160 + base58 for Evrmore P2PKH (prefix=0x21 => 'E').
    """
    h = hashlib.sha256(pubkey).digest()
    r160 = RIPEMD160.new(h).digest()
    versioned = b'\x21' + r160  # 0x21 => "E"
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return base58.b58encode(versioned + checksum).decode()

def fetch_web_content(url):
    """Fetch content from a regular web URL with robust error handling"""
    try:
        # Add http:// if no scheme is provided
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            
        # Use a more browser-like User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # First try with verification
        try:
            logger.info(f"Fetching URL with verification: {url}")
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=True
            )
            response.raise_for_status()
        except (requests.exceptions.SSLError, ssl.SSLError, requests.exceptions.ConnectionError) as e:
            # If SSL verification fails, try without verification
            logger.warning(f"SSL verification failed, retrying without: {str(e)}")
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=False
            )
            response.raise_for_status()
        
        return {
            'content': response.text,
            'content_type': response.headers.get('Content-Type', 'text/html'),
            'status': response.status_code,
            'url': response.url,
            'headers': dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {str(e)}")
        return {
            'error': str(e),
            'url': url
        }
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {str(e)}")
        return {
            'error': f"Unexpected error: {str(e)}",
            'url': url
        }

class HtmlFileManager:
    """Manages temporary HTML files for displaying content"""
    def __init__(self):
        self.html_files = {}
        
    def create_html_file(self, html_content):
        """Create a temporary HTML file from content and return its path"""
        content_id = str(uuid.uuid4())
        temp_file = TEMP_DIR / f"{content_id}.html"
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Add to the list of files for cleanup
            self.html_files[content_id] = temp_file
            
            return str(temp_file)
        except Exception as e:
            logger.error(f"Error creating HTML file: {str(e)}")
            return None
    
    def get_file_url(self, file_path):
        """Convert a file path to a file:// URL"""
        if not file_path:
            return None
        
        path = Path(file_path)
        if not path.exists():
            return None
            
        return f"file://{path.absolute()}"
        
    def cleanup(self):
        """Clean up temporary files"""
        for content_id, file_path in self.html_files.items():
            try:
                if Path(file_path).exists():
                    Path(file_path).unlink()
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {str(e)}")

# Create a singleton file manager
html_manager = HtmlFileManager()

def create_browser_panel():
    """Create a browser panel with embedded PyQt WebEngineView"""
    global qt_app, web_view, web_widget, browser_visible
    
    # URL input field
    url_bar = ft.TextField(
        hint_text="🔎 Enter URL or EvrNet domain (e.g. example.com or chess.evr)...",
        border_color="#3ea6ff",
        expand=True,
        border_radius=8,
        prefix_icon=ft.icons.SEARCH,
    )
    
    # Status display
    status_display = ft.Text(
        value="",
        color="#3ea6ff",
        weight="bold",
        size=14,
    )
    
    # Browser container where we'll position our PyQt WebView
    browser_container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Enter a URL or EVR domain above to browse", 
                    size=18, 
                    weight="bold", 
                    color="#00e0b6",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text("Browser will be embedded here",
                       color="#ccc", 
                       text_align=ft.TextAlign.CENTER,
                       size=16),
                ft.Text("Examples: example.com, chess.evr", 
                        color="#3ea6ff", 
                        text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        bgcolor="#121212",
        border_radius=8,
        expand=True,
        border=ft.border.all(color="#333", width=1),
    )
    
    def initialize_browser():
        """Initialize the PyQt browser components"""
        global qt_app, web_view, web_widget
        
        try:
            # Create QApplication if not exists
            if QApplication.instance() is None:
                qt_app = QApplication(sys.argv)
            else:
                qt_app = QApplication.instance()
            
            # Create browser widget
            web_widget = QWidget()
            web_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
            
            layout = QVBoxLayout(web_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Create WebView
            web_view = QWebEngineView()
            layout.addWidget(web_view)
            
            # Connect signals
            web_view.page().titleChanged.connect(
                lambda title: update_status(f"Page title: {title}")
            )
            web_view.page().loadStarted.connect(
                lambda: update_status("Loading...")
            )
            web_view.page().loadFinished.connect(
                lambda ok: update_status("Loaded" if ok else "Failed to load")
            )
            
            # Set initial content
            web_view.setHtml("""
            <html>
            <body style="background-color: #121212; color: white; text-align: center; padding-top: 100px; font-family: Arial;">
                <h1 style="color: #00e0b6;">EvrMail Browser</h1>
                <p>Enter a URL to start browsing</p>
            </body>
            </html>
            """)
            
            # Hide initially
            web_widget.hide()
            
            update_status("Browser initialized")
            return True
        except Exception as e:
            update_status(f"Error initializing browser: {str(e)}")
            logger.error(f"Browser initialization error: {e}")
            return False
    
    def update_status(message):
        """Update status display with a message"""
        if status_display.page:
            status_display.value = message
            status_display.update()
    
    def load_url(url=None):
        """Load a URL in the embedded browser"""
        global web_view, web_widget, browser_visible
        
        if url is None or isinstance(url, ft.ControlEvent):
            url = url_bar.value.strip() if url_bar.value else ""
        
        if not url:
            update_status("Please enter a URL")
            return
            
        # Parse EVR domains
        if url.endswith('.evr'):
            update_status(f"⏳ Looking up EVR domain: {url}")
            try:
                domain_parts = url.split('.')
                domain_name = domain_parts[0]
                
                # Get IPFS hash for domain
                rpc = rpc_client.get_client()
                result = rpc.name_show(domain_name)
                
                if not result or 'value' not in result:
                    update_status(f"❌ EVR domain not found: {url}")
                    return
                    
                ipfs_hash = result.get('value', '')
                if not ipfs_hash:
                    update_status(f"❌ EVR domain has no IPFS hash: {url}")
                    return
                
                # Show IPFS hash
                update_status(f"🔍 Found IPFS hash for {url}: {ipfs_hash}")
                
                # Fetch content from IPFS
                update_status(f"⏳ Fetching content from IPFS: {ipfs_hash}")
                content = fetch_ipfs_resource(ipfs_hash)
                
                if not content:
                    update_status(f"❌ Failed to fetch IPFS content for {url}")
                    return
                    
                # Create a temporary HTML file
                html_path = html_manager.create_html_file(content)
                if not html_path:
                    update_status(f"❌ Failed to create HTML file for {url}")
                    return
                    
                # Load the file URL
                file_url = html_manager.get_file_url(html_path)
                
                if file_url:
                    # Update URL bar
                    url_bar.value = url
                    if url_bar.page:
                        url_bar.update()
                    
                    # Load in browser
                    update_status(f"✅ Loading EVR domain: {url}")
                    
                    if web_view:
                        web_view.setUrl(QUrl(file_url))
                        show_browser()
                    else:
                        update_status(f"❌ Browser not initialized")
                else:
                    update_status(f"❌ Failed to create file URL for {url}")
            except Exception as e:
                update_status(f"❌ Error loading EVR domain: {str(e)}")
                logger.error(f"Error loading EVR domain {url}: {e}")
        else:
            # Regular URL handling
            update_status(f"⏳ Loading URL: {url}")
            
            # Add scheme if missing
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            
            # Update URL bar
            url_bar.value = url
            if url_bar.page:
                url_bar.update()
            
            if web_view:
                web_view.setUrl(QUrl(url))
                show_browser()
            else:
                update_status(f"❌ Browser not initialized")
    
    def show_browser():
        """Position and show the embedded browser"""
        global web_widget, browser_visible, browser_position
        
        if not web_widget:
            update_status("Browser not initialized")
            return
            
        try:
            # Get container position
            if not browser_container.page:
                update_status("Container not ready")
                return
                
            # Need to position based on window position plus an offset
            # This is a basic approximation that will need adjustment
            x = browser_container.page.window_left + 20
            y = browser_container.page.window_top + 200
            
            width = browser_container.page.window_width - 40
            height = browser_container.page.window_height - 300
            
            update_status(f"Positioning browser at ({x}, {y}) with size ({width}, {height})")
            
            # Show and position browser
            web_widget.setGeometry(x, y, width, height)
            web_widget.show()
            web_widget.activateWindow()
            
            browser_visible = True
        except Exception as e:
            update_status(f"Error showing browser: {str(e)}")
            logger.error(f"Error showing browser: {e}")
    
    def hide_browser():
        """Hide the embedded browser"""
        global web_widget, browser_visible
        
        if web_widget:
            web_widget.hide()
            browser_visible = False
            update_status("Browser hidden")
    
    def update_browser_position(e=None):
        """Update the browser position to follow container"""
        global web_widget, browser_visible
        
        if browser_visible and web_widget and browser_container.page:
            try:
                x = browser_container.page.window_left + 20
                y = browser_container.page.window_top + 200
                
                width = browser_container.page.window_width - 40
                height = browser_container.page.window_height - 300
                
                web_widget.setGeometry(x, y, width, height)
            except Exception as e:
                logger.error(f"Error updating browser position: {e}")
    
    # Connect the enter key to the load function
    url_bar.on_submit = load_url
    
    # Browser buttons
    load_button = ft.ElevatedButton(
        "Load URL",
        icon=ft.icons.REFRESH,
        on_click=load_url,
        bgcolor="#00e0b6",
        color="black",
    )
    
    # External browser button
    external_button = ft.ElevatedButton(
        "Open in System Browser",
        icon=ft.icons.OPEN_IN_BROWSER,
        on_click=lambda e: webbrowser.open(url_bar.value),
    )
    
    # Top bar with URL input and buttons
    top_bar = ft.Column([
        ft.Row(
        [
            url_bar,
            load_button,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        ft.Row(
            [
                external_button,
        ],
        spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    ], spacing=10)
    
    # Bottom status bar
    bottom_bar = ft.Container(
        content=status_display,
        padding=5,
        bgcolor="#0a0a0a",
        border_radius=ft.border_radius.only(
            bottom_left=8, 
            bottom_right=8
        ),
    )
    
    # Combine everything into the panel
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text("EvrMail Browser", size=20, weight="bold", color="#3ea6ff"),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10),
                ),
                top_bar,
                browser_container,
                bottom_bar,
            ],
            spacing=10,
            expand=True,
        ),
        padding=20,
        expand=True,
    )
    
    # Handle delayed initialization
    def delayed_init():
        """Initialize after panel is added to the page"""
        if panel.page:
            update_status("Initializing browser...")
            
            # Initialize browser in a separate thread to avoid blocking UI
            threading.Thread(target=initialize_browser, daemon=True).start()
            
            # Set up window event handlers
            panel.page.on_window_event = lambda e: threading.Timer(0.1, update_browser_position).start() if e.data == "move" else None
    
    # Handle cleanup
    def cleanup_resources():
        """Clean up resources when panel is removed"""
        global web_view, web_widget
        
        # Hide browser
        hide_browser()
        
        # Clean up browser objects
        if web_view:
            web_view.setParent(None)
            web_view = None
            
        if web_widget:
            web_widget.close()
            web_widget = None
            
        # Clean up temp files
        html_manager.cleanup()
    
    panel.delayed_init = delayed_init
    panel.cleanup = cleanup_resources
    
    return panel
