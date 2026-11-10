"""
core/disk_monitor.py
SMART and disk health monitoring via PowerShell.
Runs a one-shot check on demand (not a thread) since SMART polling is slow.

Returns a list of disk dicts with health, temp, hours, wear.
"""
import json
import subprocess


def _run_ps(script: str) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, timeout=15
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


def get_disk_health() -> list[dict]:
    """
    Returns a list of dicts, one per physical disk:
      name, media_type, health, size_gb, temp_c, wear_pct,
      power_on_hours, read_errors, write_errors
    """
    ps = r"""
$disks = Get-PhysicalDisk -ErrorAction SilentlyContinue
$results = @()
foreach ($disk in $disks) {
    $rel = $disk | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue
    $obj = [PSCustomObject]@{
        name            = $disk.FriendlyName
        media_type      = $disk.MediaType
        health          = $disk.HealthStatus
        size_gb         = [math]::Round($disk.Size / 1GB, 1)
        temp_c          = if ($rel) { $rel.Temperature } else { $null }
        wear_pct        = if ($rel) { $rel.Wear } else { $null }
        power_on_hours  = if ($rel) { $rel.PowerOnHours } else { $null }
        read_errors     = if ($rel) { $rel.ReadErrorsTotal } else { $null }
        write_errors    = if ($rel) { $rel.WriteErrorsTotal } else { $null }
    }
    $results += $obj
}
$results | ConvertTo-Json -Compress
"""
    raw = _run_ps(ps)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, dict):   # single disk → wrap in list
            data = [data]
        return [_clean(d) for d in data]
    except Exception as e:
        print(f"[DiskMonitor] JSON parse error: {e}")
        return []


def _clean(d: dict) -> dict:
    return {
        "name":           d.get("name") or "Disk",
        "media_type":     d.get("media_type") or "Unknown",
        "health":         d.get("health") or "Unknown",
        "size_gb":        d.get("size_gb"),
        "temp_c":         d.get("temp_c"),
        "wear_pct":       d.get("wear_pct"),
        "power_on_hours": d.get("power_on_hours"),
        "read_errors":    d.get("read_errors"),
        "write_errors":   d.get("write_errors"),
    }


def health_summary(disks: list[dict]) -> str:
    """Returns a one-line health summary string."""
    if not disks:
        return "No se pudo leer SMART"
    warnings = []
    for d in disks:
        if d["health"] not in ("Healthy", None, ""):
            warnings.append(f"{d['name']}: {d['health']}")
        if d.get("temp_c") and d["temp_c"] > 55:
            warnings.append(f"{d['name']}: {d['temp_c']}°C")
        if d.get("wear_pct") and d["wear_pct"] > 80:
            warnings.append(f"{d['name']}: desgaste {d['wear_pct']}%")
    return " | ".join(warnings) if warnings else "✅ Todos los discos saludables"
