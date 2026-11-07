"""Tests for system status module."""

import time
import socket
from unittest.mock import patch, MagicMock

import pytest

from pitunnel.system.status import (
    get_system_status,
    _get_public_ip_cached,
    _public_ip_cache,
    _fetch_public_ip,
    _get_disk_usage_shutil,
    _get_disk_usage_values,
)


@pytest.fixture(autouse=True)
def reset_cache():
    _public_ip_cache["value"] = None
    _public_ip_cache["ts"] = 0.0
    yield
    _public_ip_cache["value"] = None
    _public_ip_cache["ts"] = 0.0


def test_get_system_status_mocked():
    """get_system_status returns expected fields with mocked disk usage."""
    # Create mock disk usage results (total, used, free) in bytes
    disk_root_result = (100 * 1024**3, 60 * 1024**3, 40 * 1024**3)  # 100GB total, 60GB used
    disk_nas_result = (200 * 1024**3, 60 * 1024**3, 140 * 1024**3)  # 200GB total, 60GB used

    def mock_shutil_disk_usage(path):
        # Create a mock object with total, used, free attributes
        class MockUsage:
            def __init__(self, total, used, free):
                self.total = total
                self.used = used
                self.free = free
        
        if path == "/":
            return MockUsage(*disk_root_result)
        elif path == "/mnt/nas":
            return MockUsage(*disk_nas_result)
        return None

    with patch("pitunnel.system.status.psutil.cpu_percent", return_value=12.5), \
         patch("pitunnel.system.status.psutil.virtual_memory") as vm, \
         patch("pitunnel.system.status.psutil.boot_time", return_value=1000), \
         patch("pitunnel.system.status.psutil.net_if_addrs") as net, \
         patch("pitunnel.system.status.time.time", return_value=2000), \
         patch("pitunnel.system.status._get_cpu_temp", return_value=55.0), \
         patch("pitunnel.system.status._fetch_public_ip", return_value="1.2.3.4"), \
         patch("pitunnel.system.status.shutil.disk_usage", side_effect=mock_shutil_disk_usage):
        # Mock virtual_memory with all attributes
        vm.return_value.percent = 45.0
        vm.return_value.used = 4 * 1024**3  # 4 GB
        vm.return_value.total = 8 * 1024**3  # 8 GB

        # net_if_addrs returns one interface with IPv4
        mock_addr = MagicMock()
        mock_addr.family = 2  # AF_INET
        mock_addr.address = "192.168.1.10"
        net.return_value = {"eth0": [mock_addr]}

        status = get_system_status()

    assert status.cpu_percent == 12.5
    assert status.ram_percent == 45.0
    assert status.ram_used_gb == 4.0
    assert status.ram_total_gb == 8.0
    assert status.cpu_temp_c == 55.0
    assert status.disk_root_percent == 60.0
    assert status.disk_root_used_gb == 60.0
    assert status.disk_root_total_gb == 100.0
    assert status.disk_nas_percent == 30.0
    assert status.disk_nas_used_gb == 60.0
    assert status.disk_nas_total_gb == 200.0
    assert status.uptime_seconds == 1000
    assert status.local_ip == "192.168.1.10"
    assert status.public_ip == "1.2.3.4"


def test_public_ip_cache():
    """Public IP is cached for 10 minutes."""
    call_count = {"n": 0}

    def fake_fetch():
        call_count["n"] += 1
        return "5.6.7.8"

    with patch("pitunnel.system.status._fetch_public_ip", side_effect=fake_fetch):
        ip1 = _get_public_ip_cached()
        ip2 = _get_public_ip_cached()
        assert ip1 == "5.6.7.8"
        assert ip2 == "5.6.7.8"
        assert call_count["n"] == 1


def test_public_ip_timeout_fallback():
    """_fetch_public_ip returns 'unknown' on timeout."""
    with patch("pitunnel.system.status.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = socket.timeout("Request timed out")
        result = _fetch_public_ip()
        assert result == "unknown"


def test_public_ip_generic_error_fallback():
    """_fetch_public_ip returns 'unknown' on any error."""
    with patch("pitunnel.system.status.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network error")
        result = _fetch_public_ip()
        assert result == "unknown"


def test_get_system_status_cache_expiry():
    """Public IP cache expires after 10 minutes."""
    call_count = {"n": 0}

    def fake_fetch():
        call_count["n"] += 1
        return f"1.2.3.{call_count['n']}"

    with patch("pitunnel.system.status._fetch_public_ip", side_effect=fake_fetch):
        # First call
        ip1 = _get_public_ip_cached()
        assert ip1 == "1.2.3.1"
        assert call_count["n"] == 1

        # Second call within cache TTL
        ip2 = _get_public_ip_cached()
        assert ip2 == "1.2.3.1"
        assert call_count["n"] == 1

        # Simulate cache expiry by setting old timestamp
        _public_ip_cache["ts"] = time.time() - 700  # 11+ minutes ago

        # Third call should fetch new IP
        ip3 = _get_public_ip_cached()
        assert ip3 == "1.2.3.2"
        assert call_count["n"] == 2


def test_get_disk_usage_shutil():
    """Test _get_disk_usage_shutil returns correct values."""
    with patch("pitunnel.system.status.shutil.disk_usage") as mock_disk_usage:
        mock_usage = MagicMock()
        mock_usage.total = 100 * 1024**3
        mock_usage.used = 60 * 1024**3
        mock_usage.free = 40 * 1024**3
        mock_disk_usage.return_value = mock_usage

        result = _get_disk_usage_shutil("/test/path")
        total, used, free = result
        
        assert total == 100 * 1024**3
        assert used == 60 * 1024**3
        assert free == 40 * 1024**3


def test_get_disk_usage_values_success():
    """Test successful disk usage values retrieval."""
    with patch("pitunnel.system.status.shutil.disk_usage") as mock_disk_usage:
        mock_usage = MagicMock()
        mock_usage.total = 100 * 1024**3
        mock_usage.used = 60 * 1024**3
        mock_usage.free = 40 * 1024**3
        mock_disk_usage.return_value = mock_usage

        percent, used_gb, total_gb = _get_disk_usage_values("/")
        assert percent == 60.0
        assert used_gb == 60.0
        assert total_gb == 100.0
