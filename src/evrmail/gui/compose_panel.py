# evrmail/gui/compose_panel.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QCheckBox, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from evrmail.wallet.utils import calculate_balances
from pathlib import Path
import json
from datetime import datetime

def save_sent_message(to, subject, content, txid, dry_run=False):
    SENT_FILE = Path.home() / ".evrmail" / "sent.json"
    SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SENT_FILE.exists():
        sent = json.loads(SENT_FILE.read_text())
    else:
        sent = []

    sent.append({
        "to": to,
        "subject": subject,
        "content": content,
        "txid": txid,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
    })

    SENT_FILE.write_text(json.dumps(sent, indent=2))

def create_compose_panel(panel: QWidget) -> QWidget:
    compose_tab = QWidget()
    layout = QVBoxLayout()
    compose_tab.setLayout(layout)

    title = QLabel("📨 Compose New Message")
    title.setFont(QFont("Google Sans", 18, QFont.Medium))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    # 📬 Fields
    to_field = QLineEdit()
    to_field.setPlaceholderText("Recipient (Address or Contact Name)")
    layout.addWidget(to_field)

    subject_field = QLineEdit()
    subject_field.setPlaceholderText("Subject")
    layout.addWidget(subject_field)

    message_field = QTextEdit()
    message_field.setPlaceholderText("Write your message here...")
    layout.addWidget(message_field)

    # 📦 Outbox Dropdown
    balances = calculate_balances()
    outbox_dropdown = QComboBox()
    outbox_dropdown.addItem("(Auto-Select Outbox)")
    for asset_name in balances["assets"].keys():
        outbox_dropdown.addItem(asset_name)
    layout.addWidget(outbox_dropdown)

    # 🧪 Dry-Run Checkbox
    dry_run_checkbox = QCheckBox("🧪 Dry-Run Only (simulate, no broadcast)")
    dry_run_checkbox.setStyleSheet("color: #bbb; padding: 6px;")
    layout.addWidget(dry_run_checkbox)

    # 🚀 Send Button
    send_button = QPushButton("📤 Send Message")
    send_button.setStyleSheet("background-color: #3ea6ff; color: black; font-weight: bold; padding: 10px;")
    layout.addWidget(send_button)

    # 🛠 Handle Send
    def handle_send():
        from evrmail.commands.send.send_msg import send_msg_core

        to = to_field.text().strip()
        subject = subject_field.text().strip()
        content = message_field.toPlainText().strip()
        outbox = outbox_dropdown.currentText()
        dry_run = dry_run_checkbox.isChecked()

        if not to or not subject or not content:
            QMessageBox.warning(panel, "Missing Information", "Please fill out all fields.")
            return

        if outbox == "(Auto-Select Outbox)":
            outbox = None

        try:
            txid = send_msg_core(
                to=to,
                outbox=outbox,
                subject=subject,
                content=content,
                fee_rate=0.01,
                dry_run=dry_run,
                debug=False,
                raw=False
            )

            # 🧠 Save the sent message!
            save_sent_message(to, subject, content, txid, dry_run=dry_run)

            if dry_run:
                QMessageBox.information(
                    compose_tab,
                    "Dry-Run Accepted ✅",
                    "Transaction accepted by testmempoolaccept!\n\nNo broadcast was made."
                )
            else:
                QMessageBox.information(
                    compose_tab,
                    "Message Sent ✅",
                    f"Message successfully sent!\n\nTXID:\n{txid}"
                )

            # 🧹 Reset Form
            to_field.clear()
            subject_field.clear()
            message_field.clear()
            outbox_dropdown.setCurrentIndex(0)
            dry_run_checkbox.setChecked(False)

        except Exception as e:
            QMessageBox.critical(
                compose_tab,  # ✅ FIXED
                "Send Error",
                f"❌ Failed to send message:\n\n{e}"
            )

    send_button.clicked.connect(handle_send)

    layout.addStretch()

    return compose_tab
