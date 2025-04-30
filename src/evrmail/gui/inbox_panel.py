from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTextEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from pathlib import Path
import json

# 📂 Inbox/Sent storage
INBOX_FILE = Path.home() / ".evrmail" / "inbox.json"
SENT_FILE = Path.home() / ".evrmail" / "sent.json"

def load_messages(file_path):
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def create_inbox_panel() -> QWidget:
    panel = QWidget()
    layout = QVBoxLayout()
    panel.setLayout(layout)

    title = QLabel("📬 EvrMail Unified Inbox")
    title.setFont(QFont("Google Sans", 22, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    message_list = QListWidget()
    message_list.setStyleSheet("""
        QListWidget {
            background-color: #181818;
            color: white;
            font-size: 14px;
            border: none;
        }
        QListWidget::item {
            padding: 10px;
        }
        QListWidget::item:selected {
            background-color: #3ea6ff;
            color: black;
        }
    """)
    layout.addWidget(message_list)

    message_view = QTextEdit()
    message_view.setReadOnly(True)
    message_view.setStyleSheet("""
        QTextEdit {
            background-color: #181818;
            color: #eeeeee;
            padding: 10px;
            font-size: 14px;
            border: none;
        }
    """)
    layout.addWidget(message_view)

    refresh_btn = QPushButton("🔄 Refresh")
    refresh_btn.setStyleSheet("background-color: #3ea6ff; color: black; font-weight: bold; padding: 8px;")
    layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)

    def refresh_inbox():
        message_list.clear()
        inbox_msgs = load_messages(INBOX_FILE)
        sent_msgs = load_messages(SENT_FILE)

        # 📥 Inbox
        for msg in inbox_msgs:
            content = msg.get("content", {})
            sender = content.get("from", "Unknown")
            subject = content.get("subject", "(No Subject)")
            body = content.get("content", "(No Content)")

            display_text = f"📥 {sender}: {subject}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {
                "type": "received",
                "subject": subject,
                "from": sender,
                "body": body
            })
            message_list.addItem(item)

        # 📤 Sent
        for msg in sent_msgs:
            label = "🧪 (Simulated)" if msg.get("dry_run") else "📤"
            recipient = msg.get("to", "Unknown")
            subject = msg.get("subject", "(No Subject)")
            body = msg.get("content", "(No Content)")

            display_text = f"{label} {recipient}: {subject}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {
                "type": "sent",
                "subject": subject,
                "to": recipient,
                "body": body
            })
            message_list.addItem(item)

        if message_list.count() == 0:
            message_list.addItem("⚠️ No messages yet.")

    def show_message():
        selected_item = message_list.currentItem()
        if selected_item:
            msg_data = selected_item.data(Qt.UserRole)
            if msg_data:
                if msg_data["type"] == "received":
                    message_view.setPlainText(
                        f"📥 From: {msg_data['from']}\nSubject: {msg_data['subject']}\n\n{msg_data['body']}"
                    )
                elif msg_data["type"] == "sent":
                    message_view.setPlainText(
                        f"📤 To: {msg_data['to']}\nSubject: {msg_data['subject']}\n\n{msg_data['body']}"
                    )
            else:
                message_view.clear()

    refresh_btn.clicked.connect(refresh_inbox)
    message_list.itemClicked.connect(show_message)

    refresh_inbox()
    return panel
