"""
core/autostart.py
Manage Windows startup entry for Ojo Hermano via the Registry.
Key: HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
"""
import os
import sys
import winreg

APP_NAME = "OjoHermano"


def _get_launch_cmd() -> str:
    """Build the command string to launch the app."""
    python = sys.executable
    script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "main.py")
    )
    return f'"{python}" "{script}"'


def is_enabled() -> bool:
    """Return True if the autostart registry entry exists."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def enable() -> bool:
    """Add Ojo Hermano to Windows startup. Returns True on success."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_launch_cmd())
        winreg.CloseKey(key)
        print(f"[Autostart] Enabled: {_get_launch_cmd()}")
        return True
    except Exception as e:
        print(f"[Autostart] Failed to enable: {e}")
        return False


def disable() -> bool:
    """Remove Ojo Hermano from Windows startup. Returns True on success."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass   # already not there
        winreg.CloseKey(key)
        print("[Autostart] Disabled")
        return True
    except Exception as e:
        print(f"[Autostart] Failed to disable: {e}")
        return False


def toggle() -> bool:
    """Toggle the autostart state. Returns the new state (True=enabled)."""
    if is_enabled():
        disable()
        return False
    else:
        enable()
        return True
