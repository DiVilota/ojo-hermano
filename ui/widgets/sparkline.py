"""
ui/widgets/sparkline.py
Multi-series mini line-chart widget.

Y-axis: 0–100 (all series are pre-clamped to this range).
Grid lines drawn at 25, 50, 75.
Legend with colored dots + labels + latest value shown top-right.
"""
from collections import deque

from PyQt6.QtCore import Qt, QPointF, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget


class SparklineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._series: dict[str, dict] = {}
        self._order:  list[str] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(70)

    # ------------------------------------------------------------------
    def add_series(self, key: str, color_hex: str, label: str, scale: float = 1.0):
        """Register a new data series before pushing data."""
        self._series[key] = {
            "color": QColor(color_hex),
            "label": label,
            "scale": scale,
            "data":  deque(maxlen=300),
        }
        self._order.append(key)

    # ------------------------------------------------------------------
    def push(self, key: str, value):
        """Append a value to the named series. Value is scaled then clamped 0–100."""
        if key not in self._series:
            return
        if value is None:
            value = 0.0
        v = float(value) * self._series[key]["scale"]
        v = max(0.0, min(v, 100.0))
        self._series[key]["data"].append(v)
        self.update()

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(400, 90)

    # ------------------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        LEGEND_W = 92
        PAD_L    = 4
        PAD_T    = 6
        PAD_B    = 4
        plot_w   = w - PAD_L - LEGEND_W
        plot_h   = h - PAD_T - PAD_B

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0f172a"))

        # Border around plot area
        pen_border = QPen(QColor("#1e293b"))
        pen_border.setWidth(1)
        painter.setPen(pen_border)
        painter.drawRect(QRectF(PAD_L, PAD_T, plot_w, plot_h))

        # Grid lines at 25 / 50 / 75
        pen_grid = QPen(QColor("#1e293b"))
        pen_grid.setWidth(1)
        painter.setPen(pen_grid)
        for pct in (25, 50, 75):
            gy = PAD_T + plot_h * (1.0 - pct / 100.0)
            painter.drawLine(
                int(PAD_L), int(gy),
                int(PAD_L + plot_w), int(gy),
            )

        # Clip to plot area while drawing lines
        painter.setClipRect(QRectF(PAD_L, PAD_T, plot_w, plot_h))

        for key in self._order:
            s = self._series[key]
            data = list(s["data"])
            if len(data) < 2:
                continue

            pen = QPen(s["color"])
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            n = len(data)
            pts: list[QPointF] = []
            for i, v in enumerate(data):
                x = PAD_L + (i / (n - 1)) * plot_w
                y = PAD_T + plot_h * (1.0 - v / 100.0)
                pts.append(QPointF(x, y))

            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

        painter.setClipping(False)

        # Legend (top-right of widget)
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        lx = w - LEGEND_W + 4
        for idx, key in enumerate(self._order):
            s  = self._series[key]
            ly = PAD_T + idx * 17

            # Dot
            painter.setBrush(s["color"])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(lx), int(ly + 3), 7, 7)

            # Label + latest value
            data = list(s["data"])
            val_str = f"{data[-1]:.0f}" if data else "—"
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(
                QRectF(lx + 10, ly, LEGEND_W - 14, 15),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{s['label']} {val_str}",
            )

        painter.end()
