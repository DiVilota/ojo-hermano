"""
core/data_store.py
In-memory ring buffer (deque) + CSV persistence.
"""
import csv
import json
import os
from collections import deque


class DataStore:
    CSV_PATH      = "C:/Users/diego/OjoHermano/hardware_log.csv"
    TDR_PATH      = "C:/Users/diego/OjoHermano/tdr_events.json"
    SESSIONS_PATH = "C:/Users/diego/OjoHermano/sessions.json"

    # Flat fields written to CSV (excludes nested cpu_threads list)
    CSV_FIELDS = [
        "ts",
        "cpu_load", "cpu_max_core", "cpu_temp",
        "gpu_temp", "gpu_load", "gpu_d3d",
        "gpu_fan_rpm", "gpu_fan_pct",
        "gpu_clock", "gpu_mem_clock", "gpu_voltage",
        "gpu_vram_used", "gpu_vram_total", "gpu_fps",
        "ram_used", "ram_avail", "ram_load",
        "net_dl", "net_ul", "net_pct",
    ]

    def __init__(self, max_history: int = 600):
        self._buf: deque[dict] = deque(maxlen=max_history)
        self._tdr_events: list[dict] = []
        self._sessions:   list[dict] = []
        self.load_tdr()
        self.load_sessions()

    # ------------------------------------------------------------------
    def push(self, snapshot: dict) -> None:
        """Append a hardware snapshot to the ring buffer and CSV."""
        self._buf.append(snapshot)
        self._write_csv(snapshot)

    # ------------------------------------------------------------------
    @property
    def latest(self) -> dict | None:
        return self._buf[-1] if self._buf else None

    # ------------------------------------------------------------------
    def history(self, n: int = 100) -> list[dict]:
        """Return the last *n* snapshots (oldest first)."""
        buf_list = list(self._buf)
        return buf_list[-n:] if len(buf_list) > n else buf_list

    # ------------------------------------------------------------------
    @property
    def tdr_events(self) -> list[dict]:
        return self._tdr_events

    def add_tdr(self, event: dict) -> None:
        self._tdr_events.append(event)

    def load_tdr(self) -> None:
        """Read persisted TDR events from JSON on startup."""
        if not os.path.exists(self.TDR_PATH):
            return
        try:
            with open(self.TDR_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._tdr_events = data
        except Exception as exc:
            print(f"[DataStore] Could not load TDR events: {exc}")
            self._tdr_events = []

    # ------------------------------------------------------------------
    @property
    def sessions(self) -> list[dict]:
        return self._sessions

    def add_session(self, session: dict) -> None:
        self._sessions.append(session)
        self._save_sessions()

    def load_sessions(self) -> None:
        if not os.path.exists(self.SESSIONS_PATH):
            return
        try:
            with open(self.SESSIONS_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._sessions = data
        except Exception as exc:
            print(f"[DataStore] Could not load sessions: {exc}")
            self._sessions = []

    def _save_sessions(self) -> None:
        try:
            with open(self.SESSIONS_PATH, "w", encoding="utf-8") as fh:
                json.dump(self._sessions, fh, indent=2)
        except Exception as exc:
            print(f"[DataStore] Could not save sessions: {exc}")

    # ------------------------------------------------------------------
    def _write_csv(self, snapshot: dict) -> None:
        try:
            needs_header = (
                not os.path.exists(self.CSV_PATH)
                or os.path.getsize(self.CSV_PATH) == 0
            )
            with open(self.CSV_PATH, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh, fieldnames=self.CSV_FIELDS, extrasaction="ignore"
                )
                if needs_header:
                    writer.writeheader()
                writer.writerow({k: snapshot.get(k, "") for k in self.CSV_FIELDS})
        except Exception as exc:
            print(f"[DataStore] CSV write error: {exc}")
