#!/usr/bin/env python
# src/scripts/evrmail_logs.py

"""
📋 EvrMail Logs Viewer

This is a standalone utility to view and manage EvrMail logs.
It provides a GUI for filtering, searching, and exporting logs.
"""

import flet as ft
import sys
import os
from pathlib import Path
import argparse
import logging

# Add the parent directory to the path so we can import our modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Now we can import from evrmail directly
from evrmail.utils.logger import (
    configure_logging, APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG
)
from evrmail.gui.log_panel import create_log_panel

def run_logs_app(page: ft.Page):
    """Run the logs app in a Flet window"""
    # Configure the window properties
    page.title = "📋 EvrMail Logs"
    page.window_width = 960
    page.window_height = 720
    page.window_min_width = 800
    page.window_min_height = 520
    page.theme_mode = "dark"
    page.bgcolor = "#181818"
    page.padding = 0
    
    # Create theme with EvrMail colors
    page.theme = ft.Theme(
        color_scheme_seed="#00e0b6",
        use_material3=True,
    )
    
    # Create app bar
    app_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("📋 EvrMail Logs", size=20, color="white", weight="bold"),
                ft.Container(expand=True),  # Spacer
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    on_click=lambda _: page.window_close()
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=10,
        bgcolor="#202020",
        border_radius=ft.border_radius.only(top_left=8, top_right=8)
    )
    
    # Create the log panel
    log_panel = create_log_panel()
    
    # Main content column
    main_content = ft.Column(
        [
            app_bar,
            log_panel
        ],
        expand=True
    )
    
    # Add content to the page
    page.add(main_content)
    
    # Initialize the log panel
    if hasattr(log_panel, "delayed_init"):
        log_panel.delayed_init()

def main():
    """Main entry point for the logs application"""
    parser = argparse.ArgumentParser(description="EvrMail Logs Viewer")
    parser.add_argument(
        "--level", 
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the log level (default: info)"
    )
    parser.add_argument(
        "--category", 
        choices=["all", "app", "gui", "daemon", "wallet", "chain", "network"],
        action="append",
        help="Log categories to display (can be used multiple times, default: all)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    log_level = level_map.get(args.level, logging.INFO)
    
    # Initialize logging
    configure_logging(level=log_level)
    
    # Launch the app
    ft.app(target=run_logs_app)

if __name__ == "__main__":
    main() 