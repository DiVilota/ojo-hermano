"""
core/watchdog.py
QThread that watches Windows Event Log for GPU driver crashes (TDR events).
Polls every 10 seconds via PowerShell Get-WinEvent.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timedelta

from PyQt6.QtCore import QThread, pyqtSignal


class WatchdogThread(QThread):
    tdr_detected = pyqtSignal(dict)

    TDR_JSON = "C:/Users/diego/OjoHermano/tdr_events.json"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        # On first run look back 30 minutes
        self._last_check: datetime = datetime.now() - timedelta(minutes=30)

    # ------------------------------------------------------------------
    def run(self):
        self._running = True
        while self._running:
            try:
                self._check_events()
            except Exception as exc:
                print(f"[Watchdog] Error: {exc}")
            time.sleep(10)

    # ------------------------------------------------------------------
    def stop(self):
        self._running = False
        self.wait(6000)

    # ------------------------------------------------------------------
    def _check_events(self):
        # Record the window start *before* the query so we don't miss events
        query_start = self._last_check
        self._last_check = datetime.now()

        # Format for PowerShell datetime string
        last_str = query_start.strftime("%Y-%m-%dT%H:%M:%S")

        ps_script = (
            f"$cutoff = [datetime]'{last_str}';"
            "$filter = @{ LogName='System'; Id=4101,141; StartTime=$cutoff };"
            "$events = Get-WinEvent -FilterHashtable $filter -ErrorAction SilentlyContinue;"
            "if ($events) { $events | Select-Object TimeCreated,Id,Message | ConvertTo-Json -Depth 2 }"
            " else { '[]' }"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                timeout=20,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            print(f"[Watchdog] PowerShell call failed: {exc}")
            return

        raw = result.stdout.decode("utf-8", errors="replace").strip()
        if not raw or raw == "[]":
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"[Watchdog] JSON parse error: {exc}\nRaw: {raw[:200]}")
            return

        # PowerShell may return a single object (dict) or a list
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return

        for ev in data:
            event = {
                "timestamp":   str(ev.get("TimeCreated", "")),
                "event_id":    int(ev.get("Id", 0)),
                "description": str(ev.get("Message", ""))[:300],
            }
            self.tdr_detected.emit(event)
            self._append_event(event)

    # ------------------------------------------------------------------
    def _append_event(self, event: dict):
        events: list = []
        if os.path.exists(self.TDR_JSON):
            try:
                with open(self.TDR_JSON, "r", encoding="utf-8") as fh:
                    events = json.load(fh)
                if not isinstance(events, list):
                    events = []
            except Exception:
                events = []

        events.append(event)

        try:
            with open(self.TDR_JSON, "w", encoding="utf-8") as fh:
                json.dump(events, fh, indent=2, default=str)
        except Exception as exc:
            print(f"[Watchdog] Could not save TDR JSON: {exc}")
