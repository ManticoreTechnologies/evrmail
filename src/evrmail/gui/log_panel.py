# evrmail/gui/log_panel.py
import flet as ft
from pathlib import Path
from datetime import datetime
import re
import json
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
    
    # Store log entries in memory with expanded details
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
            list_items = []  # Will hold our formatted log entries
            
            # Level colors for text
            level_colors = {
                "debug": "#9E9E9E",   # Gray
                "info": "#FFFFFF",    # White
                "warning": "#FFC107", # Yellow/Amber
                "error": "#F44336",   # Red
                "critical": "#D50000" # Dark Red
            }
            
            for entry in log_entries:
                cat, level_name, timestamp, message, details = entry if len(entry) >= 5 else (*entry, None)
                
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
                    NETWORK: "NET",
                    DEBUG: "DEBUG"
                }
                
                cat_label = category_labels.get(cat, cat)
                level_icon = {
                    "debug": "🔍",
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🔥"
                }.get(level_name, "ℹ️")
                
                formatted_entry = f"[{timestamp}] {level_icon} [{cat_label}] {message}"
                filtered_logs.append(formatted_entry)
                
                # Create expandable log entry
                list_items.append(
                    create_expandable_log_entry(timestamp, cat, level_name, message, details)
                )
            
            # Update the text field (needed for saving logs)
            log_output.value = "\n".join(filtered_logs)
            
            # Update ListView with our beautifully formatted rows
            if hasattr(log_container, "page") and log_container.page:
                log_container.content.controls = list_items if list_items else [
                    ft.Text("No logs match the current filter criteria", 
                           color="#A0A0A0", 
                           italic=True,
                           text_align=ft.TextAlign.CENTER)
                ]
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
                                "Error filtering logs:",
                                color="#FF5252",
                                size=16,
                                weight="bold",
                                selectable=True
                            ),
                            ft.Text(
                                str(e),
                                color="#FFFFFF",
                                size=14,
                                selectable=True
                            ),
                            ft.Text(
                                f"There are {len(log_entries)} log entries stored.",
                                color="#FFFFFF",
                                size=12,
                                selectable=True
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
            except Exception as inner_e:
                print(f"Error displaying error message: {inner_e}")
    
    # Log callback function
    def log_callback(category, level_name, level_num, message, details=None):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Attempt to extract detailed information
        extracted_details = extract_details(category, message, details)
        
        # Store the log entry with details
        log_entries.append((category, level_name, timestamp, message, extracted_details))
        
        # Apply filters if the panel is visible and not during shutdown
        try:
            if hasattr(log_container, "page") and log_container.page and not getattr(log_container.page, "_closing", False):
                apply_filters()
        except Exception as e:
            # Ignore event loop closed errors which happen during shutdown
            if "Event loop is closed" not in str(e):
                print(f"Error updating log panel: {e}")
    
    # Extract detailed information from log messages
    def extract_details(category, message, details=None):
        # If details were explicitly provided, use them
        if details:
            # If it's a JSON string, parse it
            if isinstance(details, str) and details.strip().startswith('{'):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    pass
            return details
            
        extracted = {}
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check if message contains JSON - first try to extract JSON blob
        json_match = re.search(r'({.*})', message)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                if isinstance(json_data, dict):
                    extracted.update(json_data)
            except json.JSONDecodeError:
                pass
        
        # Try to extract useful information from logs based on category
        if category == WALLET:
            # Extract wallet information - addresses, transactions, balances
            if "address" in message.lower():
                # Try to extract address and balance
                address_match = re.search(r'([A-Za-z0-9]{30,})', message)
                if address_match:
                    extracted["address"] = address_match.group(1)
            elif "balance" in message.lower():
                # Try to extract balance details
                amount_match = re.search(r'([\d\.]+)\s*([A-Z]{3,})?', message)
                if amount_match:
                    extracted["amount"] = amount_match.group(1)
                    if amount_match.group(2):
                        extracted["asset"] = amount_match.group(2)
            
            # Add more specific wallet patterns
            tx_match = re.search(r'transaction:?\s*([a-f0-9]{64})', message, re.IGNORECASE)
            if tx_match:
                extracted["transaction_id"] = tx_match.group(1)
                extracted["explorer_link"] = f"https://explorer.evrmore.org/tx/{tx_match.group(1)}"
        
        elif category == DAEMON:
            # Extract daemon information - startup, stopping, errors
            if "starting" in message.lower():
                extracted["status"] = "Starting"
                extracted["timestamp"] = timestamp
            elif "stopping" in message.lower() or "shut" in message.lower():
                extracted["status"] = "Stopping"
                extracted["timestamp"] = timestamp
            
            # Extract any JSON data from daemon messages
            json_pattern = re.search(r'JSON\s+.*?:\s+({.*})', message)
            if json_pattern:
                try:
                    json_data = json.loads(json_pattern.group(1))
                    if isinstance(json_data, dict):
                        extracted["data"] = json_data
                except json.JSONDecodeError:
                    pass
                
            # Extract error information
            if "error" in message.lower() or "fail" in message.lower():
                error_match = re.search(r'(?:error|fail\w+)[:\s]+(.+?)(?:$|\.)', message, re.IGNORECASE)
                if error_match:
                    extracted["error"] = error_match.group(1).strip()
        
        elif category == CHAIN:
            # Extract blockchain information - blocks, transactions
            tx_match = re.search(r'TX:?\s*([a-f0-9]{64})', message)
            if tx_match:
                extracted["txid"] = tx_match.group(1)
                extracted["explorer_link"] = f"https://explorer.evrmore.org/tx/{tx_match.group(1)}"
            
            # Extract UTXO information
            utxo_match = re.search(r'UTXO\s+([a-f0-9]+):(\d+)', message)
            if utxo_match:
                extracted["txid"] = utxo_match.group(1)
                extracted["vout"] = utxo_match.group(2)
                extracted["explorer_link"] = f"https://explorer.evrmore.org/tx/{utxo_match.group(1)}"
                
            # Extract block information
            if "block" in message.lower():
                block_count_match = re.search(r'with\s+(\d+)\s+transactions', message)
                if block_count_match:
                    extracted["transaction_count"] = block_count_match.group(1)
                
                # Extract block hash or height
                block_hash_match = re.search(r'block\s+hash:?\s+([a-f0-9]{64})', message, re.IGNORECASE)
                if block_hash_match:
                    extracted["block_hash"] = block_hash_match.group(1)
                    extracted["explorer_link"] = f"https://explorer.evrmore.org/block/{block_hash_match.group(1)}"
                
                height_match = re.search(r'block\s+(?:height|number):?\s+(\d+)', message, re.IGNORECASE)
                if height_match:
                    extracted["block_height"] = height_match.group(1)
            
        elif category == NETWORK:
            # Extract network information - connections, peers
            if "connected" in message.lower():
                extracted["status"] = "Connected"
            elif "disconnected" in message.lower():
                extracted["status"] = "Disconnected"
                
            # Extract peer information
            peer_match = re.search(r'peer:?\s+(\S+)', message, re.IGNORECASE)
            if peer_match:
                extracted["peer"] = peer_match.group(1)
            
            # Extract IP address information
            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::(\d+))?', message)
            if ip_match:
                extracted["ip_address"] = ip_match.group(1)
                if ip_match.group(2):
                    extracted["port"] = ip_match.group(2)
                
        # Return None if no details were extracted
        return extracted if extracted else None
    
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

# Function to create expandable log entry with details
def create_expandable_log_entry(timestamp, cat, level_name, message, details=None):
    """Create an expandable log entry with detailed information"""
    # Get level icon and colors
    level_icons = {
        "debug": "🔍 DEBUG",
        "info": "ℹ️ INFO",
        "warning": "⚠️ WARN",
        "error": "❌ ERROR",
        "critical": "🔥 CRIT"
    }
    level_icon = level_icons.get(level_name, "ℹ️ INFO")
    
    # Get category and level colors
    category_colors = {
        APP: "#00BCD4",      # Cyan
        GUI: "#E040FB",      # Magenta/Purple
        DAEMON: "#FFB74D",   # Orange/Yellow
        WALLET: "#4CAF50",   # Green
        CHAIN: "#2196F3",    # Blue
        NETWORK: "#FFFFFF",  # White
        DEBUG: "#9E9E9E",    # Gray
    }
    
    level_colors = {
        "debug": "#9E9E9E",    # Gray
        "info": "#FFFFFF",     # White
        "warning": "#FFC107",  # Amber
        "error": "#F44336",    # Red
        "critical": "#FF5722"  # Deep Orange
    }
    
    cat_color = category_colors.get(cat, "#FFFFFF")
    level_color = level_colors.get(level_name, "#FFFFFF")
    
    # Function to copy text to clipboard
    def copy_to_clipboard(text, e=None):
        if hasattr(ft.page, "set_clipboard"):
            ft.page.set_clipboard(text)
            ft.page.show_snackbar(ft.SnackBar(content=ft.Text(f"Copied: {text[:20]}...")))
        
    # Create details container that will be hidden/shown
    details_container = ft.Container(
        content=ft.Column([], spacing=5),
        padding=ft.padding.only(left=20, top=5, right=10, bottom=5),
        bgcolor="#1A1A1A",
        border_radius=5,
        visible=False  # Initially hidden
    )
    
    # Toggle expansion function
    def toggle_expansion(e):
        details_container.visible = not details_container.visible
        e.control.icon = ft.icons.EXPAND_LESS if details_container.visible else ft.icons.EXPAND_MORE
        entry_container.update()
        
    # Create details list
    details_list = []
    
    # Create details from dictionary or string
    if isinstance(details, dict):
        for key, value in details.items():
            # Format the value nicely
            if isinstance(value, dict):
                # Format nested dictionary with indentation
                try:
                    formatted_value = json.dumps(value, indent=2)
                    details_list.append(
                        ft.Column([
                            ft.Text(f"{key}:", color="#A0A0A0", size=12, selectable=True),
                            ft.Container(
                                content=ft.Text(
                                    formatted_value,
                                    color="#00E676",  # Light green for JSON
                                    size=12, 
                                    selectable=True,
                                    font_family="Consolas,monospace"
                                ),
                                margin=ft.margin.only(left=15),
                                padding=8,
                                bgcolor="#1A1A1A",
                                border_radius=5,
                                border=ft.border.all(color="#333333", width=1),
                            )
                        ])
                    )
                except Exception:
                    # Fallback if JSON formatting fails
                    details_list.append(
                        ft.Row([
                            ft.Text(f"{key}:", color="#A0A0A0", size=12, selectable=True),
                            ft.Text(str(value), color="#FFFFFF", size=12, selectable=True, expand=True)
                        ], spacing=10)
                    )
            elif "explorer_link" in key or key == "explorer_link":
                # Special handling for explorer links - use gesture detector
                details_list.append(
                    ft.Row([
                        ft.Text(f"{key}:", color="#A0A0A0", size=12, selectable=True),
                        ft.Container(
                            content=ft.Text(
                                str(value),
                                color="#64B5F6",  # Light blue for links
                                size=12, 
                                selectable=True,
                                expand=True,
                                tooltip="Click to copy to clipboard"
                            ),
                            on_click=lambda e, v=value: copy_to_clipboard(v, e)
                        )
                    ], spacing=10)
                )
            elif "address" in key or "txid" in key or "hash" in key:
                # Special formatting for blockchain identifiers - use gesture detector
                details_list.append(
                    ft.Row([
                        ft.Text(f"{key}:", color="#A0A0A0", size=12, selectable=True),
                        ft.Container(
                            content=ft.Text(
                                str(value),
                                color="#FFD54F",  # Amber for blockchain IDs
                                size=12, 
                                selectable=True,
                                expand=True,
                                tooltip="Click to copy to clipboard"
                            ),
                            on_click=lambda e, v=value: copy_to_clipboard(v, e)
                        )
                    ], spacing=10)
                )
            else:
                # Regular key-value display
                details_list.append(
                    ft.Row([
                        ft.Text(f"{key}:", color="#A0A0A0", size=12, selectable=True),
                        ft.Text(
                            str(value), 
                            color="#FFFFFF", 
                            size=12, 
                            selectable=True,
                            expand=True
                        )
                    ], spacing=10)
                )
    else:
        # If no extracted details but it's an expandable entry,
        # show a message that we can extract details on demand
        details_list.append(
            ft.Text(
                "No structured data available.",
                color="#999999",
                italic=True,
                size=12
            )
        )
    
    # Update the details container with our details
    details_container.content.controls = details_list
    
    # Create the complete entry
    entry_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    # Timestamp in gray
                    ft.Text(f"[{timestamp}]", color="#A0A0A0", size=13, selectable=True),
                    # Level indicator with level-based coloring
                    ft.Text(f"{level_icon}", color=level_color, size=13, weight="bold", selectable=True),
                    # Category label with category-specific color
                    ft.Text(f"[{cat}]", color=cat_color, size=13, weight="bold", selectable=True),
                    # Message with level-based coloring
                    ft.Text(message, color=level_color, size=13, expand=True, selectable=True),
                    # Expand/collapse icon - always show for enhanced UX
                    ft.IconButton(
                        icon=ft.icons.EXPAND_MORE,
                        icon_color="#A0A0A0",
                        icon_size=18,
                        on_click=toggle_expansion
                    )
                ], spacing=8),
                details_container
            ],
            spacing=0,
            tight=True
        ),
        padding=ft.padding.only(top=5, bottom=5, left=8, right=8),
        border_radius=5
    )
    
    return entry_container
