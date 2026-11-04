"""System status collection for PiTunnel."""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Optional

import psutil
import urllib.request
import urllib.error


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
    # Fallback to psutil
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


def get_system_status() -> SystemStatus:
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = ram.used / (1024**3)
    ram_total_gb = ram.total / (1024**3)
    disk_root = psutil.disk_usage("/")
    disk_root_percent = disk_root.percent
    disk_root_used_gb = disk_root.used / (1024**3)
    disk_root_total_gb = disk_root.total / (1024**3)
    try:
        disk_nas = psutil.disk_usage("/mnt/nas")
        disk_nas_percent = disk_nas.percent
        disk_nas_used_gb = disk_nas.used / (1024**3)
        disk_nas_total_gb = disk_nas.total / (1024**3)
    except Exception:
        disk_nas = None
        disk_nas_percent = None
        disk_nas_used_gb = None
        disk_nas_total_gb = None
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
