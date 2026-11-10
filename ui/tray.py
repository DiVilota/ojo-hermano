"""
ui/tray.py
System tray icon and notification manager.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayManager:
    def __init__(self, main_window):
        self._win  = main_window
        self._icon = self._make_eye_icon()

        self._tray = QSystemTrayIcon(self._icon)
        self._tray.setToolTip("Ojo Hermano — hardware monitor")
        self._build_menu()
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    # ------------------------------------------------------------------
    @staticmethod
    def _make_eye_icon() -> QIcon:
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)

        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Eyelid outline (cyan ellipse background)
        p.setBrush(QBrush(QColor("#38bdf8")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 8, 30, 16)

        # White of eye
        p.setBrush(QBrush(QColor("#e2e8f0")))
        p.drawEllipse(3, 10, 26, 12)

        # Dark pupil
        p.setBrush(QBrush(QColor("#0f172a")))
        p.drawEllipse(10, 11, 12, 10)

        # Cyan iris
        p.setBrush(QBrush(QColor("#38bdf8")))
        p.drawEllipse(12, 13, 8, 6)

        # Specular highlight
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(14, 14, 3, 2)

        p.end()
        return QIcon(px)

    # ------------------------------------------------------------------
    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #334155;
            }
            QMenu::separator {
                height: 1px;
                background: #334155;
                margin: 3px 6px;
            }
        """)

        act_show = menu.addAction("👁  Mostrar")
        act_show.triggered.connect(self._show_window)

        menu.addSeparator()

        act_quit = menu.addAction("✕  Salir")
        act_quit.triggered.connect(QApplication.quit)

        self._tray.setContextMenu(menu)

    # ------------------------------------------------------------------
    def _show_window(self):
        self._win.show()
        self._win.raise_()
        self._win.activateWindow()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    # ------------------------------------------------------------------
    def notify(self, title: str, msg: str):
        """Show a system-tray balloon notification."""
        if self._tray.supportsMessages():
            self._tray.showMessage(
                title,
                msg,
                QSystemTrayIcon.MessageIcon.Warning,
                6000,
            )
