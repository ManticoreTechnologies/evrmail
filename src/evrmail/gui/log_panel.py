# evrmail/gui/log_panel.py
import flet as ft
from pathlib import Path
from datetime import datetime
import re
from evrmail.utils import (
    APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG,
    register_callback, set_enabled_categories
)
from evrmail.utils.logger import gui as gui_log

def create_log_panel():
    """Create an enhanced logs panel with category filtering"""
    
    # Create a Container that will hold our log entries
    log_container = ft.Container(
        content=ft.ListView(
            spacing=1,
            auto_scroll=True,
        ),
        expand=True,
        bgcolor="#121212",
        border=ft.border.all(color="#333", width=1),
        border_radius=8,
        padding=ft.padding.only(top=5, bottom=5),
    )
    
    # Legacy log output - using this for internal text processing
    log_output = ft.TextField(
        multiline=True,
        read_only=True,
        value="",
        visible=False,
        text_size=13,
        color="#ffffff",  # Bright white
    )
    
    # Store log entries in memory
    log_entries = []
    
    # Category selection with checkboxes - matched to category colors
    category_colors = {
        APP: "#00BCD4",      # Cyan
        GUI: "#E040FB",      # Magenta/Purple
        DAEMON: "#FFB74D",   # Orange/Yellow
        WALLET: "#4CAF50",   # Green
        CHAIN: "#2196F3",    # Blue
        NETWORK: "#FFFFFF",  # White
        DEBUG: "#9E9E9E"     # Gray
    }
    
    category_row = ft.Row([
        ft.Text("Categories:", color="#ccc"),
        ft.Checkbox(label="App", value=True, fill_color=category_colors[APP], check_color="#000000", data=APP),
        ft.Checkbox(label="GUI", value=True, fill_color=category_colors[GUI], check_color="#000000", data=GUI),
        ft.Checkbox(label="Daemon", value=True, fill_color=category_colors[DAEMON], check_color="#000000", data=DAEMON),
        ft.Checkbox(label="Wallet", value=True, fill_color=category_colors[WALLET], check_color="#000000", data=WALLET),
        ft.Checkbox(label="Chain", value=True, fill_color=category_colors[CHAIN], check_color="#000000", data=CHAIN),
        ft.Checkbox(label="Network", value=True, fill_color=category_colors[NETWORK], check_color="#000000", data=NETWORK),
        ft.Checkbox(label="Debug", value=True, fill_color=category_colors[DEBUG], check_color="#000000", data=DEBUG),
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    # Log level dropdown
    log_level = ft.Dropdown(
        width=180,
        options=[
            ft.dropdown.Option("debug", text="🔍 Debug (All)"),
            ft.dropdown.Option("info", text="ℹ️ Info (Normal)"),
            ft.dropdown.Option("warning", text="⚠️ Warnings"),
            ft.dropdown.Option("error", text="❌ Errors Only"),
            ft.dropdown.Option("critical", text="🔥 Critical Only"),
        ],
        value="info",
        bgcolor="#2A2A2A",
        color="#ffffff",
        border_color="#555",
        focused_border_color="#00e0b6",
        label="Log Level",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    
    # Log filter input
    filter_input = ft.TextField(
        label="Filter logs",
        width=250,
        border_color="#555",
        color="#ffffff",
        bgcolor="#2A2A2A",
        focused_border_color="#00e0b6",
        label_style=ft.TextStyle(color="#aaaaaa"),
        hint_text="Enter text to filter logs",
        hint_style=ft.TextStyle(color="#777777"),
        text_size=13
    )
    
    # Function to filter logs
    def apply_filters(e=None):
        # Check if we're shutting down
        if hasattr(log_output, "page") and getattr(log_output.page, "_closing", False):
            return
            
        # Get selected categories
        selected_categories = []
        try:
            for checkbox in category_row.controls[1:]:  # Skip the "Categories:" text
                if checkbox.value:
                    selected_categories.append(checkbox.data)
            
            # Get log level
            level_value = log_level.value
            level_map = {
                "debug": 0,
                "info": 1,
                "warning": 2,
                "error": 3,
                "critical": 4
            }
            min_level = level_map.get(level_value, 1)
            
            # Get filter text
            filter_text = filter_input.value.lower() if filter_input.value else ""
            
            # Apply filters
            filtered_logs = []
            list_items = []  # Will hold our formatted Text widgets
            
            # Level colors for text
            level_colors = {
                "debug": "#9E9E9E",   # Gray
                "info": "#FFFFFF",    # White
                "warning": "#FFC107", # Yellow/Amber
                "error": "#F44336",   # Red
                "critical": "#D50000" # Dark Red
            }
            
            for entry in log_entries:
                cat, level_name, timestamp, message = entry
                
                # Check category
                if cat not in selected_categories:
                    continue
                    
                # Check level
                level_num = level_map.get(level_name, 0)
                if level_num < min_level:
                    continue
                    
                # Check filter text
                if filter_text and filter_text not in message.lower():
                    continue
                    
                # Format the log entry for plain text output (needed for save function)
                category_labels = {
                    APP: "APP", 
                    GUI: "GUI", 
                    DAEMON: "DAEMON", 
                    WALLET: "WALLET", 
                    CHAIN: "CHAIN", 
                    NETWORK: "NET"
                }
                
                cat_label = category_labels.get(cat, cat)
                formatted_entry = f"[{timestamp}] [{cat_label}] {message}"
                filtered_logs.append(formatted_entry)
                
                # Get category and level colors
                cat_color = category_colors.get(cat, "#FFFFFF")
                level_color = level_colors.get(level_name, "#FFFFFF")
                
                # Get level icon and colors
                level_icons = {
                    "debug": "🔍 DEBUG",
                    "info": "ℹ️ INFO",
                    "warning": "⚠️ WARN",
                    "error": "❌ ERROR",
                    "critical": "🔥 CRIT"
                }
                level_icon = level_icons.get(level_name, "ℹ️ INFO")
                
                # Create row with colored components - using proper color coding based on category and level
                log_row = ft.Row([
                    # Timestamp in gray
                    ft.Text(f"[{timestamp}]", color="#A0A0A0", size=13),
                    # Level indicator with level-based coloring
                    ft.Text(f"{level_icon}", color=level_color, size=13, weight="bold"),
                    # Category label with category-specific color
                    ft.Text(f"[{cat_label}]", color=cat_color, size=13, weight="bold"),
                    # Message with level-based coloring
                    ft.Text(message, color=level_color, size=13, expand=True)
                ], spacing=8)
                
                # Use simple alternating row colors without borders or complex styling
                list_items.append(ft.Container(
                    content=log_row,
                    padding=ft.padding.all(8),
                    bgcolor="#1E1E1E" if len(list_items) % 2 == 0 else "#252525"
                ))
            
            # Update the text field (needed for saving logs)
            log_output.value = "\n".join(filtered_logs)
            
            # Update ListView with our beautifully formatted rows
            if hasattr(log_container, "page") and log_container.page:
                log_container.content.controls = list_items
                log_container.content.update()
                log_container.update()
                print(f"Log panel updated with {len(filtered_logs)} entries")
            else:
                print("Log panel is not attached to page yet")
        except Exception as e:
            print(f"Error in apply_filters: {e}")
            # Make a minimal attempt to update the log output with an error message
            try:
                if hasattr(log_container, "page") and log_container.page:
                    error_container = ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"Error filtering logs: {str(e)}",
                                color="#FF5252",
                                size=14
                            ),
                            ft.Text(
                                f"There are {len(log_entries)} log entries stored.",
                                color="#FFFFFF",
                                size=13
                            )
                        ]),
                        padding=10,
                        bgcolor="#2C2C2C",
                        border_radius=4
                    )
                    log_container.content.controls = [error_container]
                    log_container.content.update()
                    log_container.update()
            except Exception as inner_e:
                print(f"Error displaying error message: {inner_e}")
    
    # Log callback function
    def log_callback(category, level_name, level_num, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Store the log entry
        log_entries.append((category, level_name, timestamp, message))
        
        # Apply filters if the panel is visible and not during shutdown
        try:
            if hasattr(log_container, "page") and log_container.page and not getattr(log_container.page, "_closing", False):
                apply_filters()
        except Exception as e:
            # Ignore event loop closed errors which happen during shutdown
            if "Event loop is closed" not in str(e):
                print(f"Error updating log panel: {e}")
    
    # Clear logs function
    def clear_logs(e=None):
        log_entries.clear()
        try:
            log_output.value = ""
            if hasattr(log_container, "page") and log_container.page:
                log_container.content.controls = []
                log_container.content.update()
                log_container.update()
        except Exception:
            # Silently ignore errors when the control isn't on the page yet
            pass
    
    # Add filter button
    filter_button = ft.ElevatedButton(
        "🔍 Apply Filter",
        on_click=apply_filters,
        bgcolor="#2A2A2A",
        color="white",
        icon=ft.icons.FILTER_ALT,
    )
    
    # Add clear button
    clear_button = ft.ElevatedButton(
        "🧹 Clear Logs",
        on_click=clear_logs,
        bgcolor="#2A2A2A",
        color="white",
        icon=ft.icons.CLEANING_SERVICES,
    )
    
    # Add save button to export logs
    def save_logs(e=None):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path.home() / ".evrmail" / "logs" / "exports"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"evrmail_logs_{timestamp}.txt"
            log_file = log_dir / filename
            
            with open(log_file, "w") as f:
                f.write(log_output.value)
            
            # Show success message
            save_msg.value = f"Logs saved to {log_file}"
            save_msg.visible = True
            save_msg.color = "#4CAF50"  # Green color for success
            save_msg.update()
        except Exception as e:
            save_msg.value = f"Error saving logs: {str(e)}"
            save_msg.visible = True
            save_msg.color = "#FF5252"  # Red color for error
            save_msg.update()
    
    save_button = ft.ElevatedButton(
        "💾 Save Logs",
        on_click=save_logs,
        bgcolor="#2A2A2A",
        color="white",
        icon=ft.icons.SAVE,
    )
    
    # Save message
    save_msg = ft.Text("", color="#00e0b6", visible=False, size=13)
    
    # Create filter bar
    filter_bar = ft.Row([
        ft.Text("Level:", color="#ccc", size=13),
        log_level,
        filter_input,
    ], alignment=ft.MainAxisAlignment.START)
    
    # Create button bar
    button_bar = ft.Row([
        filter_button,
        clear_button,
        save_button,
    ], alignment=ft.MainAxisAlignment.END)
    
    # Create the panel
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("📜 EvrMail Logs", size=24, color="white", weight="bold"),
                category_row,
                ft.Row([
                    filter_bar,
                    ft.Container(width=20),  # Spacer
                    button_bar,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                save_msg,
                log_container,
            ],
            spacing=16,
            expand=True,
        ),
        padding=32,
        expand=True,
    )
    
    # Register for log events when panel is created
    unsubscribe_funcs = []
    for cat in [APP, GUI, DAEMON, WALLET, CHAIN, NETWORK, DEBUG]:
        unsubscribe = register_callback(log_callback, cat)
        unsubscribe_funcs.append(unsubscribe)
    
    # Update categories with active loggers
    def update_categories():
        # Get selected categories
        selected_categories = set()
        for checkbox in category_row.controls[1:]:  # Skip the "Categories:" text
            if checkbox.value:
                selected_categories.add(checkbox.data)
        
        # Update global settings
        set_enabled_categories(selected_categories)
    
    # Connect event handlers
    for checkbox in category_row.controls[1:]:
        checkbox.on_change = lambda e: (update_categories(), apply_filters())
    
    log_level.on_change = apply_filters
    filter_input.on_change = apply_filters
    
    # Add a delayed initialization function
    def delayed_init():
        # Apply filters when panel becomes visible
        try:
            gui_log("info", f"Log panel delayed_init - processing {len(log_entries)} entries")
            # Force a reload of all log entries
            apply_filters()
            gui_log("info", "Log panel initialized successfully")
        except Exception as e:
            error_msg = f"Error in log panel delayed_init: {e}"
            print(error_msg)
            
            # Add a visible error message to the panel
            if hasattr(log_container, "page") and log_container.page:
                error_container = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Error initializing log panel",
                            color="#FF5252",
                            size=16,
                            weight="bold"
                        ),
                        ft.Text(
                            str(e),
                            color="#FFFFFF",
                            size=14
                        ),
                        ft.Text(
                            f"There are {len(log_entries)} log entries stored.",
                            color="#FFFFFF",
                            size=12
                        )
                    ]),
                    padding=16,
                    bgcolor="#2C2C2C",
                    border=ft.border.all(color="#FF5252", width=1),
                    border_radius=8
                )
                log_container.content.controls = [error_container]
                log_container.content.update()
                log_container.update()
    
    # Attach references to the panel
    panel.log_container = log_container
    panel.log_output = log_output
    panel.log_entries = log_entries
    panel.clear_logs = clear_logs
    panel.apply_filters = apply_filters
    panel.delayed_init = delayed_init
    
    # Add cleanup function
    def cleanup():
        for unsub in unsubscribe_funcs:
            unsub()
    
    panel.cleanup = cleanup
    
    return panel
