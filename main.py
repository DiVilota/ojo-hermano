"""
main.py — Ojo Hermano entry point.

Wires together all subsystems:
  - DataStore         (ring buffer + CSV)
  - MonitorThread     (LibreHardwareMonitor → data_ready signal)
  - WatchdogThread    (Windows Event Log TDR watcher)
  - MainWindow        (PyQt6 dark-themed UI)
  - TrayManager       (system tray icon + balloon alerts)
  - OverlayHUD        (transparent always-on-top gaming HUD)

Global hotkey Ctrl+Shift+O toggles the overlay from a daemon thread
using QMetaObject.invokeMethod to stay thread-safe.
"""
import os
import sys
import threading

from PyQt6.QtCore import Qt, QMetaObject
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


# ---------------------------------------------------------------------------
def _build_dark_palette() -> QPalette:
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#0f172a"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#1e293b"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#0f172a"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#1e293b"))
    pal.setColor(QPalette.ColorRole.ToolTipText,     QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#1e293b"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.BrightText,      QColor("#f8fafc"))
    pal.setColor(QPalette.ColorRole.Link,            QColor("#38bdf8"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#38bdf8"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f172a"))
    # Disabled state
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#334155"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor("#334155"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#334155"))
    return pal


# ---------------------------------------------------------------------------
def _start_hotkey_thread(overlay) -> None:
    """
    Runs `keyboard.wait()` in a daemon thread.
    When Ctrl+Shift+O fires, posts overlay.toggle() safely to the Qt event loop.
    """
    def _worker():
        try:
            import keyboard  # noqa: PLC0415
            keyboard.add_hotkey(
                "ctrl+shift+o",
                lambda: QMetaObject.invokeMethod(
                    overlay,
                    "toggle",
                    Qt.ConnectionType.QueuedConnection,
                ),
            )
            keyboard.wait()          # blocks until process exits
        except ImportError:
            print("[Hotkey] 'keyboard' package not found — Ctrl+Shift+O disabled.")
        except Exception as exc:
            print(f"[Hotkey] Error: {exc}")

    t = threading.Thread(target=_worker, daemon=True, name="hotkey-thread")
    t.start()


# ---------------------------------------------------------------------------
def main() -> None:
    # Make sure relative imports (core/, ui/) resolve from the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # ── Application bootstrap ──────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("Ojo Hermano")
    app.setApplicationDisplayName("Ojo Hermano")
    app.setStyle("Fusion")                     # required for custom palettes
    app.setPalette(_build_dark_palette())
    app.setQuitOnLastWindowClosed(False)       # tray app — keep alive

    # ── Subsystems ────────────────────────────────────────────────────
    from core.data_store import DataStore       # noqa: PLC0415
    from core.monitor   import MonitorThread    # noqa: PLC0415
    from core.watchdog  import WatchdogThread   # noqa: PLC0415
    from ui.main_window import MainWindow       # noqa: PLC0415
    from ui.overlay     import OverlayHUD       # noqa: PLC0415
    from ui.tray        import TrayManager      # noqa: PLC0415

    store      = DataStore()
    monitor    = MonitorThread()
    watchdog   = WatchdogThread()
    main_win   = MainWindow()
    overlay    = OverlayHUD()
    tray       = TrayManager(main_win)

    # ── Signal wiring ─────────────────────────────────────────────────
    # Hardware data → store + UI + overlay
    monitor.data_ready.connect(store.push)
    monitor.data_ready.connect(main_win.update_data)
    monitor.data_ready.connect(overlay.update_data)

    # TDR events → store + UI + tray balloon
    watchdog.tdr_detected.connect(store.add_tdr)
    watchdog.tdr_detected.connect(main_win.add_tdr_event)
    watchdog.tdr_detected.connect(
        lambda ev: tray.notify(
            "⚠  GPU TDR Detected",
            ev.get("description", "")[:120],
        )
    )

    # Pre-populate TDR list from persisted JSON
    for ev in store.tdr_events:
        main_win.add_tdr_event(ev)

    # ── Global hotkey ─────────────────────────────────────────────────
    _start_hotkey_thread(overlay)

    # ── Start background threads ──────────────────────────────────────
    monitor.start()
    watchdog.start()

    # ── Show main window ──────────────────────────────────────────────
    main_win.show()

    # ── Graceful shutdown ─────────────────────────────────────────────
    def _on_quit():
        print("[Main] Stopping threads…")
        monitor.stop()
        watchdog.stop()
        print("[Main] Done.")

    app.aboutToQuit.connect(_on_quit)

    sys.exit(app.exec())


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
