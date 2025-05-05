import flet as ft
import sys, os
import threading
from queue import Queue
from functools import partial
import time
from pathlib import Path
import threading
import re
import logging

# Import logger
from evrmail.utils import (
    configure_logging, register_callback, daemon as daemon_log, gui as gui_log,
    APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG
)

# Import modules
from evrmail.daemon import start_daemon_threaded

# Import Flet panel implementations
from .wallet_panel import create_wallet_panel
from .log_panel import create_log_panel
from .browser_panel import create_browser_panel
from .settings_panel import create_settings_panel
from .compose_panel import create_compose_panel
from .inbox_panel import create_inbox_panel
from .balance_panel import create_balance_tab
from .utxo_panel import create_utxo_panel

# Global app reference
app = None

# Define a direct log callback function that will handle logs directly without going through the daemon adapter
def direct_log_callback(category, level_name, level_num, message, details=None):
    """
    Direct log callback function that can be registered with evrmail.utils.register_callback.
    This bypasses the adapter function in start_daemon_threaded.
    """
    # Store logs directly in the log panel if it's available
    if hasattr(app, "log_panel") and hasattr(app.log_panel, "log_entries"):
        # Get timestamp manually since we're not in the logger
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to log entries with details
        app.log_panel.log_entries.append((category, level_name, timestamp, message, details))
        
        # Update filters if panel is visible
        try:
            if hasattr(app.log_panel, "apply_filters"):
                app.log_panel.apply_filters()
        except Exception as e:
            print(f"Error updating log panel from direct callback: {e}")
    
    # Convert message to string for the simple loading screen logger
    log_str = f"[{category}] {message}"
    if app:
        app._append_log(log_str)
    else:
        print(log_str)  # Fallback if app is not initialized yet

class EvrMailApp:
    def __init__(self):
        self.log_queue = Queue()
        self.page = None
        self.log_output = None
        self.daemon_started = False
        self.current_view = None
        
        # Configure logging for the app at startup
        configure_logging(level=logging.INFO)
        
        # Make the app instance globally accessible so the direct_log_callback can use it
        global app
        app = self
        
    def _flush_log_queue(self, e=None):
        """Process any pending log messages in the queue"""
        try:
            if self.log_output and hasattr(self.log_output, "page") and self.log_output.page:
                while not self.log_queue.empty():
                    line = self.log_queue.get()
                    self.log_output.value += f"{line}\n"
                    self.log_output.update()
                    
                    # Check for successful daemon startup with more conditions
                    daemon_ready_patterns = [
                        "Daemon listening for transactions",
                        "Reloading known addresses",
                        "Block processed with",
                        "daemon ready"
                    ]
                    
                    if not self.daemon_started and any(pattern in line.lower() for pattern in daemon_ready_patterns):
                        gui_log("info", "Daemon appears to be ready, transitioning to inbox")
                        self.daemon_started = True
                        self.page.go("/inbox")
        except Exception as e:
            # Silently ignore errors if the control isn't properly initialized
            pass
            
        # Schedule the next update
        if hasattr(self, "log_timer_running") and self.log_timer_running:
            threading.Timer(0.25, self._flush_log_queue).start()

    def _append_log(self, msg: str):
        """Add a log message to the queue and log panel if available"""
        self.log_queue.put(msg)
        
        # Store logs in the log panel if it's already created and visible
        if hasattr(self, "log_panel") and hasattr(self.log_panel, "log_entries"):
            # The log callback in log_panel will handle this automatically
            pass

    def _start_background_daemon(self):
        """Start the EvrMail daemon in a background thread"""
        gui_log("info", "Starting EvrMail daemon...")
        
        # Register direct callbacks for detailed logging
        unsubscribe_funcs = []
        for category in [DAEMON, CHAIN, WALLET, NETWORK, DEBUG]:
            unsubscribe = register_callback(direct_log_callback, category)
            unsubscribe_funcs.append(unsubscribe)
        
        # Store unsubscribe functions to be called on shutdown
        self.daemon_log_unsubscribe_funcs = unsubscribe_funcs
        
        # Set a timeout to force transition to inbox after 10 seconds
        def force_start_timeout():
            if not self.daemon_started:
                gui_log("warning", "Forcing transition to inbox after timeout")
                self.daemon_started = True
                if self.page:
                    self.page.go("/inbox")
        
        # Schedule the timeout
        threading.Timer(10.0, force_start_timeout).start()
        
        # Start the daemon with our logger already configured
        # We'll use a simple message-only callback for the loading screen
        def simple_callback(msg):
            self._append_log(msg)
            # Check for successful daemon startup with more conditions
            daemon_ready_patterns = [
                "Daemon listening for transactions",
                "Reloading known addresses",
                "Block processed with",
                "daemon ready"
            ]
            
            if not self.daemon_started and any(pattern in msg.lower() for pattern in daemon_ready_patterns):
                gui_log("info", "Daemon startup detected from callback, transitioning to inbox")
                self.daemon_started = True
                # Switch to inbox view after daemon starts
                if self.page:
                    self.page.go("/inbox")
        
        # Start the daemon thread
        start_daemon_threaded(log_callback=simple_callback, debug_mode=False)

    def create_loading_view(self):
        """Create the loading view shown during daemon startup"""
        container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("🚀 Starting EvrMail Daemon...", size=20, color="#80cbc4", text_align=ft.TextAlign.CENTER),
                    ft.ProgressBar(width=400, color="#00e0b6"),
                    ft.Container(height=20),
                    ft.Text("Initializing...", size=14, color="#ccc"),
                    ft.Container(
                        content=ft.TextField(
                            multiline=True,
                            read_only=True,
                            value="",
                            text_size=13,
                            color="#ddd",
                            bgcolor="#121212",
                            border_color="#333",
                            min_lines=10,
                            max_lines=20,
                            expand=True,
                        ),
                        expand=True,
                        padding=20,
                    )
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            padding=40,
            expand=True,
        )
        
        # Store reference to log output field for updates
        self.log_output = container.content.controls[-1].content
        
        # Start log update timer using threading.Timer
        self.log_timer_running = True
        threading.Timer(0.25, self._flush_log_queue).start()
        
        return container

    def create_navigation_rail(self):
        """Create the side navigation rail"""
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type="all",
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.INBOX,
                    selected_icon=ft.icons.INBOX,
                    label="📥 Inbox",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.EDIT,
                    selected_icon=ft.icons.EDIT,
                    label="✉️ Compose",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ACCOUNT_BALANCE_WALLET,
                    selected_icon=ft.icons.ACCOUNT_BALANCE_WALLET, 
                    label="💼 Wallet",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.LANGUAGE,
                    selected_icon=ft.icons.LANGUAGE,
                    label="🌐 Browser",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS,
                    selected_icon=ft.icons.SETTINGS,
                    label="⚙️ Settings",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.DESCRIPTION,
                    selected_icon=ft.icons.DESCRIPTION,
                    label="📜 Logs",
                ),
            ],
            on_change=self.navigation_change,
        )
        return self.nav_rail

    def navigation_change(self, e):
        """Handle navigation rail selection changes"""
        selected_index = e.control.selected_index
        
        routes = ["/inbox", "/compose", "/wallet", "/browser", "/settings", "/logs"]
        if 0 <= selected_index < len(routes):
            self.page.go(routes[selected_index])

    def route_change(self, route):
        """Handle page route changes"""
        # Clear existing views
        self.page.views.clear()
        
        route_path = route.route
        
        # Special case for loading screen
        if route_path == "/":
            view = ft.View(
                route="/",
                controls=[self.create_loading_view()],
                bgcolor="#181818",
                padding=0
            )
            self.page.views.append(view)
            self.page.update()
            gui_log("info", "Displayed loading screen")
            return
        
        # Get navigation rail and select the right tab
        self.nav_rail = self.create_navigation_rail()
        
        # Set content based on route
        gui_log("info", f"Navigating to route: {route_path}")
        if route_path == "/inbox":
            self.nav_rail.selected_index = 0
            view_content = self.inbox_panel
        elif route_path == "/compose":
            self.nav_rail.selected_index = 1
            view_content = self.compose_panel
        elif route_path == "/wallet":
            self.nav_rail.selected_index = 2
            view_content = self.wallet_panel
        elif route_path == "/browser":
            self.nav_rail.selected_index = 3
            view_content = self.browser_panel
        elif route_path == "/settings":
            self.nav_rail.selected_index = 4
            view_content = self.settings_panel
        elif route_path == "/logs":
            self.nav_rail.selected_index = 5
            view_content = self.log_panel
            gui_log("info", "Switching to logs panel")
        else:
            self.nav_rail.selected_index = 0
            view_content = self.inbox_panel
        
        # Create main column without any custom app bar
        main_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.nav_rail,
                        ft.VerticalDivider(),
                        view_content
                    ],
                    expand=True
                )
            ],
            expand=True
        )
        
        # Create and add the view
        view = ft.View(
            route=route_path,
            controls=[main_column],
            bgcolor="#181818",
            padding=0
        )
        
        self.page.views.append(view)
        self.page.update()
        
        # Call the delayed_init function if it exists on the current panel
        try:
            if hasattr(view_content, "delayed_init"):
                gui_log("info", f"Calling delayed_init for {route_path}")
                view_content.delayed_init()
                gui_log("info", f"delayed_init completed for {route_path}")
        except Exception as e:
            gui_log("error", f"Error in delayed_init: {str(e)}")

    def toggle_maximize(self, e=None):
        """Toggle between maximized and normal window state"""
        self.page.window_maximized = not self.page.window_maximized
        self.page.update()

    def exit_app(self, e=None):
        """Exit the application"""
        gui_log("info", "Exiting application")
        
        # Set a flag to indicate we're shutting down
        self.page._closing = True
        
        # Stop the log timer first
        self.log_timer_running = False
        
        # Clean up log panel if it exists
        if hasattr(self, "log_panel") and hasattr(self.log_panel, "cleanup"):
            try:
                self.log_panel.cleanup()
                gui_log("info", "Log panel cleanup completed")
            except Exception as e:
                gui_log("error", f"Error cleaning up log panel: {e}")
                
        # Close the window after cleanup
        self.page.window_close()

    def minimize_to_tray(self, e=None):
        """Minimize to system tray"""
        # Note: Flet doesn't have built-in system tray support
        # This would require platform-specific code to implement
        self.page.window_minimized = True
        self.page.update()

    def main(self, page: ft.Page):
        """Main entry point for the Flet application"""
        self.page = page
        page.title = "📬 EvrMail"
        page.window_width = 1080
        page.window_height = 720
        page.window_min_width = 840
        page.window_min_height = 520
        page.theme_mode = "dark"
        page.bgcolor = "#181818"
        page.padding = 0
        
        # Create theme with EvrMail colors
        page.theme = ft.Theme(
            color_scheme_seed="#00e0b6",
            use_material3=True,
        )
        
        # Important: Make page available to all panels
        global_scope = globals()
        global_scope["page"] = page
        
        # Initialize panels - passing the page to each one
        gui_log("info", "Initializing application panels")
        
        # Create a temporary view to hold the loading screen
        # This ensures the page exists before we initialize other panels
        # which might use ListView controls
        page.views.append(
            ft.View(
                route="/",
                controls=[ft.Container(
                    content=ft.Text("Initializing...", color="white"),
                    alignment=ft.alignment.center,
                    expand=True
                )],
                bgcolor="#181818",
            )
        )
        page.update()
        
        # Now initialize the rest of the panels
        self.inbox_panel = create_inbox_panel()
        self.compose_panel = create_compose_panel()
        self.wallet_panel = create_wallet_panel()
        self.browser_panel = create_browser_panel()
        self.settings_panel = create_settings_panel()
        
        # Explicitly initialize the log panel with debugging
        gui_log("info", "Initializing log panel")
        try:
            self.log_panel = create_log_panel()
            gui_log("info", "Log panel initialization successful")
        except Exception as e:
            gui_log("error", f"Error initializing log panel: {str(e)}")
            # Create a simple fallback log panel
            self.log_panel = ft.Container(
                content=ft.Text("Error loading log panel", color="red"),
                padding=20,
                expand=True
            )
        
        # Set up routes
        page.on_route_change = self.route_change
        page.go("/")  # Start with loading view
        
        # Start the daemon
        self._start_background_daemon()

def run_gui():
    """Launch the EvrMail application in a new Flet window"""
    def main(page: ft.Page):
        # Configure the window properties
        page.title = "📬 EvrMail"
        page.window_width = 1080
        page.window_height = 720
        page.window_min_width = 840
        page.window_min_height = 520
        page.theme_mode = "dark"
        page.bgcolor = "#181818"
        page.padding = 0
        
        # Create theme with EvrMail colors
        page.theme = ft.Theme(
            color_scheme_seed="#00e0b6",
            use_material3=True,
        )
        
        # Create and initialize the application
        app = EvrMailApp()
        app.main(page)
    
    # Launch as a desktop application
    ft.app(target=main)

if __name__ == "__main__":
    run_gui()
