"""
ui/overlay.py
Transparent always-on-top gaming HUD showing 4 key metrics.

Positioned top-right of the primary screen.
Toggle visibility with overlay.toggle() (safe to call from Qt's main thread,
or via QMetaObject.invokeMethod from a non-Qt thread).
"""
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _MetricWidget(QWidget):
    """Single metric cell: emoji icon, bold value, small label."""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val = QLabel("—")
        vf = QFont()
        vf.setBold(True)
        vf.setPointSize(14)
        self._val.setFont(vf)
        self._val.setStyleSheet("color: #22c55e; background: transparent;")
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel(label)
        sub_lbl.setStyleSheet(
            "color: #64748b; font-size: 9px; background: transparent;"
        )
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(icon_lbl)
        lay.addWidget(self._val)
        lay.addWidget(sub_lbl)

    def set_value(self, text: str, color: str = "#22c55e"):
        self._val.setText(text)
        self._val.setStyleSheet(f"color: {color}; font-weight: bold; background: transparent;")


# ---------------------------------------------------------------------------
class OverlayHUD(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Prevent the HUD from grabbing focus
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._build_ui()
        self._position()
        self.hide()

    # ------------------------------------------------------------------
    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._gpu_temp = _MetricWidget("🌡", "GPU °C")
        self._fps      = _MetricWidget("🎮", "FPS")
        self._cpu      = _MetricWidget("⚡", "CPU %")
        self._ram      = _MetricWidget("🧠", "RAM %")

        # Thin vertical dividers
        for i, m in enumerate([self._gpu_temp, self._fps, self._cpu, self._ram]):
            lay.addWidget(m)
            if i < 3:
                div = QLabel()
                div.setFixedWidth(1)
                div.setStyleSheet("background: #334155;")
                lay.addWidget(div)

        self.setFixedSize(self.sizeHint())

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(316, 76)

    # ------------------------------------------------------------------
    def _position(self):
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self.move(g.right() - self.width() - 20, g.top() + 20)

    # ------------------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Semi-transparent dark pill background
        p.setBrush(QBrush(QColor(15, 23, 42, 215)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 10, 10)
        p.end()

    # ------------------------------------------------------------------
    @staticmethod
    def _heat(val, warn: float = 70, crit: float = 85) -> str:
        if val is None:
            return "#94a3b8"
        if val >= crit:
            return "#ef4444"
        if val >= warn:
            return "#f59e0b"
        return "#22c55e"

    # ------------------------------------------------------------------
    def update_data(self, s: dict):
        gt = s.get("gpu_temp")
        self._gpu_temp.set_value(
            f"{int(gt)}°" if gt is not None else "—",
            self._heat(gt, 70, 90),
        )

        fps = s.get("gpu_fps")
        self._fps.set_value(
            f"{fps:.0f}" if fps and fps > 0 else "—",
            "#22c55e",
        )

        cl = s.get("cpu_load")
        self._cpu.set_value(
            f"{int(cl)}%" if cl is not None else "—",
            self._heat(cl),
        )

        rl = s.get("ram_load")
        self._ram.set_value(
            f"{int(rl)}%" if rl is not None else "—",
            self._heat(rl),
        )

    # ------------------------------------------------------------------
    @pyqtSlot()
    def toggle(self):
        """Show or hide the HUD. Safe to invoke via QMetaObject from any thread."""
        if self.isVisible():
            self.hide()
        else:
            self._position()
            self.show()
