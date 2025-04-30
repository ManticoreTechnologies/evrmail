from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSpacerItem, QSizePolicy, QMenu,
    QSystemTrayIcon, QProgressBar, QTextEdit
)
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtCore import Qt, QPoint, QTimer
import sys, os

from .wallet_panel import create_wallet_panel
from .log_panel import create_log_panel
from .browser_panel import create_browser_panel
from .settings_panel import create_settings_panel
from evrmail.daemon import start_daemon_threaded  # 👈 this must exist
from evrmail.gui.compose_panel import create_compose_panel
from .inbox_panel import create_inbox_panel

RESIZE_MARGIN = 6

class EvrMailMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📬 EvrMail")
        self.resize(1080, 720)
        self.setMinimumSize(840, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setMouseTracking(True)
        from queue import Queue
        self._log_queue = Queue()
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None

        # ── Basic Style ───────────────────────
        self.setStyleSheet("""
            QMainWindow {
                background-color: #181818;
                color: #eee;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QPushButton {
                background-color: transparent;
                color: #ccc;
                font-size: 16px;
                padding: 6px 12px;
                border: none;
            }
            QPushButton:hover {
                color: #fff;
                background-color: #2c2c2c;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #00e0b6;
                color: white;
                border-radius: 4px;
            }
            QLabel {
                font-size: 24px;
                color: #00e0b6;
            }
        """)

        # ── System Tray ───────────────────────
        icon_path = os.path.expanduser("~/.evrmail/evrmail_tray_icon.png")
        custom_icon = QIcon(icon_path)
        self.tray_icon = QSystemTrayIcon(custom_icon, self)
        tray_menu = QMenu()
        tray_menu.addAction(QAction("🔔 Show EvrMail", self, triggered=self.show_window))
        tray_menu.addSeparator()
        tray_menu.addAction(QAction("❌ Exit", self, triggered=self.exit_app))
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("EvrMail - Running in Background")
        self.tray_icon.show()

        # ── Layout Setup ──────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Titlebar ──────────────────────────
        titlebar_widget = QWidget()
        titlebar_layout = QHBoxLayout(titlebar_widget)
        titlebar_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel("📬 EvrMail")
        title_label.setStyleSheet("font-size: 16px; color: white;")
        titlebar_layout.addWidget(title_label)
        titlebar_layout.addStretch()

        minimize_btn = QPushButton("🗕")
        maximize_btn = QPushButton("🗖")
        close_btn = QPushButton("✖")
        for btn in (minimize_btn, maximize_btn, close_btn):
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    color: white;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #333;
                    border-radius: 4px;
                }
            """)

        minimize_btn.clicked.connect(self.showMinimized)
        maximize_btn.clicked.connect(self.toggle_max_restore)
        close_btn.clicked.connect(self.exit_app)

        titlebar_layout.addWidget(minimize_btn)
        titlebar_layout.addWidget(maximize_btn)
        titlebar_layout.addWidget(close_btn)
        main_layout.addWidget(titlebar_widget)

        # ── Stack ─────────────────────────────
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.inbox_panel = create_inbox_panel()
        self.compose_panel = create_compose_panel(main_layout)
        self.settings_panel = create_settings_panel()
        self.wallet_panel = create_wallet_panel()
        self.browser_panel = create_browser_panel()
        self.log_panel = create_log_panel()

        for p in (self.inbox_panel, self.compose_panel, self.settings_panel, self.wallet_panel, self.browser_panel, self.log_panel):
            self.stack.addWidget(p)

        # ── Nav Bar ───────────────────────────
        nav = QHBoxLayout()
        nav.setContentsMargins(20, 10, 20, 10)
        self.nav_buttons = {}
        nav_items = {
            "Inbox": ("📥", self.show_inbox),
            "Compose": ("✉️", self.show_compose),
            "Settings": ("⚙️", self.show_settings),
            "Browser": ("⚙️", self.show_browser),
            "Logs": ("⚙️", self.show_logs),
            "Wallet": ("💼", self.show_wallet)
        }
        for name, (icon, func) in nav_items.items():
            btn = QPushButton(f"{icon} {name}")
            btn.setCheckable(True)
            btn.clicked.connect(func)
            self.nav_buttons[name] = btn
            nav.addWidget(btn)
        nav.addItem(QSpacerItem(40, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(nav)

        # ── Loading UI ────────────────────────
        self._init_loading_ui()
        self._start_background_daemon()
    def _flush_log_queue(self):
        while not self._log_queue.empty():
            line = self._log_queue.get()
            self.log_output.append(line)
            if "✅ Daemon listening for transactions" in line:
                QTimer.singleShot(1000, self.show_inbox)

    def _init_loading_ui(self):
        self.loading_widget = QWidget()
        layout = QVBoxLayout(self.loading_widget)
        layout.setContentsMargins(40, 40, 40, 40)

        self.loading_label = QLabel("🚀 Starting EvrMail Daemon...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 16px; color: #80cbc4;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setStyleSheet("QProgressBar { background-color: #1e1e1e; color: white; }")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #121212; color: #ddd; font-size: 13px;")
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._flush_log_queue)
        self.log_timer.start(250)  # 4 updates per second
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_output)
        self.stack.addWidget(self.loading_widget)
        self.stack.setCurrentWidget(self.loading_widget)

    def _append_log(self, msg: str):
        self._log_queue.put(msg)
        # Immediately also show it in the Logs panel
        if hasattr(self, "log_panel") and hasattr(self.log_panel, "log_output"):
            self.log_panel.log_output.append(msg)


    def _start_background_daemon(self):
        def mark_loaded():
            self.stack.setCurrentWidget(self.inbox_panel)
            self.nav_buttons["Inbox"].setChecked(True)

        def log_callback(msg):
            self._append_log(msg)
            from PySide6.QtCore import QMetaObject, Qt
            # inside log_callback:
            if "✅ Daemon listening for transactions" in msg:
                QTimer.singleShot(0, mark_loaded)
        start_daemon_threaded(log_callback=log_callback)

    # ── Navigation ──────────────────────────
    def reset_nav(self, active): [btn.setChecked(name == active) for name, btn in self.nav_buttons.items()]
    def show_compose(self): self.stack.setCurrentWidget(self.compose_panel); self.reset_nav("Compose")
    def show_settings(self): self.stack.setCurrentWidget(self.settings_panel); self.reset_nav("Settings")
    def show_browser(self): self.stack.setCurrentWidget(self.browser_panel); self.reset_nav("Browser")
    def show_logs(self): self.stack.setCurrentWidget(self.log_panel); self.reset_nav("Logs")
    def show_wallet(self): self.stack.setCurrentWidget(self.wallet_panel); self.reset_nav("Wallet")
    def show_inbox(self):
        self.stack.setCurrentWidget(self.inbox_panel)
        self.reset_nav("Inbox")
    def toggle_max_restore(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()

    def create_panel(self, title):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setAlignment(Qt.AlignCenter)
        label = QLabel(title)
        label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        l.addWidget(label)
        return p

    # ── Window Behavior ─────────────────────
    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.tray_icon.showMessage("EvrMail", "Running in background. Right-click tray icon to exit.", self.tray_icon.icon(), 3000)

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def exit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    # ── Mouse Drag/Resize ───────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._resize_start_pos = e.globalPosition().toPoint()
            self._resize_start_geom = self.geometry()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        pos = e.globalPosition().toPoint()
        if e.buttons() == Qt.LeftButton:
            if self._resize_dir:
                delta = pos - self._resize_start_pos
                g = self._resize_start_geom
                if self._resize_dir == "right":
                    self.setGeometry(g.x(), g.y(), g.width() + delta.x(), g.height())
                elif self._resize_dir == "bottom":
                    self.setGeometry(g.x(), g.y(), g.width(), g.height() + delta.y())
                elif self._resize_dir == "corner":
                    self.setGeometry(g.x(), g.y(), g.width() + delta.x(), g.height() + delta.y())
            elif self._drag_pos:
                self.move(pos - self._drag_pos)
        else:
            self._update_cursor(pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None

    def _update_cursor(self, gpos):
        rect = self.rect()
        pos = self.mapFromGlobal(gpos)
        near_right = rect.right() - RESIZE_MARGIN < pos.x() <= rect.right()
        near_bottom = rect.bottom() - RESIZE_MARGIN < pos.y() <= rect.bottom()
        if near_right and near_bottom:
            self.setCursor(Qt.SizeFDiagCursor)
            self._resize_dir = "corner"
        elif near_right:
            self.setCursor(Qt.SizeHorCursor)
            self._resize_dir = "right"
        elif near_bottom:
            self.setCursor(Qt.SizeVerCursor)
            self._resize_dir = "bottom"
        else:
            self.setCursor(Qt.ArrowCursor)
            self._resize_dir = None

def run_gui():
    app = QApplication(sys.argv)
    window = EvrMailMainWindow()
    window.show()
    sys.exit(app.exec())
