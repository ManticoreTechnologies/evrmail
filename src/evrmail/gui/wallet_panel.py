from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView, QCheckBox, QTextEdit, QMessageBox
)
from PySide6.QtGui import QFont, QGuiApplication, QColor, QPalette
from PySide6.QtCore import Qt
from evrmail.wallet.addresses import get_all_addresses
from evrmail.gui.balance_panel import create_balance_tab
from evrmail.wallet.utils import load_all_wallet_keys
from evrmail.gui.utxo_panel import create_utxo_panel

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import os

from threading import Timer
from evrmail import rpc_client
from evrmail.commands.send.send_evr import send_evr_tx

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

PAGE_SIZE = 10
def create_send_tab(panel: QWidget) -> QWidget:
    from PySide6.QtWidgets import QLineEdit, QComboBox, QMessageBox, QCheckBox
    from evrmail.wallet.utils import calculate_balances

    send_tab = QWidget()
    layout = QVBoxLayout()
    send_tab.setLayout(layout)

    title = QLabel("📤 Send EVR or Assets")
    title.setFont(QFont("Google Sans", 16, QFont.Medium))
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    asset_dropdown = QComboBox()
    asset_dropdown.setStyleSheet("color: white; background-color: #2c2c2c;")

    # 📥 Load balances dynamically
    balances = calculate_balances()

    asset_dropdown.addItem("EVR")  # Always start with native EVR
    for asset_name in balances["assets"].keys():
        asset_dropdown.addItem(asset_name)

    address_field = QLineEdit()
    address_field.setPlaceholderText("Destination Address")

    amount_field = QLineEdit()
    amount_field.setPlaceholderText("Amount to Send")

    dry_run_checkbox = QCheckBox("🧪 Dry-Run Only (simulate, no broadcast)")
    dry_run_checkbox.setStyleSheet("color: #bbb; padding: 4px;")

    send_btn = QPushButton("🚀 Send")
    send_btn.setStyleSheet("background-color: #3ea6ff; color: black; padding: 10px; border-radius: 6px; font-weight: bold;")

    def handle_send():
        asset = asset_dropdown.currentText()
        address = address_field.text()
        amount = amount_field.text()
        dry_run = dry_run_checkbox.isChecked()

        if not address or not amount:
            QMessageBox.warning(panel, "Missing Info", "Please fill in all fields.")
            return

        try:
            amount_float = float(amount)
        except ValueError:
            QMessageBox.warning(panel, "Invalid Amount", "Amount must be a number.")
            return

        confirm = QMessageBox.question(
            panel,
            "Confirm Send",
            f"Send {amount} {asset} to {address}?\n\n{'(Dry-Run only)' if dry_run else '(Will broadcast)'}",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        from evrmail.wallet import addresses
        try:
            if asset == "EVR":
                # 🔵 Send EVR
                result = send_evr_tx(
                    address,
                    addresses.get_all_addresses(),
                    amount_float,
                    dry_run=dry_run,
                    debug=False,
                    raw=False
                )
            else:
                # 🟠 Send Asset
                result = send_asset_core(
                    from_addresses=None,
                    to_address=address,
                    asset_name=asset,
                    amount=amount_float,
                    fee_rate=0.01,
                    dry_run=dry_run,
                    debug=False,
                    raw=False
                )

            if dry_run:
                QMessageBox.information(panel, "Dry-Run Success", f"🧪 Simulated {amount} {asset} to {address}\nTXID: {result}")
            else:
                QMessageBox.information(panel, "Success", f"✅ Sent {amount} {asset} to {address}\nTXID: {result}")

        except Exception as e:
            QMessageBox.critical(panel, "Send Error", f"❌ Failed to send: {e}")

    send_btn.clicked.connect(handle_send)

    layout.addWidget(QLabel("Select Asset:"))
    layout.addWidget(asset_dropdown)
    layout.addWidget(QLabel("Destination Address:"))
    layout.addWidget(address_field)
    layout.addWidget(QLabel("Amount:"))
    layout.addWidget(amount_field)
    layout.addWidget(dry_run_checkbox)
    layout.addWidget(send_btn)
    layout.addStretch()

    return send_tab


def create_receive_tab(panel: QWidget) -> QWidget:
    from PySide6.QtWidgets import QLineEdit, QComboBox
    from evrmail.wallet.store import list_wallets
    from evrmail.commands.receive import receive as receive_command

    receive_tab = QWidget()
    layout = QVBoxLayout()
    receive_tab.setLayout(layout)

    title = QLabel("📥 Receive EVR / Assets")
    title.setFont(QFont("Google Sans", 16, QFont.Medium))
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    wallet_dropdown = QComboBox()
    wallets = list_wallets()
    if not wallets:
        wallet_dropdown.addItem("⚠️ No wallets found")
    else:
        wallet_dropdown.addItems(wallets)
    wallet_dropdown.setStyleSheet("background-color: #2c2c2c; color: white;")

    friendly_name_field = QLineEdit()
    friendly_name_field.setPlaceholderText("Optional: Label (friendly name)")
    friendly_name_field.setStyleSheet("background-color: #2c2c2c; color: white;")

    address_display = QLineEdit()
    address_display.setPlaceholderText("Receiving Address will appear here")
    address_display.setReadOnly(True)
    address_display.setStyleSheet("background-color: #2c2c2c; color: #00e0b6; font-size: 14px;")

    receive_btn = QPushButton("📥 Get New Address")
    receive_btn.setStyleSheet("background-color: #3ea6ff; color: black; padding: 10px; border-radius: 6px; font-weight: bold;")

    copy_btn = QPushButton("📋 Copy Address")
    copy_btn.setStyleSheet("padding: 8px; background-color: #1f1f1f; color: white;")

    def handle_receive():
        wallet = wallet_dropdown.currentText()
        label = friendly_name_field.text().strip() or None

        if "⚠️" in wallet:
            QMessageBox.warning(panel, "No Wallet", "❌ No wallet available.")
            return

        try:
            result = receive_command(friendly_name=label, wallet_name=wallet)
            if isinstance(result, dict):
                address_display.setText(result.get("address", ""))

                QMessageBox.information(panel, "Received", "📬 New address generated.")
            else:
                raise ValueError("Invalid receive command result.")
        except Exception as e:
            QMessageBox.critical(panel, "Error", f"❌ Failed to receive address:\n{str(e)}")

    def copy_address():
        addr = address_display.text()
        if addr:
            QGuiApplication.clipboard().setText(addr)
            QMessageBox.information(panel, "Copied", "📋 Address copied to clipboard.")

    receive_btn.clicked.connect(handle_receive)
    copy_btn.clicked.connect(copy_address)

    layout.addWidget(QLabel("Select Wallet:"))
    layout.addWidget(wallet_dropdown)
    layout.addWidget(QLabel("Optional Friendly Label:"))
    layout.addWidget(friendly_name_field)
    layout.addWidget(receive_btn)
    layout.addWidget(address_display)
    layout.addWidget(copy_btn)
    layout.addStretch()
    return receive_tab


def create_keys_tab(panel: QWidget) -> QWidget:
    from evrmail.wallet.utils import load_all_wallet_keys

    keys_tab = QWidget()
    keys_layout = QVBoxLayout()
    keys_tab.setLayout(keys_layout)

    title = QLabel("🔑 Key Management")
    title.setFont(QFont("Google Sans", 16, QFont.Medium))
    title.setStyleSheet("color: white;")
    keys_layout.addWidget(title)

    table = QTableWidget()
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        "Wallet", "Mnemonic", "Passphrase", "Seed", "Extended Public Key", "Extended Private Key"
    ])
    table.setStyleSheet("""
        QTableWidget {
            background-color: #181818;
            color: #e0e0e0;
            gridline-color: #303030;
            border: 1px solid #303030;
        }
        QHeaderView::section {
            background-color: #202124;
            color: #9aa0a6;
            font-weight: 500;
            padding: 6px;
        }
    """)

    wallet_data = load_all_wallet_keys()
    table.setRowCount(len(wallet_data))
    table.setSortingEnabled(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    for i, (wallet_name, keys) in enumerate(wallet_data.items()):
        fields = [
            wallet_name,
            keys.get("mnemonic", ""),
            keys.get("mnemonic_passphrase", ""),
            keys.get("HD_seed", ""),
            keys.get("extended_public_key", ""),
            keys.get("extended_private_key", ""),
        ]

        for j, val in enumerate(fields):
            item = QTableWidgetItem(val if j == 0 else "************")
            item.setToolTip("Click to copy")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            table.setItem(i, j, item)

    def handle_key_cell_click(row, col):
        key = list(wallet_data.values())[row]
        value_map = [
            list(wallet_data.keys())[row],
            key["mnemonic"],
            key["mnemonic_passphrase"],
            key["HD_seed"],
            key["extended_public_key"],
            key["extended_private_key"],
        ]
        value = value_map[col]
        QGuiApplication.clipboard().setText(value)
        QMessageBox.information(panel, "Copied", f"Copied: {value}")

    table.cellClicked.connect(handle_key_cell_click)

    for col in range(6):
        if col == 0:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        else:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

    keys_layout.addWidget(table)
    return keys_tab

def create_wallet_panel() -> QWidget:
    panel = QWidget()
    palette = panel.palette()
    palette.setColor(QPalette.Window, QColor("#0f0f0f"))
    panel.setPalette(palette)
    panel.setAutoFillBackground(True)

    layout = QVBoxLayout()
    layout.setContentsMargins(48, 32, 48, 32)
    layout.setSpacing(12)
    panel.setLayout(layout)

    title = QLabel("Wallet Overview")
    title.setFont(QFont("Google Sans", 22, QFont.Bold))
    title.setStyleSheet("color: white;")
    layout.addWidget(title, alignment=Qt.AlignCenter)

    tabs = QTabWidget()
    tabs.setStyleSheet("""
        QTabWidget::pane { border: none; }
        QTabBar::tab {
            background: #222;
            color: #bbb;
            padding: 8px 14px;
            border-radius: 6px;
            margin: 2px;
        }
        QTabBar::tab:selected {
            background: #3ea6ff;
            color: black;
        }
    """)
    layout.addWidget(tabs)

    addr_tab = QWidget()
    addr_layout = QVBoxLayout()
    addr_tab.setLayout(addr_layout)

    top_row = QHBoxLayout()
    header = QLabel("Derived Addresses")
    header.setFont(QFont("Google Sans", 16, QFont.Medium))
    header.setStyleSheet("color: white;")
    label_filter = QCheckBox("Only show user-labeled addresses")
    label_filter.setStyleSheet("color: #bbb;")
    label_filter.setChecked(False)
    top_row.addWidget(header)
    top_row.addStretch()
    top_row.addWidget(label_filter)
    addr_layout.addLayout(top_row)

    stats_label = QLabel("")
    stats_label.setAlignment(Qt.AlignCenter)
    stats_label.setStyleSheet("color: #ccc; font-weight: 500;")
    addr_layout.addWidget(stats_label)

    address_table = QTableWidget()
    address_table.setSortingEnabled(True)
    address_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    address_table.setColumnCount(6)
    address_table.setHorizontalHeaderLabels(["Index", "Label", "Address", "Path", "Public Key", "Private Key"])
    address_table.setStyleSheet("""
        QTableWidget {
            background-color: #181818;
            color: #e0e0e0;
            gridline-color: #303030;
            border: 1px solid #303030;
        }
        QHeaderView::section {
            background-color: #202124;
            color: #9aa0a6;
            font-weight: 500;
            padding: 6px;
        }
    """)
    address_table.horizontalHeader().setStretchLastSection(False)
    addr_layout.addWidget(address_table)

    pagination_layout = QHBoxLayout()
    first_page_btn = QPushButton("⏮ First")
    prev_btn = QPushButton("⬅ Prev")
    next_btn = QPushButton("Next ➡")
    last_page_btn = QPushButton("Last ⏭")
    page_info = QLabel()
    page_info.setStyleSheet("color: white;")

    for btn in (first_page_btn, prev_btn, next_btn, last_page_btn):
        btn.setStyleSheet("padding: 6px 14px; border: none; border-radius: 6px; background-color: #1f1f1f; color: white;")

    pagination_layout.addStretch()
    pagination_layout.addWidget(first_page_btn)
    pagination_layout.addWidget(prev_btn)
    pagination_layout.addWidget(page_info)
    pagination_layout.addWidget(next_btn)
    pagination_layout.addWidget(last_page_btn)
    pagination_layout.addStretch()
    addr_layout.addLayout(pagination_layout)

    addresses = get_all_addresses(True)
    filtered = [entry for entry in addresses if entry.get("friendly_name") and not entry["friendly_name"].startswith("address_")]
    state = {"page": 0, "data": [], "total_pages": 1}

    def load_page(page: int):
        current_data = filtered if label_filter.isChecked() else addresses
        state["data"] = current_data
        total = len(current_data)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        state["total_pages"] = total_pages

        start = page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        address_table.setRowCount(end - start)

        for i, entry in enumerate(current_data[start:end]):
            idx = QTableWidgetItem(str(entry.get("index", "")))
            friendly_name = QTableWidgetItem(str(entry.get("friendly_name", "")))
            addr = QTableWidgetItem(entry.get("address", ""))
            path = QTableWidgetItem(entry.get("path", ""))
            pub = QTableWidgetItem(entry.get("public_key", ""))
            priv = QTableWidgetItem("************")

            items = [idx, friendly_name, addr, path, pub, priv]
            for item in items:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setToolTip("Click to copy")

            address_table.setItem(i, 0, idx)
            address_table.setItem(i, 1, friendly_name)
            address_table.setItem(i, 2, addr)
            address_table.setItem(i, 3, path)
            address_table.setItem(i, 4, pub)
            address_table.setItem(i, 5, priv)

        stats_label.setText(f"Total Addresses: {total} | Page {page + 1} of {total_pages}")
        page_info.setText(f"Page {page + 1} / {total_pages}")
        state["page"] = page
        first_page_btn.setEnabled(page > 0)
        prev_btn.setEnabled(page > 0)
        next_btn.setEnabled(page < total_pages - 1)

    def handle_cell_click(row, col):
        current_data = state["data"]
        index = row + state["page"] * PAGE_SIZE
        if index >= len(current_data):
            return

        field_map = {
            0: str(current_data[index].get("index", "")),
            1: str(current_data[index].get("friendly_name", "")),
            2: str(current_data[index].get("address", "")),
            3: str(current_data[index].get("path", "")),
            4: str(current_data[index].get("public_key", "")),
            5: str(current_data[index].get("private_key", "")),
        }
        text = field_map.get(col, "")
        if text:
            QGuiApplication.clipboard().setText(text)
            QMessageBox.information(panel, "Copied", f"Copied: {text}")

    address_table.cellClicked.connect(handle_cell_click)

    address_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    for col in range(1, 6):
        address_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

    first_page_btn.clicked.connect(lambda: load_page(0))
    prev_btn.clicked.connect(lambda: load_page(state["page"] - 1))
    next_btn.clicked.connect(lambda: load_page(state["page"] + 1))
    last_page_btn.clicked.connect(lambda: load_page(state["total_pages"] - 1))
    label_filter.stateChanged.connect(lambda: load_page(0))

    load_page(0)

    current_page = state.get("page", 0)
    def refresh_addresses_and_reload():
        print("[WalletPanel] 🔥 Reloading addresses from disk...")
        # Reread addresses
        new_addresses = get_all_addresses(True)
        new_filtered = [entry for entry in new_addresses if entry.get("friendly_name") and not entry["friendly_name"].startswith("address_")]

        # Update state
        addresses.clear()
        addresses.extend(new_addresses)

        filtered.clear()
        filtered.extend(new_filtered)

        state["data"] = filtered if label_filter.isChecked() else addresses
        state["total_pages"] = max(1, (len(state["data"]) + PAGE_SIZE - 1) // PAGE_SIZE)

        # Reset page to 0 or current
        state["page"] = min(state.get("page", 0), state["total_pages"] - 1)

        load_page(state["page"])



    start_wallet_folder_monitor(refresh_addresses_and_reload)

    tabs.addTab(addr_tab, "Addresses")

    keys_tab = QWidget()
    keys_layout = QVBoxLayout()
    keys_tab.setLayout(keys_layout)
    keys_layout.addWidget(QLabel("🔑 Key Management (stub)"))
    keys_layout.addWidget(QTextEdit("Key management features coming soon"))
    tabs.addTab(create_keys_tab(panel), "Keys")
    tabs.addTab(create_send_tab(panel), "Send")
    tabs.addTab(create_receive_tab(panel), "Receive")

    tabs.addTab(create_balance_tab(panel), "Balances")
    tabs.addTab(create_utxo_panel(panel), "UTXOs")




    return panel
