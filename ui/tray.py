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
        """Brother Eye icon: black bg, blue outer ring, blue iris, red pupil,
        radiating surveillance scan lines."""
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)

        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Black background
        p.setBrush(QBrush(QColor("#000a14")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 32, 32)

        # 4-6 radiating scan lines from outer edge — ACCENT at 40% opacity
        from PyQt6.QtGui import QPen as _QPen
        scan_color = QColor("#0099ff")
        scan_color.setAlpha(100)   # ~40%
        scan_pen = _QPen(scan_color, 1)
        p.setPen(scan_pen)
        import math
        cx, cy = 16.0, 16.0
        for angle_deg in range(0, 360, 60):
            rad = math.radians(angle_deg)
            x1 = cx + 14 * math.cos(rad)
            y1 = cy + 14 * math.sin(rad)
            x2 = cx + 10 * math.cos(rad)
            y2 = cy + 10 * math.sin(rad)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Outer ring — ACCENT (#0099ff)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#0099ff")))
        p.drawEllipse(2, 2, 28, 28)

        # Inner field — back to black
        p.setBrush(QBrush(QColor("#000a14")))
        p.drawEllipse(5, 5, 22, 22)

        # Iris ring — ACCENT at 60% size
        p.setBrush(QBrush(QColor("#0099ff")))
        p.drawEllipse(7, 7, 18, 18)

        # Pupil — DANGER red (#ff2244)
        p.setBrush(QBrush(QColor("#ff2244")))
        p.drawEllipse(12, 12, 8, 8)

        # Specular highlight
        p.setBrush(QBrush(QColor(255, 255, 255, 180)))
        p.drawEllipse(14, 13, 3, 2)

        p.end()
        return QIcon(px)

    # ------------------------------------------------------------------
    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #001224;
                color: #e8f4ff;
                border: 1px solid #003d6e;
                border-radius: 4px;
                padding: 2px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #002040;
                color: #0099ff;
            }
            QMenu::separator {
                height: 1px;
                background: #003d6e;
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
