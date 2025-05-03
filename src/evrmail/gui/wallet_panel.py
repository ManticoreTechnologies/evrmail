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
    
    # State management
    state = {
        "current_page": 0,
        "all_addresses": get_all_addresses(True),
        "filtered_addresses": [],
        "show_labeled_only": False,
        "total_pages": 1,
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
                ft.DataColumn(ft.Text("Index", weight="bold")),
                ft.DataColumn(ft.Text("Label", weight="bold")),
                ft.DataColumn(ft.Text("Address", weight="bold")),
                ft.DataColumn(ft.Text("Path", weight="bold")),
                ft.DataColumn(ft.Text("Public Key", weight="bold")),
                ft.DataColumn(ft.Text("Private Key", weight="bold")),
            ],
            border=ft.border.all(color="#333", width=1),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, "#333"),
            horizontal_lines=ft.border.BorderSide(1, "#333"),
            heading_row_color=ft.colors.with_opacity(0.2, "#202124"),
            heading_row_height=50,
            data_row_min_height=40,
            width=10000,  # Force full width
        )
        
        # Label filter checkbox
        label_filter = ft.Checkbox(
            label="Only show user-labeled addresses",
            value=state["show_labeled_only"],
        )
        
        # Stats label
        stats_label = ft.Text(
            value="Loading addresses...",
            color="#ccc",
            weight="medium",
            text_align=ft.TextAlign.CENTER,
        )
        
        # Pagination controls
        first_page_btn = ft.ElevatedButton("⏮ First", disabled=True)
        prev_btn = ft.ElevatedButton("⬅ Prev", disabled=True)
        page_info = ft.Text("Page 1 / 1", color="white")
        next_btn = ft.ElevatedButton("Next ➡")
        last_page_btn = ft.ElevatedButton("Last ⏭")
        
        pagination_row = ft.Row(
            [first_page_btn, prev_btn, page_info, next_btn, last_page_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        
        def load_page(page: int):
            addresses_to_use = state["filtered_addresses"] if state["show_labeled_only"] else state["all_addresses"]
            total_pages = max(1, (len(addresses_to_use) + PAGE_SIZE - 1) // PAGE_SIZE)
            page = max(0, min(page, total_pages - 1))
            
            start = page * PAGE_SIZE
            end = min(start + PAGE_SIZE, len(addresses_to_use))
            
            # Clear existing rows
            address_table.rows.clear()
            
            # Add new rows
            for entry in addresses_to_use[start:end]:
                address_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(entry.get("index", "")))),
                            ft.DataCell(ft.Text(str(entry.get("friendly_name", "")))),
                            ft.DataCell(ft.Text(entry.get("address", ""))),
                            ft.DataCell(ft.Text(entry.get("path", ""))),
                            ft.DataCell(ft.Text("************")),
                            ft.DataCell(ft.Text("************")),
                        ],
                        on_select_changed=lambda e, addr=entry.get("address", ""): copy_to_clipboard(addr),
                    )
                )
            
            # Update state and UI
            state["current_page"] = page
            stats_label.value = f"Total Addresses: {len(addresses_to_use)} | Page {page + 1} of {total_pages}"
            page_info.value = f"Page {page + 1} / {total_pages}"
            
            # Update button states
            first_page_btn.disabled = page == 0
            prev_btn.disabled = page == 0
            next_btn.disabled = page >= total_pages - 1
            last_page_btn.disabled = page >= total_pages - 1
            
            # Update UI
            address_table.update()
            stats_label.update()
            page_info.update()
            first_page_btn.update()
            prev_btn.update()
            next_btn.update()
            last_page_btn.update()
        
        def copy_to_clipboard(text):
            page.clipboard.set_text(text)
            page.snack_bar = ft.SnackBar(ft.Text(f"Copied: {text}"))
            page.snack_bar.open = True
            page.update()
        
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
        
        # Layout
        header_row = ft.Row(
            [
                ft.Text("Derived Addresses", size=16, weight="medium", color="white"),
                ft.Container(expand=True),
                label_filter,
            ],
        )
        
        address_tab = ft.Column(
            [
                header_row,
                stats_label,
                ft.Container(
                    content=address_table,
                    expand=True,
                ),
                pagination_row,
            ],
            spacing=10,
            expand=True,
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
        
        return address_tab
    
    # ---- KEYS TAB ----
    def create_keys_tab():
        wallet_data = load_all_wallet_keys()
        
        # Keys table
        keys_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Wallet", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Mnemonic", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Passphrase", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Seed", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Extended Public Key", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Extended Private Key", weight=ft.FontWeight.BOLD)),
            ],
            border=ft.border.all(color="#333", width=1),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, "#333"),
            horizontal_lines=ft.border.BorderSide(1, "#333"),
            heading_row_color=ft.colors.with_opacity(0.2, "#202124"),
            heading_row_height=50,
            data_row_min_height=40,
            width=10000,  # Force full width
        )
        
        # Add rows to keys table
        for wallet_name, keys in wallet_data.items():
            keys_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(wallet_name)),
                        ft.DataCell(ft.Text("************")),
                        ft.DataCell(ft.Text("************")),
                        ft.DataCell(ft.Text("************")),
                        ft.DataCell(ft.Text("************")),
                        ft.DataCell(ft.Text("************")),
                    ],
                    on_select_changed=lambda e, name=wallet_name: show_key_details(name),
                )
            )
        
        def show_key_details(wallet_name):
            # In a real app, this would show a dialog with the actual keys
            # For security reasons, we just show a message
            page.dialog = ft.AlertDialog(
                title=ft.Text(f"🔑 {wallet_name} Keys"),
                content=ft.Text("Key details would be shown here.\nFor security reasons, they are not displayed in this implementation."),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: close_dialog()),
                ]
            )
            page.dialog.open = True
            page.update()
        
        def close_dialog():
            page.dialog.open = False
            page.update()
        
        keys_tab = ft.Column(
            [
                ft.Text("🔑 Key Management", size=16, weight="medium", color="white"),
                ft.Container(
                    content=keys_table,
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        )
        
        return keys_tab
    
    # ---- SEND TAB ----
    def create_send_tab():
        # Calculate balances
        balances = calculate_balances()
        
        # Asset dropdown
        asset_dropdown = ft.Dropdown(
            label="Select Asset",
            options=[
                ft.dropdown.Option("EVR")
            ] + [
                ft.dropdown.Option(asset_name) for asset_name in balances["assets"].keys()
            ],
            width=400,
        )
        
        # Input fields
        address_field = ft.TextField(
            label="Destination Address",
            hint_text="Enter recipient address",
            border_color="#3ea6ff",
            expand=True,
        )
        
        amount_field = ft.TextField(
            label="Amount",
            hint_text="Enter amount to send",
            border_color="#3ea6ff",
            expand=True,
        )
        
        # Dry run checkbox
        dry_run_checkbox = ft.Checkbox(
            label="🧪 Dry-Run Only (simulate, no broadcast)",
            value=False,
        )
        
        # Status message
        status_text = ft.Text(
            value="",
            color="#3ea6ff",
        )
        
        # Send button
        send_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SEND),
                    ft.Text("🚀 Send", size=16, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            bgcolor="#3ea6ff",
            color="black",
            width=200,
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
            
            # Confirm dialog
            page.dialog = ft.AlertDialog(
                title=ft.Text("Confirm Send"),
                content=ft.Text(
                    f"Send {amount} {asset} to {address}?\n\n{'(Dry-Run only)' if dry_run else '(Will broadcast)'}"
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.TextButton("Confirm", on_click=lambda e: execute_send(asset, address, amount, dry_run)),
                ],
            )
            page.dialog.open = True
            page.update()
        
        def close_dialog(e=None):
            page.dialog.open = False
            page.update()
        
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
        
        # Layout
        send_tab = ft.Column(
            [
                ft.Text("📤 Send EVR or Assets", size=16, weight="medium", color="white"),
                asset_dropdown,
                address_field,
                amount_field,
                dry_run_checkbox,
                status_text,
                ft.Container(
                    content=send_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=10,
            expand=True,
        )
        
        return send_tab
    
    # ---- RECEIVE TAB ----
    def create_receive_tab():
        from evrmail.wallet.store import list_wallets
        from evrmail.commands.receive import receive as receive_command
        
        # Get wallets
        wallets = list_wallets()
        
        # Wallet dropdown
        wallet_dropdown = ft.Dropdown(
            label="Select Wallet",
            options=[
                ft.dropdown.Option(wallet) for wallet in wallets
            ] if wallets else [
                ft.dropdown.Option("⚠️ No wallets found")
            ],
            width=400,
        )
        
        # Input fields
        label_field = ft.TextField(
            label="Optional Label",
            hint_text="Enter a friendly name for this address",
            border_color="#3ea6ff",
            expand=True,
        )
        
        # Address display
        address_display = ft.TextField(
            label="Receiving Address",
            read_only=True,
            hint_text="Address will appear here",
            border_color="#3ea6ff",
            expand=True,
            text_style=ft.TextStyle(color="#00e0b6"),
        )
        
        # Receive button
        receive_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CALL_RECEIVED),
                    ft.Text("📥 Get New Address", size=16, weight="bold")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            bgcolor="#3ea6ff",
            color="black",
            width=200,
        )
        
        # Copy button
        copy_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.COPY),
                    ft.Text("📋 Copy Address")
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
        
        def handle_receive(e):
            wallet = wallet_dropdown.value
            label = label_field.value.strip() or None
            
            if "⚠️" in wallet:
                page.snack_bar = ft.SnackBar(ft.Text("❌ No wallet available"))
                page.snack_bar.open = True
                page.update()
                return
            
            try:
                result = receive_command(friendly_name=label, wallet_name=wallet)
                if isinstance(result, dict):
                    address_display.value = result.get("address", "")
                    address_display.update()
                    
                    page.snack_bar = ft.SnackBar(ft.Text("📬 New address generated"))
                    page.snack_bar.open = True
                    page.update()
                else:
                    raise ValueError("Invalid receive command result")
            except Exception as e:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Failed to receive address: {str(e)}"))
                page.snack_bar.open = True
                page.update()
        
        def copy_address(e):
            if address_display.value:
                page.clipboard.set_text(address_display.value)
                page.snack_bar = ft.SnackBar(ft.Text("📋 Address copied to clipboard"))
                page.snack_bar.open = True
                page.update()
        
        # Set up event handlers
        receive_button.on_click = handle_receive
        copy_button.on_click = copy_address
        
        # Layout
        receive_tab = ft.Column(
            [
                ft.Text("📥 Receive EVR / Assets", size=16, weight="medium", color="white"),
                wallet_dropdown,
                label_field,
                receive_button,
                address_display,
                copy_button,
            ],
            spacing=10,
            expand=True,
        )
        
        return receive_tab
    
    # ---- Create the main panel structure ----
    # Create tabs
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
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
                    content=ft.Text(
                        "Wallet Overview",
                        size=22,
                        weight="bold",
                        color="white",
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20),
                ),
                tabs,
            ],
            spacing=12,
            expand=True,
        ),
        padding=32,
        expand=True,
    )
    
    # Add this to load the address table data after the panel is created
    def delayed_init():
        # This will be called after the panel is added to the page
        for tab in tabs.tabs:
            if tab.text == "Addresses" and hasattr(tab, "content"):
                addr_tab = tab.content
                # Find the DataTable in the address tab
                for ctrl in addr_tab.controls:
                    if isinstance(ctrl, ft.Container) and hasattr(ctrl, "content") and isinstance(ctrl.content, ft.DataTable):
                        # Found the table, now we can load data
                        load_page(0)
                        break
    
    # Add the delayed_init function as an attribute of the panel
    panel.delayed_init = delayed_init
    
    return panel
