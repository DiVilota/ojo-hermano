"""
ui/settings_dialog.py
Settings / Preferences panel for Ojo Hermano.
Opens as a dialog from the main window.
"""
import csv
import json
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.theme import DARK_STYLESHEET
from ui import theme

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SettingsDialog(QDialog):
    """Modal settings dialog. Emits settings_changed(dict) on Apply/OK."""

    settings_changed = pyqtSignal(dict)

    # Defaults (also the in-memory state between opens)
    DEFAULTS = {
        "rise_rate":       4.0,   # °C/min
        "rise_min_temp":  65.0,   # °C
        "sustain_temp":   85.0,   # °C
        "session_threshold": 15.0, # GPU D3D % to detect session
    }

    def __init__(self, current: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ojo Hermano — Configuración")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._vals = dict(self.DEFAULTS)
        if current:
            self._vals.update(current)
        self._build_ui()
        self._apply_dark()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("⚙  Configuración")
        f = QFont(); f.setBold(True); f.setPointSize(13)
        title.setFont(f)
        title.setStyleSheet(f"color: {theme.ACCENT};")
        root.addWidget(title)

        # ── Alertas de temperatura ─────────────────────────────────────
        temp_box = QGroupBox("Alertas de temperatura predictivas")
        form = QFormLayout(temp_box)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        self._rise_rate = QDoubleSpinBox()
        self._rise_rate.setRange(1.0, 20.0)
        self._rise_rate.setSingleStep(0.5)
        self._rise_rate.setSuffix("  °C/min")
        self._rise_rate.setValue(self._vals["rise_rate"])
        self._rise_rate.setToolTip(
            "Alerta si la GPU sube más rápido que este valor.\n"
            "Valor más bajo = alertas más tempranas (puede ser ruidoso)."
        )
        form.addRow("Tasa de subida:", self._rise_rate)

        self._rise_min = QDoubleSpinBox()
        self._rise_min.setRange(40.0, 90.0)
        self._rise_min.setSingleStep(1.0)
        self._rise_min.setSuffix("  °C")
        self._rise_min.setValue(self._vals["rise_min_temp"])
        self._rise_min.setToolTip("Solo alertar si la temp ya superó este valor.")
        form.addRow("Temp. mínima para alerta:", self._rise_min)

        self._sustain = QDoubleSpinBox()
        self._sustain.setRange(70.0, 110.0)
        self._sustain.setSingleStep(1.0)
        self._sustain.setSuffix("  °C")
        self._sustain.setValue(self._vals["sustain_temp"])
        self._sustain.setToolTip("Alerta si la GPU se mantiene por encima de esto por >1 min.")
        form.addRow("Temp. sostenida crítica:", self._sustain)

        root.addWidget(temp_box)

        # ── Detección de sesión ────────────────────────────────────────
        sess_box = QGroupBox("Detección de sesión de juego")
        form2 = QFormLayout(sess_box)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form2.setSpacing(8)

        self._sess_thr = QDoubleSpinBox()
        self._sess_thr.setRange(5.0, 60.0)
        self._sess_thr.setSingleStep(1.0)
        self._sess_thr.setSuffix("  % D3D")
        self._sess_thr.setValue(self._vals["session_threshold"])
        self._sess_thr.setToolTip(
            "Carga GPU D3D mínima para considerar que estás jugando.\n"
            "Sube este valor si el monitor detecta sesiones cuando no juegas."
        )
        form2.addRow("Umbral de actividad:", self._sess_thr)

        root.addWidget(sess_box)

        # ── Export ─────────────────────────────────────────────────────
        export_box = QGroupBox("Exportar datos")
        exp_lay = QHBoxLayout(export_box)
        exp_lay.setSpacing(8)

        btn_hw = QPushButton("💾  Hardware Log (CSV)")
        btn_hw.clicked.connect(self._export_hw)

        btn_sess = QPushButton("🎮  Sesiones (CSV)")
        btn_sess.clicked.connect(self._export_sessions)

        btn_tdr = QPushButton("⚡  TDR Events (JSON)")
        btn_tdr.clicked.connect(self._export_tdr)

        for b in (btn_hw, btn_sess, btn_tdr):
            b.setStyleSheet(
                f"QPushButton {{ background:{theme.CARD}; border:1px solid {theme.BORDER};"
                f" border-radius:5px; color:{theme.TEXT}; padding:5px 10px; font-size:11px; }}"
                f"QPushButton:hover {{ background:{theme.CARD_HOVER}; }}"
            )
            exp_lay.addWidget(b)

        root.addWidget(export_box)

        # ── Sistema ────────────────────────────────────────────────────
        sys_box = QGroupBox("Sistema")
        sys_lay = QVBoxLayout(sys_box)
        sys_lay.setSpacing(8)

        # Autostart
        self._autostart_cb = QCheckBox("Iniciar Ojo Hermano con Windows")
        self._autostart_cb.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        try:
            from core.autostart import is_enabled
            self._autostart_cb.setChecked(is_enabled())
        except Exception:
            self._autostart_cb.setChecked(False)
        self._autostart_cb.toggled.connect(self._on_autostart_toggle)
        sys_lay.addWidget(self._autostart_cb)

        # Disk health button
        disk_btn = QPushButton("💾  Ver salud de discos (SMART)")
        disk_btn.setStyleSheet(
            "QPushButton { background:#1e293b; border:1px solid #334155;"
            " border-radius:5px; color:#e2e8f0; padding:5px 10px; font-size:11px; }"
            "QPushButton:hover { background:#334155; }"
        )
        disk_btn.clicked.connect(self._show_disk_health)
        sys_lay.addWidget(disk_btn)

        root.addWidget(sys_box)

        # ── Hotkeys (info) ─────────────────────────────────────────────
        info_lbl = QLabel("⌨  Overlay HUD:  Ctrl + Shift + O")
        info_lbl.setStyleSheet(f"color:{theme.MUTED}; font-size:11px; padding: 4px 0;")
        root.addWidget(info_lbl)

        # ── Buttons ────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        root.addWidget(btns)

    # ------------------------------------------------------------------ style
    def _apply_dark(self):
        self.setStyleSheet(DARK_STYLESHEET)

    # ------------------------------------------------------------------ actions
    def _collect(self) -> dict:
        return {
            "rise_rate":          self._rise_rate.value(),
            "rise_min_temp":      self._rise_min.value(),
            "sustain_temp":       self._sustain.value(),
            "session_threshold":  self._sess_thr.value(),
        }

    def _on_apply(self):
        self._vals = self._collect()
        self.settings_changed.emit(self._vals)

    def _on_ok(self):
        self._on_apply()
        self.accept()

    def current_settings(self) -> dict:
        return dict(self._vals)

    # ------------------------------------------------------------------ export
    def _export_hw(self):
        src = os.path.join(PROJECT_DIR, "hardware_log.csv")
        if not os.path.exists(src):
            QMessageBox.warning(self, "Export", "No hay datos de hardware aún."); return
        dst, _ = QFileDialog.getSaveFileName(
            self, "Guardar Hardware Log", "hardware_log.csv", "CSV (*.csv)"
        )
        if dst:
            import shutil; shutil.copy2(src, dst)
            QMessageBox.information(self, "Export", f"Guardado en:\n{dst}")

    def _export_sessions(self):
        src = os.path.join(PROJECT_DIR, "sessions.json")
        if not os.path.exists(src):
            QMessageBox.warning(self, "Export", "No hay sesiones guardadas aún."); return
        dst, _ = QFileDialog.getSaveFileName(
            self, "Guardar Sesiones", "sessions.csv", "CSV (*.csv)"
        )
        if not dst:
            return
        with open(src, encoding="utf-8") as f:
            sessions = json.load(f)
        if not sessions:
            QMessageBox.warning(self, "Export", "Sin sesiones."); return
        keys = list(sessions[0].keys())
        with open(dst, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader(); w.writerows(sessions)
        QMessageBox.information(self, "Export", f"Guardado en:\n{dst}")

    def _export_tdr(self):
        src = os.path.join(PROJECT_DIR, "tdr_events.json")
        if not os.path.exists(src):
            QMessageBox.warning(self, "Export", "No hay eventos TDR aún."); return
        dst, _ = QFileDialog.getSaveFileName(
            self, "Guardar TDR Events", "tdr_events.json", "JSON (*.json)"
        )
        if dst:
            import shutil; shutil.copy2(src, dst)
            QMessageBox.information(self, "Export", f"Guardado en:\n{dst}")

    def _on_autostart_toggle(self, checked: bool) -> None:
        try:
            from core.autostart import enable, disable
            if checked:
                ok = enable()
            else:
                ok = disable()
            if not ok:
                QMessageBox.warning(self, "Autostart",
                                    "No se pudo modificar el registro de Windows.")
        except Exception as e:
            QMessageBox.warning(self, "Autostart", f"Error: {e}")

    def _show_disk_health(self) -> None:
        try:
            from core.disk_monitor import get_disk_health
            disks = get_disk_health()
        except Exception as e:
            QMessageBox.warning(self, "SMART", f"Error al leer discos: {e}"); return

        if not disks:
            QMessageBox.information(self, "SMART", "No se encontraron discos."); return

        lines = []
        for d in disks:
            lines.append(f"💾  {d['name']} ({d['media_type']}, {d.get('size_gb','?')} GB)")
            lines.append(f"   Estado: {d['health']}")
            if d.get("temp_c"):    lines.append(f"   Temperatura: {d['temp_c']}°C")
            if d.get("wear_pct"):  lines.append(f"   Desgaste: {d['wear_pct']}%")
            if d.get("power_on_hours"): lines.append(f"   Horas encendido: {d['power_on_hours']} h")
            if d.get("read_errors"):    lines.append(f"   Errores lectura: {d['read_errors']}")
            lines.append("")

        msg = "\n".join(lines).strip()
        note = "\n\n⚠ Temperatura y desgaste requieren ejecutar como Administrador." \
               if not any(d.get("temp_c") for d in disks) else ""
        QMessageBox.information(self, "Salud de Discos (SMART)", msg + note)
