"""
ui/overlay.py
Transparent always-on-top gaming HUD — Brother Eye surveillance theme.

Features:
  - Draggable: left-click and drag to reposition anywhere on screen
  - Opacity control via set_opacity(float) — also adjustable from settings tab
  - Position memory: saved to overlay_pos.json on hide, restored on show
  - Brother Eye design: dark pill with electric-blue border and scan lines

Toggle visibility with overlay.toggle() (safe from Qt main thread,
or via QMetaObject.invokeMethod from a non-Qt thread).
"""
import datetime
import json
import os

from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Palette constants (inline — keeps overlay self-contained at import time)
_ACCENT  = "#0099ff"
_MUTED   = "#4d7a99"
_TEXT    = "#e8f4ff"
_OK      = "#00cc66"
_WARN    = "#f59e0b"
_DANGER  = "#ff2244"

_PROJECT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_POSITION_FILE = os.path.join(_PROJECT_DIR, "overlay_pos.json")


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
        icon_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 12px; background: transparent;"
        )
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val = QLabel("—")
        vf = QFont()
        vf.setBold(True)
        vf.setPointSize(14)
        self._val.setFont(vf)
        self._val.setStyleSheet(f"color: {_TEXT}; background: transparent;")
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel(label)
        sub_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 9px; background: transparent;"
        )
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(icon_lbl)
        lay.addWidget(self._val)
        lay.addWidget(sub_lbl)

    def set_value(self, text: str, color: str = _OK):
        self._val.setText(text)
        self._val.setStyleSheet(
            f"color: {color}; font-weight: bold; background: transparent;"
        )


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
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Dragging state
        self._drag_pos = None

        # Opacity (Brother Eye default: 88%)
        self._opacity = 0.88
        self.setWindowOpacity(self._opacity)

        self._build_ui()
        self._restore_position()   # load saved pos or default top-right
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
        self._session  = _MetricWidget("⏱", "Sesión")
        self._session_start: "datetime.datetime | None" = None

        # Thin vertical dividers — ACCENT at 30% opacity
        for i, m in enumerate([self._gpu_temp, self._fps, self._cpu,
                                self._ram, self._session]):
            lay.addWidget(m)
            if i < 4:
                div = QLabel()
                div.setFixedWidth(1)
                div.setStyleSheet("background: rgba(0, 153, 255, 0.30);")
                lay.addWidget(div)

        self.setFixedSize(self.sizeHint())

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(420, 80)

    # ------------------------------------------------------------------
    # Position memory
    # ------------------------------------------------------------------
    def _default_position(self):
        """Move to top-right of primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self.move(g.right() - self.width() - 20, g.top() + 20)

    def _save_position(self):
        try:
            pos = self.pos()
            with open(_POSITION_FILE, "w", encoding="utf-8") as f:
                json.dump({"x": pos.x(), "y": pos.y()}, f)
        except OSError:
            pass

    def _restore_position(self):
        try:
            with open(_POSITION_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.move(int(data["x"]), int(data["y"]))
        except (OSError, KeyError, ValueError, json.JSONDecodeError):
            self._default_position()

    # ------------------------------------------------------------------
    # Mouse drag — left-click to move the HUD anywhere
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):       # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):        # noqa: N802
        if (event.buttons() == Qt.MouseButton.LeftButton
                and self._drag_pos is not None):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):     # noqa: N802
        self._drag_pos = None

    # ------------------------------------------------------------------
    # Opacity control
    # ------------------------------------------------------------------
    @pyqtSlot(float)
    def set_opacity(self, value: float):
        self._opacity = max(0.1, min(1.0, value))
        self.setWindowOpacity(self._opacity)

    # ------------------------------------------------------------------
    # Custom paint — Brother Eye surveillance HUD
    # ------------------------------------------------------------------
    def paintEvent(self, event):            # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.rect()

        # 1) Dark background — deep space black at ~90% opacity
        p.setBrush(QBrush(QColor(0, 10, 20, 230)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 10, 10)

        # 2) Scan-line effect — 3 thin horizontal lines at 10% opacity
        #    Evokes a surveillance-monitor / CRT raster aesthetic
        p.setPen(QPen(QColor(0, 153, 255, 25), 1))   # ACCENT at ~10%
        step = r.height() // 4
        for i in range(1, 4):
            y = r.top() + i * step
            p.drawLine(r.left() + 14, y, r.right() - 14, y)

        # 3) Electric-blue border — 2 px
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(_ACCENT), 2))
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 10, 10)

        p.end()

    # ------------------------------------------------------------------
    @staticmethod
    def _heat(val, warn: float = 70, crit: float = 85) -> str:
        if val is None:
            return _MUTED
        if val >= crit:
            return _DANGER
        if val >= warn:
            return _WARN
        return _OK

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
            _OK,
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

        # Session elapsed time
        if self._session_start is not None:
            elapsed = datetime.datetime.now() - self._session_start
            m, sec  = divmod(int(elapsed.total_seconds()), 60)
            h, m    = divmod(m, 60)
            txt     = f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
            self._session.set_value(txt, _OK)
        else:
            self._session.set_value("—", _MUTED)

    # ------------------------------------------------------------------
    @pyqtSlot()
    def toggle(self):
        """Show or hide the HUD. Safe to invoke via QMetaObject from any thread."""
        if self.isVisible():
            self._save_position()
            self.hide()
        else:
            self._restore_position()
            self.show()

    @pyqtSlot(dict)
    def on_session_started(self, payload: dict) -> None:
        self._session_start = datetime.datetime.now()

    @pyqtSlot(dict)
    def on_session_ended(self, session: dict) -> None:
        self._session_start = None
        self._session.set_value("—", _MUTED)
