"""
ui/sessions_panel.py
Gaming session history panel — shows all past sessions in a table
with peak temps, duration, avg FPS and TDR count.
"""
import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui import theme


def _fmt(val, suffix="", decimals=0, fallback="—"):
    if val is None:
        return fallback
    if decimals == 0:
        return f"{int(round(val))}{suffix}"
    return f"{val:.{decimals}f}{suffix}"


class _SessionBarChart(QWidget):
    """Mini bar chart: peak GPU temp per session (last N sessions)."""

    MAX_BARS = 20
    WARN_TEMP  = 70.0
    CRIT_TEMP  = 85.0
    BAR_COLOR_OK   = QColor(theme.OK)
    BAR_COLOR_WARN = QColor(theme.WARN)
    BAR_COLOR_CRIT = QColor(theme.DANGER)
    GRID_COLOR     = QColor(theme.BORDER)
    TEXT_COLOR     = QColor(theme.MUTED)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []
        self.setMinimumHeight(90)
        self.setToolTip("Pico de temperatura GPU por sesión (últimas 20)")

    def set_sessions(self, sessions: list[dict]):
        self._data = sessions[-self.MAX_BARS:]
        self.update()

    def paintEvent(self, _):  # noqa: N802
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 36, 8, 8, 20

        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b
        n       = len(self._data)
        bar_w   = max(4, int(chart_w / n) - 2)
        max_t   = 110.0

        # grid lines at 70 and 85
        p.setPen(QPen(QColor(theme.BORDER), 1, Qt.PenStyle.DashLine))
        for t_line in (70, 85):
            y = pad_t + chart_h - int(chart_h * t_line / max_t)
            p.drawLine(pad_l, y, W - pad_r, y)
            p.setPen(QPen(self.TEXT_COLOR))
            p.setFont(QFont("", 7))
            p.drawText(2, y + 4, f"{t_line}°")
            p.setPen(QPen(QColor(theme.BORDER), 1, Qt.PenStyle.DashLine))

        # bars
        for i, s in enumerate(self._data):
            t = s.get("peak_gpu_temp")
            if t is None:
                continue
            bh = int(chart_h * min(t, max_t) / max_t)
            x  = pad_l + i * (chart_w // n)
            y  = pad_t + chart_h - bh
            color = (self.BAR_COLOR_CRIT if t >= self.CRIT_TEMP
                     else self.BAR_COLOR_WARN if t >= self.WARN_TEMP
                     else self.BAR_COLOR_OK)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, bar_w, bh, 2, 2)

        p.end()


class _StatCard(QWidget):
    """Small summary card: big number + label."""

    def __init__(self, label: str, color: str = "#e2e8f0", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {theme.CARD}; border: 1px solid {theme.ACCENT}; border-radius: 8px;"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val = QLabel("—")
        f = QFont()
        f.setBold(True)
        f.setPointSize(20)
        self._val.setFont(f)
        self._val.setStyleSheet(f"color: {color}; background: transparent;")
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(self._val)
        lay.addWidget(lbl)

    def set(self, text: str):
        self._val.setText(text)


class SessionsPanel(QWidget):
    """Full sessions history panel — drop into a QTabWidget."""

    HEADERS = [
        "Fecha",
        "Duración",
        "Inicio",
        "Fin",
        "Peak GPU °C",
        "Avg GPU °C",
        "Peak CPU %",
        "Avg D3D %",
        "Avg FPS",
        "TDR 💀",
        "Muestras",
    ]

    # column index → color fn
    _TEMP_COL  = 4
    _CPU_COL   = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions: list[dict] = []
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        # ── Summary cards ───────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)

        self._c_total    = _StatCard("Sesiones totales",    theme.ACCENT)
        self._c_time     = _StatCard("Tiempo total",        theme.ACCENT)
        self._c_peak_gpu = _StatCard("Pico GPU máximo",     theme.WARN)
        self._c_tdr      = _StatCard("TDR durante sesiones",theme.DANGER)

        for c in (self._c_total, self._c_time, self._c_peak_gpu, self._c_tdr):
            c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        # ── Active session banner (hidden unless gaming) ─────────────────
        self._active_banner = QLabel("🎮  Sesión activa")
        self._active_banner.setStyleSheet(
            f"background: rgba(0,153,255,0.12); border: 1px solid rgba(0,153,255,0.4);"
            f"border-radius: 6px; color: {theme.ACCENT}; font-weight: bold; font-size: 12px;"
            "padding: 6px 12px;"
        )
        self._active_banner.hide()
        root.addWidget(self._active_banner)

        # ── Bar chart ────────────────────────────────────────────────────
        chart_lbl = QLabel("Pico GPU °C por sesión")
        chart_lbl.setStyleSheet(f"color:{theme.MUTED}; font-size:10px; font-weight:bold;")
        root.addWidget(chart_lbl)
        self._bar_chart = _SessionBarChart()
        root.addWidget(self._bar_chart)

        # ── Table ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #334155;")
        root.addWidget(sep)

        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setStyleSheet(
            f"QHeaderView::section {{ background: {theme.CARD}; color: {theme.MUTED};"
            " font-size: 10px; font-weight: bold; border: none;"
            f" border-bottom: 1px solid {theme.BORDER}; padding: 4px; }}"
        )
        self._table.setStyleSheet(
            f"QTableWidget {{ background: {theme.BG}; color: {theme.TEXT};"
            f" gridline-color: {theme.BORDER}; border: none; font-size: 11px; }}"
            "QTableWidget::item { padding: 4px 6px; }"
            f"QTableWidget::item:selected {{ background: {theme.BORDER}; }}"
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        root.addWidget(self._table)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _heat_color(val, warn=70, crit=85) -> str:
        if val is None:
            return theme.MUTED
        if val >= crit:
            return theme.DANGER
        if val >= warn:
            return theme.WARN
        return theme.OK

    def _make_item(self, text: str, color: str = None,
                   align=Qt.AlignmentFlag.AlignCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color or theme.TEXT))
        item.setTextAlignment(align)
        return item

    # ------------------------------------------------------------------ public
    def load_sessions(self, sessions: list[dict]) -> None:
        """Populate from DataStore on startup."""
        self._sessions = list(sessions)
        self._rebuild_table()
        self._update_summary()
        self._bar_chart.set_sessions(self._sessions)

    def add_session(self, session: dict) -> None:
        """Add a newly completed session and refresh."""
        self._sessions.append(session)
        self._rebuild_table()
        self._update_summary()
        self._bar_chart.set_sessions(self._sessions)

    def set_active(self, active: bool, start_ts: str = "") -> None:
        """Show/hide the 'gaming session active' banner."""
        if active:
            self._active_banner.setText(f"🎮  Sesión activa desde {start_ts}")
            self._active_banner.show()
        else:
            self._active_banner.hide()

    # ------------------------------------------------------------------ internals
    def _rebuild_table(self):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for s in reversed(self._sessions):  # newest first
            row = self._table.rowCount()
            self._table.insertRow(row)

            date_str = s.get("start", "")[:10]
            dur      = s.get("duration_fmt", "—")
            start_t  = s.get("start", "—")[11:16]
            end_t    = s.get("end",   "—")[11:16]

            peak_gpu = s.get("peak_gpu_temp")
            avg_gpu  = s.get("avg_gpu_temp")
            peak_cpu = s.get("peak_cpu_load")
            avg_d3d  = s.get("avg_d3d_load")
            avg_fps  = s.get("avg_fps")
            tdr      = s.get("tdr_count", 0) or 0
            samples  = s.get("sample_count", 0)

            cells = [
                (date_str,                  theme.TEXT),
                (dur,                       theme.ACCENT),
                (start_t,                   theme.MUTED),
                (end_t,                     theme.MUTED),
                (_fmt(peak_gpu, "°C"),      self._heat_color(peak_gpu, 70, 90)),
                (_fmt(avg_gpu,  "°C"),      self._heat_color(avg_gpu,  65, 80)),
                (_fmt(peak_cpu, "%"),       self._heat_color(peak_cpu)),
                (_fmt(avg_d3d,  "%"),       theme.ACCENT),
                (_fmt(avg_fps,  " fps", 1), theme.OK if avg_fps else theme.MUTED),
                (str(tdr) if tdr else "—",  theme.DANGER if tdr else theme.MUTED),
                (str(samples),              theme.MUTED),
            ]

            for col, (text, color) in enumerate(cells):
                self._table.setItem(row, col, self._make_item(text, color))

        self._table.setSortingEnabled(True)

    def _update_summary(self):
        n = len(self._sessions)
        self._c_total.set(str(n))

        total_s = sum(s.get("duration_s", 0) for s in self._sessions)
        h, rem  = divmod(total_s, 3600)
        m, _    = divmod(rem, 60)
        self._c_time.set(f"{h}h {m:02d}m" if h else f"{m}m")

        all_peaks = [s["peak_gpu_temp"] for s in self._sessions
                     if s.get("peak_gpu_temp") is not None]
        self._c_peak_gpu.set(f"{max(all_peaks):.0f}°C" if all_peaks else "—")

        self._c_tdr.set("—")   # TDR linking future feature
        total_tdr = sum(s.get("tdr_count", 0) or 0 for s in self._sessions)
        self._c_tdr.set(str(total_tdr) if total_tdr else "0")
