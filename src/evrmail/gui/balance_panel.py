"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

evrmail/gui/balance_panel.py

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from evrmail.wallet.utils import calculate_balances

def create_balance_tab(panel: QWidget) -> QWidget:
    bal_tab = QWidget()
    bal_layout = QVBoxLayout()
    bal_tab.setLayout(bal_layout)

    title = QLabel("💰 Wallet Balances")
    title.setFont(QFont("Google Sans", 16, QFont.Medium))
    title.setStyleSheet("color: white;")
    bal_layout.addWidget(title)

    balances = calculate_balances()

    # ── EVR Total ──────────────────────────
    total_evr = sum(balances["evr"].values()) / 1e8
    self_total_label = QLabel(f"Total EVR: {total_evr:.8f}")
    self_total_label.setFont(QFont("Google Sans", 14, QFont.Bold))
    self_total_label.setStyleSheet("color: #4caf50; padding: 6px;")
    bal_layout.addWidget(self_total_label)

    # ── EVR Table ───────────────────────────
    evr_table = QTableWidget()
    evr_table.setColumnCount(2)
    evr_table.setHorizontalHeaderLabels(["Address", "EVR Balance"])
    evr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    evr_table.setStyleSheet("""
        QTableWidget {
            background-color: #181818;
            color: white;
            gridline-color: #333;
        }
        QHeaderView::section {
            background-color: #2c2c2c;
            color: #bbb;
            font-weight: bold;
            padding: 6px;
        }
    """)

    evr_rows = list(balances["evr"].items())
    evr_table.setRowCount(len(evr_rows))
    for row, (address, amount) in enumerate(evr_rows):
        evr_table.setItem(row, 0, QTableWidgetItem(address))
        evr_table.setItem(row, 1, QTableWidgetItem(f"{amount / 1e8:.8f}"))

    evr_table.setSortingEnabled(True)

    bal_layout.addWidget(QLabel("🔵 EVR Balances"))
    bal_layout.addWidget(evr_table)

    # ── Asset Table ─────────────────────────
    asset_table = QTableWidget()
    asset_table.setColumnCount(3)
    asset_table.setHorizontalHeaderLabels(["Asset", "Address", "Amount"])
    asset_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    asset_table.setStyleSheet("""
        QTableWidget {
            background-color: #181818;
            color: white;
            gridline-color: #333;
        }
        QHeaderView::section {
            background-color: #2c2c2c;
            color: #bbb;
            font-weight: bold;
            padding: 6px;
        }
    """)

    asset_rows = []
    for asset_name, addr_map in balances["assets"].items():
        for address, amount in addr_map.items():
            asset_rows.append((asset_name, address, amount / 1e8))

    asset_table.setRowCount(len(asset_rows))
    for row, (asset, address, amount) in enumerate(asset_rows):
        asset_table.setItem(row, 0, QTableWidgetItem(asset))
        asset_table.setItem(row, 1, QTableWidgetItem(address))
        asset_table.setItem(row, 2, QTableWidgetItem(f"{amount:.8f}"))

    asset_table.setSortingEnabled(True)

    bal_layout.addWidget(QLabel("🟠 Asset Balances"))
    bal_layout.addWidget(asset_table)

    bal_layout.addStretch()

    return bal_tab
