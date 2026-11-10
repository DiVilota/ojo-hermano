"""
ui/theme.py
Brother Eye color palette and comprehensive QSS stylesheet for Ojo Hermano.

DC Comics Brother Eye visual identity:
  - Deep space black backgrounds  — surveillance satellite exterior
  - Electric blue circuits/borders — data streams, surveillance feeds
  - Amber/gold                     — the iconic Brother Eye iris
  - Threat red                     — target locked / critical alerts
"""

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
BG          = "#000a14"   # deep space black
CARD        = "#001224"   # dark navy panels
BORDER      = "#003d6e"   # blue border
BORDER_GLOW = "#0066cc"   # glow accent
ACCENT      = "#0099ff"   # Brother Eye electric blue
ACCENT_DIM  = "#005c99"   # dimmer blue
TEXT        = "#e8f4ff"   # blue-white text
MUTED       = "#4d7a99"   # muted blue-grey
WARN        = "#f59e0b"   # amber (the eye color)
DANGER      = "#ff2244"   # threat red
OK          = "#00cc66"   # clear signal green
CARD_HOVER  = "#002040"   # hover state


# ---------------------------------------------------------------------------
# Comprehensive QSS stylesheet (generated from palette above)
# ---------------------------------------------------------------------------
def _build() -> str:
    return f"""
QMainWindow, QWidget#centralWidget, QScrollArea, QWidget {{
    background-color: {BG};
    color: {TEXT};
}}
QScrollArea {{
    border: none;
}}
QGroupBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    color: {MUTED};
    font-size: 11px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: {ACCENT};
}}
QProgressBar {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: 3px;
    height: 8px;
    text-align: right;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DIM}, stop:1 {ACCENT});
    border-radius: 3px;
}}
QListWidget {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT};
    font-size: 11px;
}}
QListWidget::item:selected {{
    background-color: {BORDER};
    color: {TEXT};
}}
QTableWidget {{
    background: {BG};
    color: {TEXT};
    gridline-color: {BORDER};
    border: none;
    font-size: 11px;
}}
QTableWidget::item {{
    padding: 4px 6px;
}}
QTableWidget::item:selected {{
    background: {BORDER};
    color: {TEXT};
}}
QHeaderView::section {{
    background: {CARD};
    color: {MUTED};
    font-size: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px;
}}
QScrollBar:vertical {{
    background: {CARD};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {CARD};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {CARD};
    color: {MUTED};
    padding: 6px 18px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-size: 11px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {BG};
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
    background: {CARD_HOVER};
}}
QDialog {{
    background: {BG};
    color: {TEXT};
}}
QLabel {{
    color: {TEXT};
    font-size: 11px;
    background: transparent;
}}
QDoubleSpinBox, QSpinBox {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT};
    padding: 3px 6px;
    font-size: 11px;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{
    border-color: {ACCENT};
}}
QDialogButtonBox QPushButton {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 5px;
    color: {TEXT};
    padding: 5px 16px;
    font-size: 11px;
}}
QDialogButtonBox QPushButton:hover {{
    background: {CARD_HOVER};
    border-color: {BORDER_GLOW};
}}
QDialogButtonBox QPushButton:default {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 5px;
    color: {TEXT};
    padding: 5px 14px;
    font-size: 11px;
}}
QPushButton:hover {{
    background: {CARD_HOVER};
    border-color: {BORDER_GLOW};
}}
QPushButton:default {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QSplitter::handle {{
    background: {BORDER};
}}
QCheckBox {{
    color: {TEXT};
    font-size: 11px;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BORDER};
    border-radius: 3px;
    background: {BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    border: 1px solid {ACCENT_DIM};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_DIM};
    border-radius: 2px;
}}
"""


DARK_STYLESHEET: str = _build()
