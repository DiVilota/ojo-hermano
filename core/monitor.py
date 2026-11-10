"""
core/monitor.py
QThread that polls LibreHardwareMonitor every 3 seconds via pythonnet.
"""
import os
import sys
import time

from PyQt6.QtCore import QThread, pyqtSignal


class MonitorThread(QThread):
    data_ready = pyqtSignal(dict)

    DLL_PATH = "C:/Users/diego/hermes_monitor/LibreHardwareMonitorLib.dll"

    def __init__(self, dll_path: str = None, parent=None):
        super().__init__(parent)
        self._dll_path = dll_path or self.DLL_PATH
        self._running = False

    # ------------------------------------------------------------------
    def run(self):
        self._running = True
        try:
            import clr  # pythonnet

            dll_dir  = os.path.dirname(os.path.abspath(self._dll_path))
            dll_name = os.path.splitext(os.path.basename(self._dll_path))[0]
            if dll_dir not in sys.path:
                sys.path.insert(0, dll_dir)
            clr.AddReference(dll_name)

            from LibreHardwareMonitor.Hardware import Computer  # noqa: E402

            computer = Computer()
            computer.IsCpuEnabled     = True
            computer.IsGpuEnabled     = True
            computer.IsMemoryEnabled  = True
            computer.IsNetworkEnabled = True
            computer.IsStorageEnabled = True
            computer.Open()

            try:
                while self._running:
                    try:
                        snapshot = self._poll(computer)
                        self.data_ready.emit(snapshot)
                    except Exception as exc:
                        print(f"[Monitor] Poll error: {exc}")
                    time.sleep(3)
            finally:
                try:
                    computer.Close()
                except Exception:
                    pass

        except Exception as exc:
            print(f"[Monitor] Fatal startup error: {exc}")

    # ------------------------------------------------------------------
    def stop(self):
        self._running = False
        self.wait(6000)

    # ------------------------------------------------------------------
    def _poll(self, computer) -> dict:
        snapshot = {
            "ts":           time.time(),
            "cpu_load":     None,
            "cpu_max_core": None,
            "cpu_temp":     None,
            "cpu_threads":  [],
            "gpu_temp":     None,
            "gpu_load":     None,
            "gpu_d3d":      None,
            "gpu_fan_rpm":  None,
            "gpu_fan_pct":  None,
            "gpu_clock":    None,
            "gpu_mem_clock":None,
            "gpu_voltage":  None,
            "gpu_vram_used":None,
            "gpu_vram_total":None,
            "gpu_fps":      None,
            "ram_used":     None,
            "ram_avail":    None,
            "ram_load":     None,
            "net_dl":       None,
            "net_ul":       None,
            "net_pct":      None,
        }

        for hw in computer.Hardware:
            hw.Update()
            for sub in hw.SubHardware:
                sub.Update()

            hw_type = str(hw.HardwareType)

            if "Cpu" in hw_type:
                self._collect_cpu(hw, snapshot)
            elif "Gpu" in hw_type:
                self._collect_gpu(hw, snapshot)
            elif "Memory" in hw_type:
                self._collect_memory(hw, snapshot)
            elif "Network" in hw_type:
                self._collect_network(hw, snapshot)

        return snapshot

    # ------------------------------------------------------------------
    @staticmethod
    def _fval(sensor) -> float | None:
        """Safely extract float from a .NET nullable sensor value."""
        try:
            v = sensor.Value
            if v is None:
                return None
            return float(v)
        except Exception:
            return None

    # ------------------------------------------------------------------
    def _collect_cpu(self, hw, snap: dict):
        threads = []
        for s in hw.Sensors:
            st   = str(s.SensorType)
            name = str(s.Name)
            val  = self._fval(s)

            if "Load" in st:
                if "Total" in name or "CPU Total" in name:
                    snap["cpu_load"] = val
                elif "Core Max" in name or "CPU Core Max" in name:
                    snap["cpu_max_core"] = val
                elif "Core #" in name:
                    # Exclude aggregated "Max" cores
                    threads.append({"name": name, "val": val})

            elif "Temperature" in st:
                if snap["cpu_temp"] is None:
                    if "Package" in name or "Core #0" in name or "CPU Package" in name:
                        snap["cpu_temp"] = val

        # Sort by core number so Core #0, #1 … appear in order
        threads.sort(key=lambda x: x["name"])
        snap["cpu_threads"] = threads

    # ------------------------------------------------------------------
    def _collect_gpu(self, hw, snap: dict):
        for s in hw.Sensors:
            st   = str(s.SensorType)
            name = str(s.Name)
            val  = self._fval(s)

            if "Temperature" in st:
                if "GPU Core" in name or "GPU" in name:
                    if snap["gpu_temp"] is None:
                        snap["gpu_temp"] = val

            elif "Load" in st:
                if "D3D 3D" in name:
                    snap["gpu_d3d"] = val
                elif "GPU Core" in name or "GPU Graphics" in name:
                    snap["gpu_load"] = val

            elif "Fan" in st:
                # Fan type gives RPM
                snap["gpu_fan_rpm"] = val

            elif "Control" in st:
                # Control type gives fan %
                if "Fan" in name:
                    snap["gpu_fan_pct"] = val

            elif "Clock" in st:
                if "GPU Core" in name:
                    snap["gpu_clock"] = val
                elif "GPU Memory" in name:
                    snap["gpu_mem_clock"] = val

            elif "Voltage" in st:
                if "GPU Core" in name:
                    snap["gpu_voltage"] = val

            elif "SmallData" in st:
                if "GPU Memory Used" in name or "VRAM Used" in name:
                    snap["gpu_vram_used"] = val
                elif (
                    "D3D Dedicated Memory Total" in name
                    or "GPU Memory Total" in name
                    or "VRAM Total" in name
                ):
                    snap["gpu_vram_total"] = val

            elif "Data" in st:
                if "GPU Memory Used" in name:
                    snap["gpu_vram_used"] = val
                elif "GPU Memory Total" in name:
                    snap["gpu_vram_total"] = val

            elif "Factor" in st:
                if "Fullscreen FPS" in name or "FPS" in name:
                    snap["gpu_fps"] = val if (val is not None and val > 0) else None

    # ------------------------------------------------------------------
    def _collect_memory(self, hw, snap: dict):
        for s in hw.Sensors:
            st   = str(s.SensorType)
            name = str(s.Name)
            val  = self._fval(s)

            if "Data" in st or "SmallData" in st:
                if "Used" in name:
                    snap["ram_used"] = val
                elif "Available" in name or "Free" in name:
                    snap["ram_avail"] = val

            elif "Load" in st:
                if "Memory" in name or "Virtual" not in name:
                    snap["ram_load"] = val

    # ------------------------------------------------------------------
    def _collect_network(self, hw, snap: dict):
        for s in hw.Sensors:
            st   = str(s.SensorType)
            name = str(s.Name)
            val  = self._fval(s)

            if "Throughput" in st or "Data" in st:
                if "Download" in name:
                    snap["net_dl"] = val
                elif "Upload" in name:
                    snap["net_ul"] = val

            elif "Load" in st:
                snap["net_pct"] = val
