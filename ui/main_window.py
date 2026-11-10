"""
ui/main_window.py
Main application window for Ojo Hermano.
"""
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.gauge import GaugeWidget
from ui.widgets.sparkline import SparklineWidget
from ui.sessions_panel import SessionsPanel
from ui.settings_dialog import SettingsDialog

# ---------------------------------------------------------------------------
# Dark stylesheet
# ---------------------------------------------------------------------------
DARK_STYLE = """
QMainWindow, QWidget#centralWidget, QScrollArea, QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
}
QScrollArea {
    border: none;
}
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    color: #94a3b8;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
}
QProgressBar {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 3px;
    height: 8px;
    text-align: right;
}
QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 3px;
}
QListWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 4px;
    color: #e2e8f0;
    font-size: 11px;
}
QListWidget::item:selected {
    background-color: #334155;
}
QScrollBar:vertical {
    background: #1e293b;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 3px;
    min-height: 20px;
}
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 6px;
}
QTabBar::tab {
    background: #1e293b;
    color: #64748b;
    padding: 6px 18px;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-size: 11px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #0f172a;
    color: #e2e8f0;
    border-bottom: 2px solid #38bdf8;
}
QTabBar::tab:hover:!selected {
    color: #94a3b8;
}
"""


# ---------------------------------------------------------------------------
# Helper: key-value row widget
# ---------------------------------------------------------------------------
class _KVRow(QWidget):
    def __init__(self, key: str, value: str = "—", accent: str = None, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 1, 0, 1)
        lay.setSpacing(6)

        key_lbl = QLabel(key + ":")
        key_lbl.setStyleSheet("color: #64748b; font-size: 10px;")
        key_lbl.setFixedWidth(118)
        key_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.val_lbl = QLabel(value)
        f = QFont()
        f.setBold(True)
        f.setPointSize(10)
        self.val_lbl.setFont(f)
        self._default_color = accent or "#e2e8f0"
        self.val_lbl.setStyleSheet(f"color: {self._default_color};")

        lay.addWidget(key_lbl)
        lay.addWidget(self.val_lbl, 1)

    def set(self, text: str, color: str = None):
        self.val_lbl.setText(text)
        c = color or self._default_color
        self.val_lbl.setStyleSheet(f"color: {c}; font-weight: bold;")


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ojo Hermano")
        self.setMinimumSize(820, 720)
        self.setStyleSheet(DARK_STYLE)
        self._settings_dialog: "SettingsDialog | None" = None
        self._settings: dict = SettingsDialog.DEFAULTS.copy()
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Tab widget ──────────────────────────────────────────────────
        self._tabs = QTabWidget()
        outer.addWidget(self._tabs)

        # Tab 1: Dashboard
        dashboard_widget = QWidget()
        self._tabs.addTab(dashboard_widget, "📊  Dashboard")
        self._build_dashboard(dashboard_widget)

        # Tab 2: Sessions
        self._sessions_panel = SessionsPanel()
        self._tabs.addTab(self._sessions_panel, "🎮  Sesiones")

        # Tab 3: Settings
        settings_btn_widget = QWidget()
        settings_lay = QVBoxLayout(settings_btn_widget)
        settings_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        open_settings_btn = QPushButton("⚙  Abrir configuración")
        open_settings_btn.setStyleSheet(
            "QPushButton{background:#1e293b;border:1px solid #334155;"
            "border-radius:6px;color:#38bdf8;padding:8px 20px;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#334155;}"
        )
        open_settings_btn.setFixedWidth(220)
        open_settings_btn.clicked.connect(self._open_settings)
        settings_lay.addSpacing(20)
        settings_lay.addWidget(open_settings_btn)
        self._tabs.addTab(settings_btn_widget, "⚙  Ajustes")

    # ------------------------------------------------------------------ dashboard
    def _build_dashboard(self, parent: QWidget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(14, 10, 14, 14)
        root.setSpacing(10)
        scroll.setWidget(content)

        outer = QVBoxLayout(parent)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # ── Header ──────────────────────────────────────────────────────
        hdr = QWidget()
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("👁  Ojo Hermano")
        tf = QFont()
        tf.setBold(True)
        tf.setPointSize(17)
        title.setFont(tf)
        title.setStyleSheet("color: #38bdf8;")

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #22c55e; font-size: 15px;")

        self._ts = QLabel("—")
        self._ts.setStyleSheet("color: #64748b; font-size: 11px;")

        # Session active badge
        self._session_badge = QLabel("🎮 Sesión activa")
        self._session_badge.setStyleSheet(
            "background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.4);"
            "border-radius: 10px; color: #22c55e; font-size: 10px; font-weight: bold;"
            "padding: 2px 10px;"
        )
        self._session_badge.hide()

        # Predictive alert banner
        self._alert_banner = QLabel()
        self._alert_banner.setStyleSheet(
            "background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.4);"
            "border-radius: 7px; color: #f87171; font-size: 11px; font-weight: bold;"
            "padding: 6px 12px;"
        )
        self._alert_banner.setWordWrap(True)
        self._alert_banner.hide()

        hdr_lay.addWidget(title)
        hdr_lay.addWidget(self._dot)
        hdr_lay.addWidget(self._session_badge)
        hdr_lay.addStretch()
        hdr_lay.addWidget(self._ts)
        root.addWidget(hdr)
        root.addWidget(self._alert_banner)

        # ── Gauge row ───────────────────────────────────────────────────
        gauge_card = QWidget()
        gauge_card.setStyleSheet(
            "background: #1e293b; border-radius: 8px; border: 1px solid #334155;"
        )
        g_lay = QHBoxLayout(gauge_card)
        g_lay.setContentsMargins(8, 6, 8, 6)
        g_lay.setSpacing(0)

        self._g_gpu_temp = GaugeWidget("GPU Temp", "°C",  max_value=110, warn_pct=0.64, critical_pct=0.82)
        self._g_gpu_d3d  = GaugeWidget("GPU D3D",  "%",   max_value=100)
        self._g_cpu      = GaugeWidget("CPU",      "%",   max_value=100)
        self._g_ram      = GaugeWidget("RAM",      "%",   max_value=100)

        for g in (self._g_gpu_temp, self._g_gpu_d3d, self._g_cpu, self._g_ram):
            g.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            g.setFixedHeight(130)
            g_lay.addWidget(g)

        root.addWidget(gauge_card)

        # ── Detail group boxes ──────────────────────────────────────────
        detail_row = QHBoxLayout()
        detail_row.setSpacing(8)

        # GPU
        gpu_box = QGroupBox("GPU")
        gbl     = QVBoxLayout(gpu_box)
        gbl.setSpacing(2)
        self._kv = {}

        def _kv(box_layout, name, key, accent=None):
            row = _KVRow(name, accent=accent)
            box_layout.addWidget(row)
            self._kv[key] = row

        _kv(gbl, "Temperature",    "gpu_temp",    "#f59e0b")
        _kv(gbl, "Core Load",      "gpu_load",    "#f59e0b")
        _kv(gbl, "D3D 3D Load",    "gpu_d3d",     "#f59e0b")
        _kv(gbl, "Core Clock",     "gpu_clock")
        _kv(gbl, "Memory Clock",   "gpu_mem_clk")
        _kv(gbl, "VRAM Used",      "gpu_vram",    "#38bdf8")
        _kv(gbl, "Core Voltage",   "gpu_voltage")
        _kv(gbl, "Fan",            "gpu_fan")
        _kv(gbl, "FPS Factor",     "gpu_fps",     "#22c55e")

        # System
        sys_box = QGroupBox("System")
        sbl     = QVBoxLayout(sys_box)
        sbl.setSpacing(2)
        _kv(sbl, "CPU Total",     "cpu_load",  "#6366f1")
        _kv(sbl, "Max Core",      "cpu_max")
        _kv(sbl, "Package Temp",  "cpu_temp")
        _kv(sbl, "RAM Used",      "ram_used",  "#22c55e")
        _kv(sbl, "RAM Free",      "ram_avail")
        _kv(sbl, "RAM Load",      "ram_load")

        # Network
        net_box = QGroupBox("Network")
        nbl     = QVBoxLayout(net_box)
        nbl.setSpacing(2)
        _kv(nbl, "Download",    "net_dl",  "#38bdf8")
        _kv(nbl, "Upload",      "net_ul",  "#38bdf8")
        _kv(nbl, "Utilization", "net_pct")

        detail_row.addWidget(gpu_box, 2)
        detail_row.addWidget(sys_box, 1)
        detail_row.addWidget(net_box, 1)
        root.addLayout(detail_row)

        # ── CPU cores ───────────────────────────────────────────────────
        cores_box  = QGroupBox("CPU Cores")
        cores_grid = QGridLayout(cores_box)
        cores_grid.setSpacing(4)
        cores_grid.setHorizontalSpacing(8)
        self._core_bars: list[QProgressBar] = []
        self._core_pcts: list[QLabel]       = []

        for i in range(8):
            r, c = divmod(i, 4)
            lbl = QLabel(f"C{i+1}")
            lbl.setStyleSheet("color: #64748b; font-size: 9px;")
            lbl.setFixedWidth(18)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)

            pct = QLabel("0%")
            pct.setStyleSheet("color: #94a3b8; font-size: 9px;")
            pct.setFixedWidth(26)
            pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self._core_bars.append(bar)
            self._core_pcts.append(pct)

            base_col = c * 3
            cores_grid.addWidget(lbl, r, base_col)
            cores_grid.addWidget(bar, r, base_col + 1)
            cores_grid.addWidget(pct, r, base_col + 2)

        root.addWidget(cores_box)

        # ── Sparkline ───────────────────────────────────────────────────
        spark_box = QGroupBox("History (last 15 min)")
        spark_lay = QVBoxLayout(spark_box)
        spark_lay.setContentsMargins(6, 6, 6, 6)
        self._spark = SparklineWidget()
        self._spark.add_series("gpu_load", "#f59e0b", "GPU",  scale=1.0)
        self._spark.add_series("cpu_load", "#6366f1", "CPU",  scale=1.0)
        self._spark.add_series("ram_load", "#22c55e", "RAM",  scale=1.0)
        self._spark.add_series("net_pct",  "#38bdf8", "Net",  scale=1.0)
        spark_lay.addWidget(self._spark)
        root.addWidget(spark_box)

        # ── TDR events ──────────────────────────────────────────────────
        tdr_box = QGroupBox("⚠  GPU Driver Crashes (TDR Events)")
        tdr_lay = QVBoxLayout(tdr_box)
        self._tdr_list = QListWidget()
        self._tdr_list.setMaximumHeight(110)
        placeholder = QListWidgetItem("No TDR events detected.")
        placeholder.setForeground(QColor("#64748b"))
        self._tdr_list.addItem(placeholder)
        tdr_lay.addWidget(self._tdr_list)
        root.addWidget(tdr_box)

        root.addStretch()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _fmt(val, suffix: str = "", decimals: int = 0, fallback: str = "—") -> str:
        if val is None:
            return fallback
        if decimals == 0:
            return f"{int(round(val))}{suffix}"
        return f"{val:.{decimals}f}{suffix}"

    @staticmethod
    def _heat(val, warn: float = 70, crit: float = 85) -> str:
        if val is None:
            return "#e2e8f0"
        if val >= crit:
            return "#ef4444"
        if val >= warn:
            return "#f59e0b"
        return "#22c55e"

    @staticmethod
    def _fmt_speed(val) -> str:
        if val is None:
            return "—"
        if val >= 1024 * 1024:
            return f"{val / (1024*1024):.2f} GB/s"
        if val >= 1024:
            return f"{val / 1024:.2f} MB/s"
        return f"{val:.1f} KB/s"

    # ------------------------------------------------------------------ slot
    def update_data(self, s: dict):
        self._ts.setText(QDateTime.currentDateTime().toString("hh:mm:ss"))

        # Gauges
        self._g_gpu_temp.set_value(s.get("gpu_temp") or 0)
        self._g_gpu_d3d.set_value(s.get("gpu_d3d")   or s.get("gpu_load") or 0)
        self._g_cpu.set_value(s.get("cpu_load")       or 0)
        self._g_ram.set_value(s.get("ram_load")       or 0)

        # GPU KVs
        gt = s.get("gpu_temp")
        self._kv["gpu_temp"].set(self._fmt(gt, "°C"), self._heat(gt, 70, 90))
        gl = s.get("gpu_load")
        self._kv["gpu_load"].set(self._fmt(gl, "%"), self._heat(gl))
        gd = s.get("gpu_d3d")
        self._kv["gpu_d3d"].set(self._fmt(gd, "%"), self._heat(gd))
        self._kv["gpu_clock"].set(self._fmt(s.get("gpu_clock"), " MHz"))
        self._kv["gpu_mem_clk"].set(self._fmt(s.get("gpu_mem_clock"), " MHz"))

        vu, vt = s.get("gpu_vram_used"), s.get("gpu_vram_total")
        if vu is not None and vt is not None:
            self._kv["gpu_vram"].set(f"{vu:.0f} / {vt:.0f} MB")
        else:
            self._kv["gpu_vram"].set(self._fmt(vu, " MB", 0))

        self._kv["gpu_voltage"].set(self._fmt(s.get("gpu_voltage"), " V", 3))

        frpm = s.get("gpu_fan_rpm")
        fpct = s.get("gpu_fan_pct")
        parts = []
        if frpm is not None:
            parts.append(f"{int(frpm)} RPM")
        if fpct is not None:
            parts.append(f"{int(fpct)}%")
        self._kv["gpu_fan"].set(" · ".join(parts) if parts else "—")

        fps = s.get("gpu_fps")
        self._kv["gpu_fps"].set(f"{fps:.1f}" if fps and fps > 0 else "—")

        # System KVs
        cl = s.get("cpu_load")
        self._kv["cpu_load"].set(self._fmt(cl, "%"), self._heat(cl))
        self._kv["cpu_max"].set(self._fmt(s.get("cpu_max_core"), "%"))
        ct = s.get("cpu_temp")
        self._kv["cpu_temp"].set(self._fmt(ct, "°C"), self._heat(ct, 70, 90) if ct else None)
        self._kv["ram_used"].set(self._fmt(s.get("ram_used"), " GB", 1))
        self._kv["ram_avail"].set(self._fmt(s.get("ram_avail"), " GB", 1))
        rl = s.get("ram_load")
        self._kv["ram_load"].set(self._fmt(rl, "%"), self._heat(rl))

        # Network KVs
        self._kv["net_dl"].set(self._fmt_speed(s.get("net_dl")))
        self._kv["net_ul"].set(self._fmt_speed(s.get("net_ul")))
        self._kv["net_pct"].set(self._fmt(s.get("net_pct"), "%", 1))

        # CPU cores (up to 8 shown)
        threads = s.get("cpu_threads", [])
        for i in range(8):
            if i < len(threads):
                v = threads[i].get("val")
                iv = int(v) if v is not None else 0
                self._core_bars[i].setValue(iv)
                self._core_pcts[i].setText(f"{iv}%")
            else:
                self._core_bars[i].setValue(0)
                self._core_pcts[i].setText("—")

        # Sparkline
        self._spark.push("gpu_load", s.get("gpu_load") or 0)
        self._spark.push("cpu_load", s.get("cpu_load") or 0)
        self._spark.push("ram_load", s.get("ram_load") or 0)
        self._spark.push("net_pct",  s.get("net_pct")  or 0)

    def add_tdr_event(self, event: dict):
        # Remove placeholder if still present
        if self._tdr_list.count() == 1:
            ph = self._tdr_list.item(0)
            if ph and ph.text() == "No TDR events detected.":
                self._tdr_list.clear()

        ts   = event.get("timestamp", "")
        eid  = event.get("event_id",  "?")
        desc = event.get("description", "")[:90]
        item = QListWidgetItem(f"⚠  [{ts}]  ID {eid}: {desc}")
        item.setForeground(QColor("#ef4444"))
        self._tdr_list.insertItem(0, item)

    # ------------------------------------------------------------------ session slots
    def on_session_started(self, payload: dict) -> None:
        ts = payload.get("start", "")
        self._session_badge.setText(f"🎮 Jugando desde {ts[11:16]}")
        self._session_badge.show()
        self._sessions_panel.set_active(True, ts)

    def on_session_ended(self, session: dict) -> None:
        self._session_badge.hide()
        self._sessions_panel.set_active(False)
        self._sessions_panel.add_session(session)
        # Switch to Sessions tab briefly to show the new entry
        self._tabs.setCurrentIndex(1)

    def load_sessions(self, sessions: list) -> None:
        self._sessions_panel.load_sessions(sessions)

    # ------------------------------------------------------------------ predictive alerts
    def on_trend_alert(self, alert: dict) -> None:
        """Show predictive warning banner from TrendAnalyzer."""
        msg = alert.get("message", "")
        icon = {"rising": "🌡️", "sustained": "🔥", "throttle": "⚡"}.get(
            alert.get("type", ""), "⚠️"
        )
        self._alert_banner.setText(f"{icon}  {msg}")
        self._alert_banner.show()
        # Switch to dashboard if on another tab
        if self._tabs.currentIndex() != 0:
            self._tabs.setCurrentIndex(0)

    def on_alert_cleared(self, _: dict) -> None:
        self._alert_banner.hide()

    # ------------------------------------------------------------------ settings
    def _open_settings(self) -> None:
        dlg = SettingsDialog(current=self._settings, parent=self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self, s: dict) -> None:
        self._settings = s
        self.settings_changed_signal.emit(s)

    # Signal for main.py to pick up settings changes
    from PyQt6.QtCore import pyqtSignal as _sig
    settings_changed_signal = _sig(dict)

    # ------------------------------------------------------------------ close
    def closeEvent(self, event):  # noqa: N802
        """Hide to tray instead of quitting."""
        event.ignore()
        self.hide()
