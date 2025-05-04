import flet as ft
from evrmail.wallet.addresses import get_all_addresses
from evrmail.wallet.utils import load_all_wallet_keys, calculate_balances
from pathlib import Path
import os
import threading
import time
from threading import Timer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from evrmail import rpc_client
from evrmail.commands.send.send_evr import send_evr_tx
from evrmail.gui.balance_panel import create_balance_tab
from evrmail.gui.utxo_panel import create_utxo_panel

# Constants
PAGE_SIZE = 10

# Global page reference that will be used across the module
_PAGE_REF = {"page": None}

def get_page():
    """Return the global page reference or attempt to get it from globals"""
    if _PAGE_REF["page"] is not None:
        return _PAGE_REF["page"]
    
    # Try to get from globals as fallback
    if 'page' in globals():
        _PAGE_REF["page"] = globals()['page']
        return _PAGE_REF["page"]
    
    # Last resort, look through all frame globals
    import inspect
    for frame in inspect.stack():
        if 'page' in frame.frame.f_globals:
            _PAGE_REF["page"] = frame.frame.f_globals['page']
            return _PAGE_REF["page"]
            
    # Nothing found
    return None

class WalletFolderHandler(FileSystemEventHandler):
    def __init__(self, reload_func):
        super().__init__()
        self.reload_func = reload_func
        self.timer = None

    def on_modified(self, event):
        if event.src_path.endswith(".json"):
            if self.timer:
                self.timer.cancel()
            self.timer = Timer(0.3, self.reload_func)  # 300ms delay
            self.timer.start()

def start_wallet_folder_monitor(reload_func):
    wallets_path = os.path.expanduser("~/.evrmail/wallets")
    if not os.path.exists(wallets_path):
        return

    observer = Observer()
    handler = WalletFolderHandler(reload_func)
    observer.schedule(handler, path=wallets_path, recursive=False)
    observer.start()

    # Keep running in the background thread
    thread = threading.Thread(target=observer.join, daemon=True)
    thread.start()

def send_asset_core(
    from_addresses: list,
    to_address: str,
    asset_name: str,
    amount: float,
    fee_rate: float = 0.01,
    dry_run: bool = False,
    debug: bool = False,
    raw: bool = False
) -> str:
    """
    Pure function to send an asset programmatically.
    """
    fee_rate_sats = int(fee_rate * 1e8)
    asset_qty = int(amount * 1e8)  # Asset amounts are integerized (1 EVR = 1e8 satoshis)

    # 📦 Build transaction
    tx, txid = create_send_asset_transaction(
        from_addresses,
        to_address,
        asset_name,
        asset_qty,
        fee_rate=fee_rate_sats
    )

    if dry_run:
        # 🧪 Testmempoolaccept
        result = rpc_client.testmempoolaccept([tx])
        status = result[0] if result else {}
        if status.get("txid") == txid and status.get("allowed"):
            return txid
        else:
            raise Exception(f"Dry-run rejected: {status.get('reject-reason', 'unknown reason')}")
    else:
        # 📡 Broadcast real transaction
        tx_hash = rpc_client.sendrawtransaction(tx)
        return tx_hash

def create_wallet_panel():
    """Create the wallet panel using Flet components"""
    
    # Try to initialize page reference early
    try:
        global page
        if 'page' in globals():
            _PAGE_REF["page"] = page
            print("✅ Page reference initialized early in create_wallet_panel")
    except Exception as e:
        print(f"⚠️ Early page initialization failed: {str(e)}")
    
    # State management
    state = {
        "current_page": 0,
        "all_addresses": get_all_addresses(True),
        "filtered_addresses": [],
        "show_labeled_only": False,
        "total_pages": 1,
        "load_page_func": None,  # Store the load_page function here
        "page": None,  # Will be set when the panel is added to the page
    }
    
    # Filter labeled addresses
    state["filtered_addresses"] = [entry for entry in state["all_addresses"] 
                                  if entry.get("friendly_name") and 
                                  not entry["friendly_name"].startswith("address_")]
    
    # Calculate total pages
    def calculate_total_pages():
        addresses_to_use = state["filtered_addresses"] if state["show_labeled_only"] else state["all_addresses"]
        state["total_pages"] = max(1, (len(addresses_to_use) + PAGE_SIZE - 1) // PAGE_SIZE)
        return state["total_pages"]
    
    calculate_total_pages()
    
    # ---- ADDRESS TAB ----
    def create_address_tab():
        # Address table
        address_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Index", weight="bold", color="#00e0b6")),
                ft.DataColumn(ft.Text("Label", weight="bold", color="#00e0b6")),
                ft.DataColumn(ft.Text("Address", weight="bold", color="#00e0b6")),
                ft.DataColumn(ft.Text("Path", weight="bold", color="#00e0b6")),
                ft.DataColumn(ft.Text("Public Key", weight="bold", color="#00e0b6")),
                ft.DataColumn(ft.Text("Private Key", weight="bold", color="#00e0b6")),
            ],
            border=ft.border.all(color="#333", width=1),
            border_radius=12,
            vertical_lines=ft.border.BorderSide(1, "#333"),
            horizontal_lines=ft.border.BorderSide(1, "#333"),
            heading_row_color=ft.colors.with_opacity(0.2, "#202124"),
            heading_row_height=50,
            data_row_min_height=45,
            width=10000,  # Force full width
            data_row_color={"hovered": "#1f2937"},
            show_checkbox_column=False,
        )
        
        # Label filter checkbox
        label_filter = ft.Checkbox(
            label="Only show user-labeled addresses",
            value=state["show_labeled_only"],
            fill_color="#00e0b6",
        )
        
        # Stats label
        stats_label = ft.Text(
            value="Loading addresses...",
            color="#ccc",
            weight="medium",
            text_align=ft.TextAlign.CENTER,
            size=14,
        )
        
        # Pagination controls
        first_page_btn = ft.ElevatedButton(
            "⏮ First", 
            disabled=True,
            style=ft.ButtonStyle(
                color={"": "white", "disabled": "#555"},
                bgcolor={"": "#1f1f1f", "disabled": "#111"}
            ),
        )
        
        prev_btn = ft.ElevatedButton(
            "⬅ Prev", 
            disabled=True,
            style=ft.ButtonStyle(
                color={"": "white", "disabled": "#555"},
                bgcolor={"": "#1f1f1f", "disabled": "#111"}
            ),
        )
        
        page_info = ft.Text("Page 1 / 1", color="#ccc", weight="bold")
        
        next_btn = ft.ElevatedButton(
            "Next ➡",
            style=ft.ButtonStyle(
                color={"": "white", "disabled": "#555"},
                bgcolor={"": "#1f1f1f", "disabled": "#111"}
            ),
        )
        
        last_page_btn = ft.ElevatedButton(
            "Last ⏭",
            style=ft.ButtonStyle(
                color={"": "white", "disabled": "#555"},
                bgcolor={"": "#1f1f1f", "disabled": "#111"}
            ),
        )
        
        pagination_row = ft.Row(
            [first_page_btn, prev_btn, page_info, next_btn, last_page_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        def load_page(page_num: int):
            addresses_to_use = state["filtered_addresses"] if state["show_labeled_only"] else state["all_addresses"]
            total_pages = max(1, (len(addresses_to_use) + PAGE_SIZE - 1) // PAGE_SIZE)
            page_num = max(0, min(page_num, total_pages - 1))
            
            start = page_num * PAGE_SIZE
            end = min(start + PAGE_SIZE, len(addresses_to_use))
            
            # Clear existing rows
            address_table.rows.clear()
            
            # Get current page reference
            current_page = get_page()
            
            # Add new rows with direct handlers for copying
            for entry in addresses_to_use[start:end]:
                address = entry.get("address", "")
                
                # Define a click handler with closure over current values
                def make_click_handler(addr, pg):
                    def click_handler(e):
                        try:
                            # Try direct copying with event's page first
                            if hasattr(e, "page") and hasattr(e.page, "clipboard"):
                                e.page.clipboard.set_text(addr)
                                e.page.snack_bar = ft.SnackBar(
                                    ft.Text(f"Copied: {addr}"),
                                    bgcolor="#00e0b6",
                                    action="OK",
                                    open=True
                                )
                                e.page.update()
                                print(f"✅ Direct copy with event.page successful: {addr[:10]}...")
                                return
                        except Exception as ex:
                            print(f"First copy attempt failed: {str(ex)}")
                        
                        # Fallback: Show a dialog with the address
                        try:
                            # Use the event's page, get_page() function, or any available page
                            dialog_page = None
                            if hasattr(e, "page"):
                                dialog_page = e.page
                            elif pg is not None:
                                dialog_page = pg
                            elif get_page() is not None:
                                dialog_page = get_page()
                            elif 'page' in globals():
                                dialog_page = globals()['page']
                            
                            if dialog_page:
                                # Show a dialog with the address for easy copying
                                dialog_page.dialog = ft.AlertDialog(
                                    title=ft.Text("Copy Address", color="#00e0b6"),
                                    content=ft.Column([
                                        ft.Text("Please copy this address manually:"),
                                        ft.Text(
                                            addr,
                                            text_align=ft.TextAlign.CENTER,
                                            weight="bold",
                                            size=14,
                                            bgcolor="#111111",
                                            color="#00e0b6",
                                            width=400,
                                            selectable=True,
                                            style=ft.TextStyle(font_family="monospace"),
                                        ),
                                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                    actions=[
                                        ft.TextButton("Close", on_click=lambda e: close_copy_dialog(e)),
                                    ],
                                    actions_alignment=ft.MainAxisAlignment.END,
                                    bgcolor="#202020",
                                )
                                dialog_page.dialog.open = True
                                dialog_page.update()
                                print(f"✅ Showed address dialog for: {addr[:10]}...")
                                
                                # Define the dialog close function
                                def close_copy_dialog(e):
                                    e.page.dialog.open = False
                                    e.page.update()
                            else:
                                print("❌ No page reference available to show dialog")
                        except Exception as ex:
                            print(f"❌ Dialog fallback also failed: {str(ex)}")
                    return click_handler
                
                # Create row with the handler
                click_handler = make_click_handler(address, current_page)
                
                address_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(entry.get("index", "")))),
                            ft.DataCell(ft.Text(str(entry.get("friendly_name", "")), color="#00e0b6" if entry.get("friendly_name") else "white")),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Text(
                                            address,  # Show the full address
                                            expand=True,
                                            color="#00e0b6",
                                            selectable=True,
                                            style=ft.TextStyle(font_family="monospace", size=12),
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.COPY,
                                            tooltip="Copy address",
                                            icon_color="#00e0b6",
                                            on_click=click_handler,
                                        )
                                    ],
                                    spacing=5,
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ),
                            ft.DataCell(ft.Text(entry.get("path", ""))),
                            ft.DataCell(ft.Text("************", color="#777")),
                            ft.DataCell(ft.Text("************", color="#777")),
                        ],
                        on_select_changed=click_handler,
                    )
                )
            
            # Update state and UI
            state["current_page"] = page_num
            stats_label.value = f"Total Addresses: {len(addresses_to_use)} | Page {page_num + 1} of {total_pages}"
            page_info.value = f"Page {page_num + 1} / {total_pages}"
            
            # Update button states
            first_page_btn.disabled = page_num == 0
            prev_btn.disabled = page_num == 0
            next_btn.disabled = page_num >= total_pages - 1
            last_page_btn.disabled = page_num >= total_pages - 1
            
            # Update UI
            address_table.update()
            stats_label.update()
            page_info.update()
            first_page_btn.update()
            prev_btn.update()
            next_btn.update()
            last_page_btn.update()
        
        def handle_filter_change(e):
            state["show_labeled_only"] = label_filter.value
            calculate_total_pages()
            load_page(0)
        
        # Set up event handlers
        label_filter.on_change = handle_filter_change
        first_page_btn.on_click = lambda _: load_page(0)
        prev_btn.on_click = lambda _: load_page(state["current_page"] - 1)
        next_btn.on_click = lambda _: load_page(state["current_page"] + 1)
        last_page_btn.on_click = lambda _: load_page(state["total_pages"] - 1)
        
        # Layout with card-like container
        header_row = ft.Row(
            [
                ft.Text("Derived Addresses", size=18, weight="bold", color="#00e0b6"),
                ft.Container(expand=True),
                label_filter,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        address_tab = ft.Container(
            content=ft.Column(
                [
                    header_row,
                    stats_label,
                    ft.Container(
                        content=address_table,
                        expand=True,
                        padding=ft.padding.symmetric(vertical=10),
                    ),
                    pagination_row,
                ],
                spacing=15,
                expand=True,
            ),
            padding=15,
            expand=True,
            border_radius=12,
            bgcolor="#121212",
        )
        
        # Set up refresh function for wallet folder monitor
        def refresh_addresses():
            print("[WalletPanel] 🔥 Reloading addresses from disk...")
            # Reread addresses
            state["all_addresses"] = get_all_addresses(True)
            state["filtered_addresses"] = [
                entry for entry in state["all_addresses"] 
                if entry.get("friendly_name") and not entry["friendly_name"].startswith("address_")
            ]
            calculate_total_pages()
            load_page(min(state["current_page"], state["total_pages"] - 1))
        
        # Start wallet folder monitor
        start_wallet_folder_monitor(refresh_addresses)
        
        # Store load_page in state for access from delayed_init
        state["load_page_func"] = load_page
        
        return address_tab
    
    # ---- KEYS TAB ----
    def create_keys_tab():
        wallet_data = load_all_wallet_keys()
        
        # Keys table
        keys_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Wallet", weight=ft.FontWeight.BOLD, color="#00e0b6")),
                ft.DataColumn(ft.Text("Mnemonic", weight=ft.FontWeight.BOLD, color="#00e0b6")),
                ft.DataColumn(ft.Text("Passphrase", weight=ft.FontWeight.BOLD, color="#00e0b6")),
                ft.DataColumn(ft.Text("Seed", weight=ft.FontWeight.BOLD, color="#00e0b6")),
                ft.DataColumn(ft.Text("Extended Public Key", weight=ft.FontWeight.BOLD, color="#00e0b6")),
                ft.DataColumn(ft.Text("Extended Private Key", weight=ft.FontWeight.BOLD, color="#00e0b6")),
            ],
            border=ft.border.all(color="#333", width=1),
            border_radius=12,
            vertical_lines=ft.border.BorderSide(1, "#333"),
            horizontal_lines=ft.border.BorderSide(1, "#333"),
            heading_row_color=ft.colors.with_opacity(0.2, "#202124"),
            heading_row_height=50,
            data_row_min_height=45,
            width=10000,  # Force full width
            data_row_color={"hovered": "#1f2937"},
            show_checkbox_column=False,
        )
        
        # Add rows to keys table
        for wallet_name, keys in wallet_data.items():
            keys_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(wallet_name, color="#00e0b6", weight="bold")),
                        ft.DataCell(ft.Text("************", color="#777")),
                        ft.DataCell(ft.Text("************", color="#777")),
                        ft.DataCell(ft.Text("************", color="#777")),
                        ft.DataCell(ft.Text("************", color="#777")),
                        ft.DataCell(ft.Text("************", color="#777")),
                    ],
                    on_select_changed=lambda e, name=wallet_name: show_key_details(name),
                )
            )
        
        def show_key_details(wallet_name):
            # In a real app, this would show a dialog with the actual keys
            # For security reasons, we just show a message
            
            # Get page safely
            if "page" in state and state["page"] is not None:
                current_page = state["page"]
            else:
                # Try to access global page as a fallback
                global page
                if 'page' in globals():
                    current_page = page
                    # Update state for future use
                    state["page"] = page
                else:
                    print("Warning: page object not available for dialog operation")
                    return
            
            current_page.dialog = ft.AlertDialog(
                title=ft.Text(f"🔑 {wallet_name} Keys", color="#00e0b6"),
                content=ft.Text("Key details would be shown here.\nFor security reasons, they are not displayed in this implementation."),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: close_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#202020",
            )
            current_page.dialog.open = True
            current_page.update()
        
        def close_dialog():
            # Get page safely
            if "page" in state and state["page"] is not None:
                current_page = state["page"]
            else:
                # Try to access global page as a fallback
                global page
                if 'page' in globals():
                    current_page = page
                    # Update state for future use
                    state["page"] = page
                else:
                    print("Warning: page object not available for dialog operation")
                    return
                
            current_page.dialog.open = False
            current_page.update()
        
        # Layout with card-like container
        keys_tab = ft.Container(
            content=ft.Column(
                [
                    ft.Text("🔑 Key Management", size=18, weight="bold", color="#00e0b6"),
                    ft.Container(height=15),
                    ft.Container(
                        content=keys_table,
                        expand=True,
                    ),
                ],
                spacing=5,
                expand=True,
            ),
            padding=15,
            expand=True,
            border_radius=12,
            bgcolor="#121212",
        )
        
        return keys_tab
    
    # ---- SEND TAB ----
    def create_send_tab():
        # Calculate balances
        balances = calculate_balances()
        
        # Asset dropdown
        asset_dropdown = ft.Dropdown(
            label="Select Asset",
            hint_text="Choose asset to send",
            options=[
                ft.dropdown.Option("EVR")
            ] + [
                ft.dropdown.Option(asset_name) for asset_name in balances["assets"].keys()
            ],
            width=400,
            border_color="#00e0b6",
            focused_border_color="#00e0b6",
            focused_color="#00e0b6",
        )
        
        # Input fields
        address_field = ft.TextField(
            label="Destination Address",
            hint_text="Enter recipient address",
            border_color="#3ea6ff",
            expand=True,
            focused_border_color="#00e0b6",
        )
        
        amount_field = ft.TextField(
            label="Amount",
            hint_text="Enter amount to send",
            border_color="#3ea6ff",
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            focused_border_color="#00e0b6",
        )
        
        # Dry run checkbox
        dry_run_checkbox = ft.Checkbox(
            label="🧪 Dry-Run Only (simulate, no broadcast)",
            value=False,
            fill_color="#00e0b6",
        )
        
        # Status message
        status_text = ft.Text(
            value="",
            color="#3ea6ff",
            selectable=True,
        )
        
        # Send button
        send_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SEND),
                    ft.Text("Send Transaction", size=16, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            bgcolor="#00e0b6",
            color="black",
            width=250,
            height=48,
        )
        
        def handle_send(e):
            asset = asset_dropdown.value or "EVR"
            address = address_field.value or ""
            amount_str = amount_field.value or ""
            dry_run = dry_run_checkbox.value
            
            # Validate inputs
            if not address or not amount_str:
                status_text.value = "❌ Please fill in all fields"
                status_text.color = "red"
                status_text.update()
                return
            
            try:
                amount = float(amount_str)
            except ValueError:
                status_text.value = "❌ Amount must be a number"
                status_text.color = "red"
                status_text.update()
                return
            
            # Get page safely
            if "page" in state and state["page"] is not None:
                current_page = state["page"]
            else:
                # Try to access global page as a fallback
                global page
                if 'page' in globals():
                    current_page = page
                    # Update state for future use
                    state["page"] = page
                else:
                    print("Warning: page object not available for dialog operation")
                    return
            
            # Confirm dialog
            current_page.dialog = ft.AlertDialog(
                title=ft.Text("Confirm Transaction", color="#00e0b6"),
                content=ft.Column([
                    ft.Text(f"Send {amount} {asset}"),
                    ft.Text(f"To: {address}"),
                    ft.Text(f"{'(Dry-Run only)' if dry_run else '(Will broadcast)'}", color="orange" if dry_run else "#4caf50"),
                ]),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.ElevatedButton(
                        "Confirm",
                        on_click=lambda e: execute_send(asset, address, amount, dry_run),
                        bgcolor="#00e0b6",
                        color="black",
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#202020",
            )
            current_page.dialog.open = True
            current_page.update()
        
        def close_dialog(e=None):
            # Get page safely
            if "page" in state and state["page"] is not None:
                current_page = state["page"]
            else:
                # Try to access global page as a fallback
                global page
                if 'page' in globals():
                    current_page = page
                    # Update state for future use
                    state["page"] = page
                else:
                    print("Warning: page object not available for dialog operation")
                    return
                
            current_page.dialog.open = False
            current_page.update()
        
        def execute_send(asset, address, amount, dry_run):
            close_dialog()
            
            # Show sending status
            status_text.value = "⏳ Processing transaction..."
            status_text.color = "orange"
            status_text.update()
            
            try:
                if asset == "EVR":
                    # Send EVR
                    from evrmail.wallet import addresses
                    result = send_evr_tx(
                        address,
                        addresses.get_all_addresses(),
                        amount,
                        dry_run=dry_run,
                        debug=False,
                        raw=False
                    )
                else:
                    # Send Asset
                    result = send_asset_core(
                        from_addresses=None,
                        to_address=address,
                        asset_name=asset,
                        amount=amount,
                        fee_rate=0.01,
                        dry_run=dry_run,
                        debug=False,
                        raw=False
                    )
                
                if dry_run:
                    status_text.value = f"🧪 Simulated {amount} {asset} to {address}\nTXID: {result}"
                else:
                    status_text.value = f"✅ Sent {amount} {asset} to {address}\nTXID: {result}"
                status_text.color = "#4caf50"
                status_text.update()
                
            except Exception as e:
                status_text.value = f"❌ Failed to send: {str(e)}"
                status_text.color = "red"
                status_text.update()
        
        # Set up event handlers
        send_button.on_click = handle_send
        
        # Layout with card-like container
        send_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("📤 Send EVR or Assets", size=18, weight="bold", color="#00e0b6"),
                    ft.Divider(height=1, color="#333"),
                    ft.Container(height=10),
                    asset_dropdown,
                    address_field,
                    amount_field,
                    dry_run_checkbox,
                    ft.Container(
                        content=status_text,
                        margin=ft.margin.only(top=10, bottom=10),
                        padding=10,
                        border_radius=8,
                        bgcolor="#202020" if status_text.value else ft.colors.TRANSPARENT,
                        visible=bool(status_text.value),
                    ),
                    ft.Container(
                        content=send_button,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=20),
                    ),
                ],
                spacing=15,
                expand=True,
            ),
            padding=15,
            expand=True,
            border_radius=12,
            bgcolor="#121212",
        )
        
        return send_card
    
    # ---- RECEIVE TAB ----
    def create_receive_tab():
        from evrmail.wallet.store import list_wallets
        from evrmail.commands.receive import receive as receive_command
        
        # Get wallets
        wallets = list_wallets()
        
        # Wallet dropdown
        wallet_dropdown = ft.Dropdown(
            label="Select Wallet",
            hint_text="Choose wallet for new address",
            options=[
                ft.dropdown.Option(wallet) for wallet in wallets
            ] if wallets else [
                ft.dropdown.Option("⚠️ No wallets found")
            ],
            width=400,
            border_color="#00e0b6",
            focused_border_color="#00e0b6",
            focused_color="#00e0b6",
        )
        
        # Input fields
        label_field = ft.TextField(
            label="Optional Label",
            hint_text="Enter a friendly name for this address",
            border_color="#3ea6ff",
            expand=True,
            focused_border_color="#00e0b6",
        )
        
        # Address display
        address_display = ft.TextField(
            label="Receiving Address",
            read_only=True,
            hint_text="Address will appear here",
            border_color="#3ea6ff",
            expand=True,
            text_style=ft.TextStyle(color="#00e0b6", weight="bold"),
            bgcolor="#151515",
            selection_color="#00e0b6",
        )
        
        # QR code container (placeholder)
        qr_container = ft.Container(
            content=ft.Text("QR will appear here", color="#555"),
            alignment=ft.alignment.center,
            height=150,
            width=150,
            border=ft.border.all(color="#333"),
            border_radius=8,
            bgcolor="#0c0c0c",
        )
        
        # Receive button
        receive_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CALL_RECEIVED),
                    ft.Text("Generate New Address", size=16, weight="bold")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            bgcolor="#00e0b6",
            color="black",
            width=250,
            height=48,
        )
        
        # Copy button
        copy_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.COPY),
                    ft.Text("Copy Address")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            bgcolor="#202020",
            color="white",
            width=200,
        )
        
        # Add a direct clipboard button to the address display in receive tab
        copy_btn = ft.IconButton(
            icon=ft.icons.COPY,
            tooltip="Copy address",
            icon_color="#00e0b6",
        )
        
        # Set a handler for the copy button that uses the button's page reference
        def direct_copy_handler(e):
            if address_display.value:
                addr = address_display.value
                try:
                    # Try direct copying with event's page first
                    if hasattr(e, "page") and hasattr(e.page, "clipboard"):
                        print(f"🧪 Attempting to copy: {addr[:10]}...")
                        e.page.clipboard.set_text(addr)
                        print(f"✅ Successfully called clipboard.set_text with: {addr[:10]}...")
                        e.page.snack_bar = ft.SnackBar(
                            ft.Text("📋 Address copied to clipboard"),
                            bgcolor="#00e0b6",
                            action="OK",
                        )
                        e.page.snack_bar.open = True
                        e.page.update()
                        print(f"✅ Direct copy with event.page successful: {addr[:10]}...")
                        return
                except Exception as ex:
                    print(f"First receive copy attempt failed: {str(ex)}")
                
                # Fallback: Show a dialog with the address
                try:
                    # Use the event's page or any available page
                    dialog_page = None
                    if hasattr(e, "page"):
                        dialog_page = e.page
                    elif get_page() is not None:
                        dialog_page = get_page()
                    elif 'page' in globals():
                        dialog_page = globals()['page']
                    
                    if dialog_page:
                        # Show a dialog with the address for easy copying
                        dialog_page.dialog = ft.AlertDialog(
                            title=ft.Text("Copy Receiving Address", color="#00e0b6"),
                            content=ft.Column([
                                ft.Text("Please copy this address manually:"),
                                ft.Text(
                                    addr,
                                    text_align=ft.TextAlign.CENTER,
                                    weight="bold",
                                    size=14,
                                    bgcolor="#111111",
                                    color="#00e0b6",
                                    width=400,
                                    selectable=True,
                                    style=ft.TextStyle(font_family="monospace"),
                                ),
                            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            actions=[
                                ft.TextButton("Close", on_click=lambda e: close_copy_dialog(e)),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            bgcolor="#202020",
                        )
                        dialog_page.dialog.open = True
                        dialog_page.update()
                        print(f"✅ Showed address dialog for: {addr[:10]}...")
                        
                        # Define the dialog close function
                        def close_copy_dialog(e):
                            e.page.dialog.open = False
                            e.page.update()
                    else:
                        print("❌ No page reference available to show dialog")
                except Exception as ex:
                    print(f"❌ Dialog fallback also failed: {str(ex)}")
        
        copy_btn.on_click = direct_copy_handler
        
        # Replace the address display with a row containing both the field and button
        address_row = ft.Row(
            [
                address_display,
                copy_btn
            ],
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        def handle_receive(e):
            wallet = wallet_dropdown.value
            label = label_field.value.strip() or None
            
            # Get page safely
            if "page" in state and state["page"] is not None:
                current_page = state["page"]
            else:
                # Try to access global page as a fallback
                global page
                if 'page' in globals():
                    current_page = page
                    # Update state for future use
                    state["page"] = page
                else:
                    print("Warning: page object not available for receive operation")
                    return
            
            if not wallet or "⚠️" in str(wallet):
                current_page.snack_bar = ft.SnackBar(
                    ft.Text("❌ No wallet available"),
                    bgcolor="#ff3333",
                    action="OK",
                )
                current_page.snack_bar.open = True
                current_page.update()
                return
            
            try:
                result = receive_command(friendly_name=label, wallet_name=wallet)
                if isinstance(result, dict):
                    address_display.value = result.get("address", "")
                    address_display.update()
                    
                    # Update QR container with address text as placeholder
                    # In a real implementation, this would generate a QR code
                    qr_container.content = ft.Text(
                        "QR for: " + result.get("address", "")[:10] + "...",
                        color="#aaa",
                        text_align=ft.TextAlign.CENTER,
                        size=12,
                    )
                    qr_container.update()
                    
                    current_page.snack_bar = ft.SnackBar(
                        ft.Text("📬 New address generated"),
                        bgcolor="#00e0b6",
                        action="OK",
                    )
                    current_page.snack_bar.open = True
                    current_page.update()
                else:
                    raise ValueError("Invalid receive command result")
            except Exception as e:
                current_page.snack_bar = ft.SnackBar(
                    ft.Text(f"❌ Failed to receive address: {str(e)}"),
                    bgcolor="#ff3333",
                    action="OK",
                )
                current_page.snack_bar.open = True
                current_page.update()
        
        # Set up event handlers
        receive_button.on_click = handle_receive
        
        # Handler for the copy button (uses the same direct approach)
        def copy_address(e):
            if address_display.value:
                addr = address_display.value
                try:
                    # Try direct copying with event's page first
                    if hasattr(e, "page") and hasattr(e.page, "clipboard"):
                        e.page.clipboard.set_text(addr)
                        e.page.snack_bar = ft.SnackBar(
                            ft.Text("📋 Address copied to clipboard"),
                            bgcolor="#00e0b6",
                            action="OK",
                        )
                        e.page.snack_bar.open = True
                        e.page.update()
                        print(f"✅ Copy button clicked, used e.page: {addr[:10]}...")
                        return
                except Exception as ex:
                    print(f"First copy button attempt failed: {str(ex)}")
                
                # Fallback: Show a dialog with the address
                try:
                    # Use the event's page or any available page
                    dialog_page = None
                    if hasattr(e, "page"):
                        dialog_page = e.page
                    elif get_page() is not None:
                        dialog_page = get_page()
                    elif 'page' in globals():
                        dialog_page = globals()['page']
                    
                    if dialog_page:
                        # Show a dialog with the address for easy copying
                        dialog_page.dialog = ft.AlertDialog(
                            title=ft.Text("Copy Receiving Address", color="#00e0b6"),
                            content=ft.Column([
                                ft.Text("Please copy this address manually:"),
                                ft.Text(
                                    addr,
                                    text_align=ft.TextAlign.CENTER,
                                    weight="bold",
                                    size=14,
                                    bgcolor="#111111",
                                    color="#00e0b6",
                                    width=400,
                                    selectable=True,
                                    style=ft.TextStyle(font_family="monospace"),
                                ),
                            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            actions=[
                                ft.TextButton("Close", on_click=lambda e: close_copy_dialog(e)),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            bgcolor="#202020",
                        )
                        dialog_page.dialog.open = True
                        dialog_page.update()
                        print(f"✅ Showed address dialog for: {addr[:10]}...")
                        
                        # Define the dialog close function
                        def close_copy_dialog(e):
                            e.page.dialog.open = False
                            e.page.update()
                    else:
                        print("❌ No page reference available to show dialog")
                except Exception as ex:
                    print(f"❌ Dialog fallback also failed: {str(ex)}")
        
        copy_button.on_click = copy_address
        
        # Layout with card-like container and two columns
        receive_tab = ft.Container(
            content=ft.Column(
                [
                    ft.Text("📥 Receive EVR / Assets", size=18, weight="bold", color="#00e0b6"),
                    ft.Divider(height=1, color="#333"),
                    ft.Container(height=10),
                    
                    ft.Row(
                        [
                            # Left column - form
                            ft.Column(
                                [
                                    wallet_dropdown,
                                    label_field,
                                    receive_button,
                                ],
                                spacing=15,
                                expand=True,
                            ),
                            
                            # Right column - display & QR
                            ft.Column(
                                [
                                    qr_container,
                                    ft.Container(height=10),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5,
                            ),
                        ],
                        spacing=30,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    
                    # Bottom section - address display and copy button
                    ft.Container(height=15),
                    address_row,  # Use the combined row instead of just the field
                    ft.Container(
                        content=copy_button,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=10),
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=15,
            expand=True,
            border_radius=12,
            bgcolor="#121212",
        )
        
        return receive_tab
    
    # ---- Create the main panel structure ----
    # Create tabs
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tab_alignment=ft.TabAlignment.START,
        tabs=[
            ft.Tab(
                text="Addresses",
                icon=ft.icons.LIST_ALT,
                content=create_address_tab(),
            ),
            ft.Tab(
                text="Keys",
                icon=ft.icons.KEY,
                content=create_keys_tab(),
            ),
            ft.Tab(
                text="Send",
                icon=ft.icons.SEND,
                content=create_send_tab(),
            ),
            ft.Tab(
                text="Receive",
                icon=ft.icons.CALL_RECEIVED,
                content=create_receive_tab(),
            ),
            ft.Tab(
                text="Balances",
                icon=ft.icons.ACCOUNT_BALANCE_WALLET,
                content=create_balance_tab(),
            ),
            ft.Tab(
                text="UTXOs",
                icon=ft.icons.DIAMOND,
                content=create_utxo_panel(),
            ),
        ],
        expand=1,
    )
    
    # Main panel container
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.icons.ACCOUNT_BALANCE_WALLET,
                                color="#00e0b6",
                                size=28,
                            ),
                            ft.Text(
                                "Wallet Overview",
                                size=24, 
                                weight="bold",
                                color="#00e0b6",
                            ),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    margin=ft.margin.only(bottom=20, top=10),
                ),
                tabs,
            ],
            spacing=12,
            expand=True,
        ),
        padding=32,
        bgcolor="#181818",
        expand=True,
        border_radius=15,
    )
    
    # Add this to load the address table data after the panel is created
    def delayed_init():
        """This will be called after the panel is added to the page"""
        # Get the current page from the global scope
        global page
        if 'page' in globals():
            # Set in both state and global reference
            state["page"] = page
            _PAGE_REF["page"] = page
            print("✅ Page reference successfully set in delayed_init")
            
        if state["load_page_func"]:
            state["load_page_func"](0)
    
    # Add the delayed_init function as an attribute of the panel
    panel.delayed_init = delayed_init
    
    return panel
