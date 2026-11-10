"""
ui/widgets/gauge.py
Custom PyQt6 circular arc gauge widget.

Arc geometry:
  - 240° span starting at 210° (bottom-left) going clockwise.
  - Qt drawArc uses 1/16° units; positive = counter-clockwise from 3 o'clock.
  - Start: 210° → qt_start = 210*16  (8 o'clock position)
  - Span:  -240*16 (clockwise through bottom, right, up to 2 o'clock)

Color zones:
  - 0 … warn_pct  : green  #22c55e
  - warn … crit   : amber  #f59e0b
  - crit … 100%   : red    #ef4444
"""
import math  # noqa: F401 – kept for future tweaks

from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget


class GaugeWidget(QWidget):
    def __init__(
        self,
        label: str = "",
        unit: str = "%",
        max_value: float = 100,
        warn_pct: float = 0.70,
        critical_pct: float = 0.85,
        parent=None,
    ):
        super().__init__(parent)
        self._value      = 0.0
        self._max_value  = float(max_value)
        self._label      = label
        self._unit       = unit
        self._warn_pct   = warn_pct
        self._crit_pct   = critical_pct

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(90, 110)

    # -- Properties --------------------------------------------------------
    @property
    def value(self) -> float:
        return self._value

    @property
    def max_value(self) -> float:
        return self._max_value

    @property
    def label(self) -> str:
        return self._label

    @property
    def unit(self) -> str:
        return self._unit

    def set_value(self, v):
        if v is None:
            v = 0.0
        self._value = max(0.0, min(float(v), self._max_value))
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(110, 130)

    # -- Painting ----------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # --- Layout constants ---
        label_h  = 20          # bottom label height
        margin   = 10
        pen_w    = 9
        # Square bounding box for the arc, centered horizontally
        arc_side = min(w, h - label_h) - margin * 2
        if arc_side < 20:
            painter.end()
            return

        cx   = w / 2
        cy   = (h - label_h) / 2 + margin / 2
        half = arc_side / 2
        rect = QRectF(cx - half, cy - half, arc_side, arc_side)

        # Qt arc: 0 = 3 o'clock, positive = CCW, units = 1/16 degree
        qt_start  =  210 * 16          # 8-o'clock (bottom-left)
        qt_bg_span = -240 * 16         # full 240° clockwise

        pct = self._value / self._max_value if self._max_value > 0 else 0.0
        pct = max(0.0, min(pct, 1.0))
        qt_fg_span = int(qt_bg_span * pct)

        # --- Background arc ---
        pen_bg = QPen(QColor("#334155"))
        pen_bg.setWidth(pen_w)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, qt_start, qt_bg_span)

        # --- Foreground arc ---
        if pct >= self._crit_pct:
            arc_color = QColor("#ef4444")
        elif pct >= self._warn_pct:
            arc_color = QColor("#f59e0b")
        else:
            arc_color = QColor("#22c55e")

        if qt_fg_span != 0:
            pen_fg = QPen(arc_color)
            pen_fg.setWidth(pen_w)
            pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_fg)
            painter.drawArc(rect, qt_start, qt_fg_span)

        # --- Value text (large, bold, centered in arc) ---
        val_font = QFont()
        val_font.setBold(True)
        val_font.setPointSize(max(10, int(arc_side / 5)))
        painter.setFont(val_font)
        painter.setPen(QColor("#e2e8f0"))

        val_str = f"{int(self._value)}"
        text_rect = QRectF(cx - half, cy - half + pen_w, arc_side, arc_side - pen_w * 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, val_str)

        # --- Unit text (small, below value) ---
        unit_font = QFont()
        unit_font.setPointSize(8)
        painter.setFont(unit_font)
        painter.setPen(QColor("#64748b"))
        painter.drawText(
            QRectF(cx - half, cy + half * 0.25, arc_side, 18),
            Qt.AlignmentFlag.AlignCenter,
            self._unit,
        )

        # --- Label below the arc ---
        lbl_font = QFont()
        lbl_font.setPointSize(9)
        painter.setFont(lbl_font)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(
            QRectF(0, h - label_h, w, label_h),
            Qt.AlignmentFlag.AlignCenter,
            self._label,
        )

        painter.end()
