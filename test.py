import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class BrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Embedded Browser Example")
        self.setGeometry(100, 100, 1200, 800)

        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("https://flet.dev"))

        self.reload_button = QPushButton("🔄 Reload")
        self.reload_button.clicked.connect(self.webview.reload)

        layout = QVBoxLayout()
        layout.addWidget(self.reload_button)
        layout.addWidget(self.webview)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserApp()
    window.show()
    sys.exit(app.exec())
