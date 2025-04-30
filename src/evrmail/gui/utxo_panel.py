from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView
)
from PySide6.QtGui import QFont, QGuiApplication, QBrush, QColor
from PySide6.QtCore import Qt
from pathlib import Path
import json

def create_utxo_panel(panel: QWidget) -> QWidget:
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(48, 32, 48, 32)
    layout.setSpacing(12)

    title = QLabel("💎 UTXO Overview")
    title.setFont(QFont("Google Sans", 22, QFont.Bold))
    title.setStyleSheet("color: white;")
    layout.addWidget(title, alignment=Qt.AlignCenter)

    controls_layout = QHBoxLayout()
    refresh_btn = QPushButton("🔄 Refresh UTXOs")
    refresh_btn.setStyleSheet("padding: 10px; background-color: #3ea6ff; color: black; border-radius: 6px; font-weight: bold;")
    controls_layout.addWidget(refresh_btn)

    show_spent_checkbox = QCheckBox("👁 Show Spent")
    show_spent_checkbox.setStyleSheet("color: #bbb; padding-left: 12px;")
    show_spent_checkbox.setChecked(False)
    controls_layout.addWidget(show_spent_checkbox)

    controls_layout.addStretch()
    layout.addLayout(controls_layout)

    table = QTableWidget()
    table.setColumnCount(8)
    table.setHorizontalHeaderLabels(["Spent", "Status", "Address", "Asset", "Amount", "TXID", "VOUT", "Confirmations"])
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
    table.setSortingEnabled(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    layout.addWidget(table)

    all_rows = []  # Store all UTXOs so we can filter spent/unspent

    def load_utxos():
        nonlocal all_rows
        table.setRowCount(0)
        all_rows = []

        utxo_dir = Path.home() / ".evrmail" / "utxos"
        confirmed_file = utxo_dir / "confirmed.json"
        mempool_file = utxo_dir / "mempool.json"

        if confirmed_file.exists():
            confirmed = json.loads(confirmed_file.read_text())
            for address, utxos in confirmed.items():
                for utxo in utxos:
                    print(utxo)
                    all_rows.append({
                        "spent": utxo.get("spent", False),
                        "status": "✅ Confirmed",
                        "address": address,
                        "asset": utxo.get("asset", "EVR"),
                        "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                        "txid": utxo["txid"],
                        "vout": utxo["vout"],
                        "confirmations": utxo.get("confirmations", 1)
                    })

        if mempool_file.exists():
            mempool = json.loads(mempool_file.read_text())
            for address, utxos in mempool.items():
                for utxo in utxos:
                    all_rows.append({
                        "spent": utxo.get("spent", False),
                        "status": "⏳ Unconfirmed",
                        "address": address,
                        "asset": utxo.get("asset", "EVR"),
                        "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                        "txid": utxo["txid"],
                        "vout": utxo["vout"],
                        "confirmations": 0
                    })

        refresh_table()

    def refresh_table():
        show_spent = show_spent_checkbox.isChecked()
        filtered_rows = [row for row in all_rows if show_spent or not row["spent"]]

        table.setRowCount(len(filtered_rows))

        for r, row in enumerate(filtered_rows):
            items = [
                QTableWidgetItem("❌" if row["spent"] else "✅"),
                QTableWidgetItem(row["status"]),
                QTableWidgetItem(row["address"]),
                QTableWidgetItem(row["asset"] if row["asset"] else "EVR"),
                QTableWidgetItem(f"{row['amount']:.8f}"),
                QTableWidgetItem(row["txid"]),
                QTableWidgetItem(str(row["vout"])),
                QTableWidgetItem(str(row["confirmations"])),
            ]

            for i, item in enumerate(items):
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table.setItem(r, i, item)

            # Color code
            if row["spent"]:
                color = QColor("red")
            elif row["confirmations"] == 0:
                color = QColor("orange")
            else:
                color = QColor("lightgreen")

            for i in range(len(items)):
                table.item(r, i).setForeground(QBrush(color))

    refresh_btn.clicked.connect(load_utxos)
    show_spent_checkbox.stateChanged.connect(refresh_table)

    # Initial load
    load_utxos()

    return panel
