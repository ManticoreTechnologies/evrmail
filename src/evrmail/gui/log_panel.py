# evrmail/gui/log_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

def create_log_panel() -> QWidget:
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(32, 32, 32, 32)
    layout.setSpacing(16)

    title = QLabel("📜 EvrMail Logs")
    title.setFont(QFont("Google Sans", 18, QFont.Medium))
    title.setStyleSheet("color: white;")
    layout.addWidget(title)

    log_output = QTextEdit()
    log_output.setReadOnly(True)
    log_output.setStyleSheet("""
        QTextEdit {
            background-color: #121212;
            color: #ccc;
            font-family: Consolas, monospace;
            font-size: 13px;
            border: 1px solid #333;
            border-radius: 8px;
        }
    """)
    layout.addWidget(log_output)

    clear_btn = QPushButton("🧹 Clear Logs")
    clear_btn.setStyleSheet("""
        QPushButton {
            padding: 8px 16px;
            border: none;
            background-color: #3c3c3c;
            color: white;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #555;
        }
    """)
    clear_btn.clicked.connect(log_output.clear)
    layout.addWidget(clear_btn, alignment=Qt.AlignRight)

    # 🔥 Attach direct access
    panel.log_output = log_output

    return panel
