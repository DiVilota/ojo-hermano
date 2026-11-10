"""
core/trend_analyzer.py
Predictive intelligence layer — watches hardware trends and warns
BEFORE a crash happens, not after.

Signals emitted (all carry a dict with context):
  temp_rising    — GPU temp rising faster than RISE_RATE threshold
  temp_sustained — GPU has been above SUSTAIN_TEMP for too long
  throttle       — GPU clock dropped while load stayed high (thermal throttling)
  alert_cleared  — previous alert condition is no longer present
"""
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal


class TrendAnalyzer(QObject):

    temp_rising    = pyqtSignal(dict)
    temp_sustained = pyqtSignal(dict)
    throttle       = pyqtSignal(dict)
    alert_cleared  = pyqtSignal(dict)

    # ── Thresholds (all configurable via update_settings) ──────────────
    RISE_RATE_C_PER_MIN  = 4.0   # °C/min — "rising fast" threshold
    RISE_WINDOW          = 5     # samples to measure rate over (5×3s = 15s)
    RISE_MIN_TEMP        = 65.0  # only trigger if already above this

    SUSTAIN_TEMP         = 85.0  # °C — "dangerously hot"
    SUSTAIN_SAMPLES      = 20    # consecutive samples = 60s

    THROTTLE_CLOCK_REF   = None  # set on first sample; baseline max clock seen
    THROTTLE_CLOCK_DROP  = 0.18  # 18% clock drop vs peak while load is high
    THROTTLE_LOAD_MIN    = 40.0  # GPU D3D % must be above this to flag throttle
    THROTTLE_CONFIRM     = 3     # consecutive low-clock samples before alerting

    # ── Cooldown: don't spam the same alert type ──────────────────────
    COOLDOWN_SAMPLES     = 40    # ~2 min between same-type alerts

    def __init__(self, parent=None):
        super().__init__(parent)
        self._temps: deque[float] = deque(maxlen=self.RISE_WINDOW + 1)
        self._clocks: deque[float] = deque(maxlen=10)
        self._sustain_count   = 0
        self._throttle_count  = 0
        self._peak_clock      = 0.0
        self._alerted: dict[str, int] = {}   # alert_type → samples since last fire
        self._any_active      = False

    # ------------------------------------------------------------------ slot
    def on_data(self, snap: dict) -> None:
        temp  = snap.get("gpu_temp")
        clock = snap.get("gpu_clock")
        d3d   = snap.get("gpu_d3d") or 0.0

        # Tick cooldown counters
        for k in list(self._alerted):
            self._alerted[k] += 1

        if temp is None:
            return

        self._temps.append(temp)

        # Update peak clock (the highest we've ever seen = baseline)
        if clock and clock > self._peak_clock:
            self._peak_clock = clock
        if clock:
            self._clocks.append(clock)

        fired_any = False

        # ── 1. Rising temperature ──────────────────────────────────────
        if (len(self._temps) >= self.RISE_WINDOW
                and temp >= self.RISE_MIN_TEMP):
            oldest = self._temps[0]
            # samples-1 intervals × 3s each
            elapsed_min = ((len(self._temps) - 1) * 3) / 60.0
            if elapsed_min > 0:
                rate = (temp - oldest) / elapsed_min
                if (rate >= self.RISE_RATE_C_PER_MIN
                        and self._cooldown_ok("rising")):
                    self._alerted["rising"] = 0
                    self.temp_rising.emit({
                        "type":    "rising",
                        "gpu_temp": temp,
                        "rate_c_per_min": round(rate, 1),
                        "message": (
                            f"GPU subiendo {rate:.1f}°C/min "
                            f"({oldest:.0f}→{temp:.0f}°C) — "
                            f"TDR posible en ~"
                            f"{max(1, int((95 - temp) / rate))} min"
                        ),
                    })
                    fired_any = True

        # ── 2. Sustained high temperature ─────────────────────────────
        if temp >= self.SUSTAIN_TEMP:
            self._sustain_count += 1
        else:
            self._sustain_count = 0

        if (self._sustain_count >= self.SUSTAIN_SAMPLES
                and self._cooldown_ok("sustained")):
            self._alerted["sustained"] = 0
            mins = round(self._sustain_count * 3 / 60, 1)
            self.temp_sustained.emit({
                "type":    "sustained",
                "gpu_temp": temp,
                "minutes":  mins,
                "message": (
                    f"GPU a {temp:.0f}°C por {mins} min — "
                    f"riesgo alto de TDR"
                ),
            })
            fired_any = True

        # ── 3. Throttle detection ──────────────────────────────────────
        if (clock and self._peak_clock > 0
                and d3d >= self.THROTTLE_LOAD_MIN):
            drop = (self._peak_clock - clock) / self._peak_clock
            if drop >= self.THROTTLE_CLOCK_DROP:
                self._throttle_count += 1
            else:
                self._throttle_count = 0

            if (self._throttle_count >= self.THROTTLE_CONFIRM
                    and self._cooldown_ok("throttle")):
                self._alerted["throttle"] = 0
                self.throttle.emit({
                    "type":       "throttle",
                    "gpu_temp":   temp,
                    "gpu_clock":  clock,
                    "peak_clock": self._peak_clock,
                    "drop_pct":   round(drop * 100, 1),
                    "message": (
                        f"Throttling detectado — clock bajó "
                        f"{drop*100:.0f}% "
                        f"({self._peak_clock:.0f}→{clock:.0f} MHz) "
                        f"bajo carga {d3d:.0f}%"
                    ),
                })
                fired_any = True

        # ── 4. Clear alert if everything cool again ───────────────────
        if (self._any_active
                and not fired_any
                and temp < self.RISE_MIN_TEMP
                and self._sustain_count == 0
                and self._throttle_count == 0):
            self._any_active = False
            self.alert_cleared.emit({"message": "GPU dentro de parámetros normales ✓"})

        if fired_any:
            self._any_active = True

    # ------------------------------------------------------------------ helpers
    def _cooldown_ok(self, key: str) -> bool:
        return self._alerted.get(key, self.COOLDOWN_SAMPLES + 1) > self.COOLDOWN_SAMPLES

    def update_settings(self, settings: dict) -> None:
        if "rise_rate" in settings:
            self.RISE_RATE_C_PER_MIN = float(settings["rise_rate"])
        if "sustain_temp" in settings:
            self.SUSTAIN_TEMP = float(settings["sustain_temp"])
        if "rise_min_temp" in settings:
            self.RISE_MIN_TEMP = float(settings["rise_min_temp"])
