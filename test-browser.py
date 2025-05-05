import flet as ft
import sys
from pathlib import Path
import threading
import time

# Import required PyQt components
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt

# Global app instance
qt_app = None
web_view = None
web_widget = None
browser_visible = False
browser_position = (0, 0)
browser_size = (800, 600)

def main(page: ft.Page):
    global qt_app, web_view, web_widget, browser_visible, browser_position, browser_size
    
    page.title = "Embedded Browser Test"
    page.window_width = 1000
    page.window_height = 800
    
    # URL input
    url_input = ft.TextField(
        hint_text="Enter URL (e.g., https://flet.dev)...",
        expand=True,
        on_submit=lambda e: load_url(url_input.value),
    )
    
    # Status text
    status_text = ft.Text("Ready")
    
    # Functions for browser management
    def initialize_browser():
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
                lambda title: page.invoke_async(lambda: set_status(f"Page title: {title}"))
            )
            web_view.page().loadStarted.connect(
                lambda: page.invoke_async(lambda: set_status("Loading..."))
            )
            web_view.page().loadFinished.connect(
                lambda ok: page.invoke_async(lambda: set_status("Loaded" if ok else "Failed to load"))
            )
            
            # Set initial size and position
            web_widget.resize(browser_size[0], browser_size[1])
            
            # Load default content
            web_view.setHtml("""
            <html>
            <body style="background-color: #121212; color: white; text-align: center; padding-top: 100px; font-family: Arial;">
                <h1 style="color: #00e0b6;">EvrMail Test Browser</h1>
                <p>Enter a URL to start browsing</p>
            </body>
            </html>
            """)
            
            # Hide initially
            web_widget.hide()
            
            return True
        except Exception as e:
            status_text.value = f"Error initializing browser: {str(e)}"
            page.update()
            return False
    
    def set_status(message):
        status_text.value = message
        page.update()
    
    def load_url(url):
        global web_view, web_widget, browser_visible
        
        if not url:
            return
            
        # Add scheme if missing
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        status_text.value = f"Loading: {url}"
        page.update()
        
        if web_view:
            web_view.setUrl(QUrl(url))
            
            # Make browser visible
            if not browser_visible:
                show_browser()
    
    def show_browser():
        global web_widget, browser_visible, browser_position
        
        if not web_widget:
            return
            
        # Update position to match container's position
        x = browser_container.page.window_left + 100
        y = browser_container.page.window_top + 200
        
        # Show browser
        web_widget.setGeometry(x, y, browser_size[0], browser_size[1])
        web_widget.show()
        web_widget.activateWindow()
        
        browser_visible = True
    
    def hide_browser():
        global web_widget, browser_visible
        
        if web_widget:
            web_widget.hide()
            browser_visible = False
    
    def update_browser_position():
        global web_widget, browser_visible, browser_position
        
        # Only update if visible
        if browser_visible and web_widget:
            x = browser_container.page.window_left + 100
            y = browser_container.page.window_top + 200
            
            web_widget.move(x, y)
    
    # Browser container placeholder
    browser_container = ft.Container(
        content=ft.Column(
            [
                ft.Text("Browser Area", size=20, weight="bold", color="#00e0b6"),
                ft.Text("Browser will be initialized when you enter a URL", size=14, color="#ccc"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#121212",
        border_radius=8,
        expand=True,
        height=500,
        border=ft.border.all(color="#333", width=1),
    )
    
    # Load button
    load_button = ft.ElevatedButton(
        "Load URL",
        icon=ft.icons.REFRESH,
        on_click=lambda e: load_url(url_input.value),
    )
    
    # Add controls to page
    page.add(
        ft.Column([
            ft.Text("Embedded Browser Test", size=24, weight="bold"),
            ft.Row([url_input, load_button], spacing=10),
            browser_container,
            status_text,
        ], spacing=20, expand=True)
    )
    
    # Initialize browser in a separate thread
    threading.Thread(target=initialize_browser, daemon=True).start()
    
    # Set up window move event handler to reposition browser
    def on_window_event(e):
        if e.data == "move":
            # Use a small delay to ensure window has settled
            threading.Timer(0.1, update_browser_position).start()
    
    page.on_window_event = on_window_event
    
    # Make sure browser is closed when app exits
    def on_close(e):
        global web_widget, web_view
        
        if web_view:
            web_view.setParent(None)
            web_view.deleteLater()
        
        if web_widget:
            web_widget.close()
            web_widget.deleteLater()
    
    page.on_close = on_close

if __name__ == "__main__":
    ft.app(target=main) 