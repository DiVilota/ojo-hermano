"""
core/session_tracker.py
Detects gaming sessions automatically based on GPU D3D load threshold.

A session STARTS when gpu_d3d > LOAD_THRESHOLD for MIN_ACTIVE_SAMPLES consecutive polls.
A session ENDS  when gpu_d3d < LOAD_THRESHOLD for IDLE_TIMEOUT_SAMPLES consecutive polls.

Emits:
  session_started(dict)  — when gaming begins
  session_ended(dict)    — when gaming ends, with full stats
"""
import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class SessionTracker(QObject):
    session_started = pyqtSignal(dict)
    session_ended   = pyqtSignal(dict)

    # Tuning
    LOAD_THRESHOLD       = 15.0   # GPU D3D % to consider "gaming"
    MIN_ACTIVE_SAMPLES   = 3      # consecutive polls above threshold → session start (3×3s = 9s)
    IDLE_TIMEOUT_SAMPLES = 10     # consecutive polls below threshold → session end  (10×3s = 30s)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active        = False
        self._above_count   = 0    # consecutive samples above threshold
        self._below_count   = 0    # consecutive samples below threshold (while active)

        # Accumulated stats for the current session
        self._start_time:   datetime.datetime | None = None
        self._samples:      list[dict]               = []

    # ------------------------------------------------------------------ slot
    def on_data(self, snap: dict) -> None:
        """Call this for every hardware snapshot (connected to MonitorThread.data_ready)."""
        d3d = snap.get("gpu_d3d") or 0.0

        if not self._active:
            # Waiting for a session to start
            if d3d >= self.LOAD_THRESHOLD:
                self._above_count += 1
            else:
                self._above_count = 0

            if self._above_count >= self.MIN_ACTIVE_SAMPLES:
                self._start_session(snap)
        else:
            # Session is active — accumulate stats
            self._samples.append(snap)

            if d3d < self.LOAD_THRESHOLD:
                self._below_count += 1
            else:
                self._below_count = 0

            if self._below_count >= self.IDLE_TIMEOUT_SAMPLES:
                self._end_session(snap)

    # ------------------------------------------------------------------ helpers
    def _start_session(self, snap: dict) -> None:
        self._active      = True
        self._below_count = 0
        self._above_count = 0
        self._start_time  = datetime.datetime.now()
        self._samples     = [snap]

        payload = {
            "start": self._start_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.session_started.emit(payload)
        print(f"[Session] Started at {payload['start']}")

    def _end_session(self, snap: dict) -> None:
        end_time  = datetime.datetime.now()
        duration  = end_time - self._start_time
        duration_s = int(duration.total_seconds())

        # Compute stats from accumulated samples
        gpu_temps  = [s["gpu_temp"]  for s in self._samples if s.get("gpu_temp")  is not None]
        cpu_loads  = [s["cpu_load"]  for s in self._samples if s.get("cpu_load")  is not None]
        d3d_loads  = [s["gpu_d3d"]   for s in self._samples if s.get("gpu_d3d")   is not None]
        fps_values = [s["gpu_fps"]   for s in self._samples if s.get("gpu_fps") and s["gpu_fps"] > 0]

        session = {
            "start":        self._start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end":          end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_s":   duration_s,
            "duration_fmt": _fmt_duration(duration_s),
            "peak_gpu_temp":  round(max(gpu_temps),  1) if gpu_temps  else None,
            "avg_gpu_temp":   round(sum(gpu_temps)  / len(gpu_temps),  1) if gpu_temps  else None,
            "peak_cpu_load":  round(max(cpu_loads),  1) if cpu_loads  else None,
            "avg_d3d_load":   round(sum(d3d_loads)  / len(d3d_loads),  1) if d3d_loads  else None,
            "avg_fps":        round(sum(fps_values) / len(fps_values), 1) if fps_values else None,
            "sample_count":   len(self._samples),
        }

        self._active     = False
        self._start_time = None
        self._samples    = []
        self._below_count = 0

        self.session_ended.emit(session)
        print(f"[Session] Ended — {session['duration_fmt']}, "
              f"peak GPU {session['peak_gpu_temp']}°C")

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def session_start(self) -> datetime.datetime | None:
        return self._start_time


def _fmt_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"
