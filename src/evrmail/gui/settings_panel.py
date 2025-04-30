from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

def create_settings_panel() -> QWidget:
    panel = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(32, 32, 32, 32)
    layout.setSpacing(16)
    panel.setLayout(layout)

    # ── Title ─────────────────────────────
    title = QLabel("⚙️ Settings")
    title.setFont(QFont("Google Sans", 18, QFont.Medium))
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    # ── Form Fields ───────────────────────
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignLeft)
    form.setFormAlignment(Qt.AlignTop)

    # Placeholder fields (modular, expandable)
    rpc_field = QLineEdit()
    rpc_field.setPlaceholderText("e.g. https://rpc.evrmore.exchange")
    max_addr_field = QLineEdit()
    max_addr_field.setPlaceholderText("e.g. 1000")

    form.addRow("🔧 Custom Node URL:", rpc_field)
    form.addRow("📐 Max Addresses:", max_addr_field)

    # Style form labels
    for i in range(form.rowCount()):
        label = form.itemAt(i, QFormLayout.LabelRole).widget()
        if label:
            label.setStyleSheet("color: white;")

    layout.addLayout(form)
    layout.addStretch()

    return panel
