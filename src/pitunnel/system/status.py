"""System status collection for PiTunnel."""

from __future__ import annotations

import logging
import os
import shutil
import socket
import time
from dataclasses import dataclass
from typing import Optional

import psutil
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    cpu_temp_c: Optional[float]
    disk_root_percent: float
    disk_root_used_gb: float
    disk_root_total_gb: float
    disk_nas_percent: Optional[float]
    disk_nas_used_gb: Optional[float]
    disk_nas_total_gb: Optional[float]
    uptime_seconds: int
    local_ip: str
    public_ip: str


def _get_cpu_temp() -> Optional[float]:
    # Try thermal zone
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            val = int(f.read().strip())
            return val / 1000.0
    except Exception:
        pass
    # Fallback to sensors
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            if entries:
                return float(entries[0].current)
    except Exception:
        pass
    return None


def _get_local_ip() -> str:
    try:
        # Find first non-loopback IPv4
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address
    except Exception:
        pass
    return "0.0.0.0"


_public_ip_cache: dict = {"value": None, "ts": 0.0}
_CACHE_TTL = 600  # seconds


def _fetch_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=text", timeout=3) as resp:
            return resp.read().decode().strip()
    except Exception:
        return "unknown"


def _get_public_ip_cached() -> str:
    now = time.time()
    if _public_ip_cache["value"] is not None and now - _public_ip_cache["ts"] < _CACHE_TTL:
        return _public_ip_cache["value"]
    ip = _fetch_public_ip()
    _public_ip_cache["value"] = ip
    _public_ip_cache["ts"] = now
    return ip


def _get_disk_usage_shutil(path: str) -> tuple[int, int, int] | None:
    """Get disk usage using shutil.disk_usage (Python standard library).
    
    This is the recommended approach as it's more reliable than psutil
    in environments with mount namespace issues (Docker, chroot, etc.).
    """
    try:
        usage = shutil.disk_usage(path)
        return (usage.total, usage.used, usage.free)
    except Exception:
        return None


def _get_disk_usage_values(path: str) -> tuple[float, float, float] | None:
    """Get disk usage values (percent, used_gb, total_gb) for a path."""
    result = _get_disk_usage_shutil(path)
    
    if result is None:
        return None
    
    total, used, free = result
    total_gb = total / (1024**3)
    used_gb = used / (1024**3)
    percent = (used / total) * 100 if total > 0 else 0
    
    return (percent, used_gb, total_gb)


def get_system_status(disk_root_path: str = "/") -> SystemStatus:
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = ram.used / (1024**3)
    ram_total_gb = ram.total / (1024**3)
    
    # Detect if we are likely running in Docker where the container's "/"
    # (overlay filesystem) resides on the same host filesystem as /mnt/nas.
    # In that case disk_root_path should be overridden to point at the SD card.
    if disk_root_path == "/":
        try:
            if os.stat("/").st_dev == os.stat("/mnt/nas").st_dev:
                logger.warning(
                    "Root path '/' and '/mnt/nas' are on the same filesystem. "
                    "In Docker this usually means the overlay resides on the NAS; "
                    "set storage.disk_root_path to the SD card mount point."
                )
        except Exception:
            pass

    # Get disk usage for root filesystem (configurable; in Docker the overlay
    # filesystem may reside on a NAS mount, so the path can be overridden to
    # point at the actual SD card, e.g. the host root bind-mounted into the container).
    disk_values = _get_disk_usage_values(disk_root_path)
    if disk_values is None:
        disk_root_percent = 0.0
        disk_root_used_gb = 0.0
        disk_root_total_gb = 0.0
    else:
        disk_root_percent, disk_root_used_gb, disk_root_total_gb = disk_values
    
    # Get disk usage for NAS
    disk_nas_values = _get_disk_usage_values("/mnt/nas")
    if disk_nas_values is None:
        disk_nas_percent = None
        disk_nas_used_gb = None
        disk_nas_total_gb = None
    else:
        disk_nas_percent, disk_nas_used_gb, disk_nas_total_gb = disk_nas_values
    
    uptime = int(time.time() - psutil.boot_time())
    local_ip = _get_local_ip()
    cpu_temp = _get_cpu_temp()
    public_ip = _get_public_ip_cached()
    return SystemStatus(
        cpu_percent=cpu,
        ram_percent=ram_percent,
        ram_used_gb=ram_used_gb,
        ram_total_gb=ram_total_gb,
        cpu_temp_c=cpu_temp,
        disk_root_percent=disk_root_percent,
        disk_root_used_gb=disk_root_used_gb,
        disk_root_total_gb=disk_root_total_gb,
        disk_nas_percent=disk_nas_percent,
        disk_nas_used_gb=disk_nas_used_gb,
        disk_nas_total_gb=disk_nas_total_gb,
        uptime_seconds=uptime,
        local_ip=local_ip,
        public_ip=public_ip,
    )
