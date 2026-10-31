"""Tests for system status module."""

import time
from unittest.mock import patch, MagicMock

import pytest

from pitunnel.system.status import get_system_status, _get_public_ip_cached, _public_ip_cache


@pytest.fixture(autouse=True)
def reset_cache():
    _public_ip_cache["value"] = None
    _public_ip_cache["ts"] = 0.0
    yield
    _public_ip_cache["value"] = None
    _public_ip_cache["ts"] = 0.0


def test_get_system_status_mocked():
    """get_system_status returns expected fields with mocked psutil."""
    with patch("pitunnel.system.status.psutil.cpu_percent", return_value=12.5), \
         patch("pitunnel.system.status.psutil.virtual_memory") as vm, \
         patch("pitunnel.system.status.psutil.disk_usage") as du, \
         patch("pitunnel.system.status.psutil.boot_time", return_value=1000), \
         patch("pitunnel.system.status.psutil.net_if_addrs") as net, \
         patch("pitunnel.system.status.time.time", return_value=2000), \
         patch("pitunnel.system.status._get_cpu_temp", return_value=55.0), \
         patch("pitunnel.system.status._fetch_public_ip", return_value="1.2.3.4"):
        vm.return_value.percent = 45.0
        # disk_usage called twice, return different mocks
        du.side_effect = [
            MagicMock(percent=60.0),
            MagicMock(percent=30.0),
        ]
        # net_if_addrs returns one interface with IPv4
        mock_addr = MagicMock()
        mock_addr.family = 2  # AF_INET
        mock_addr.address = "192.168.1.10"
        net.return_value = {"eth0": [mock_addr]}

        status = get_system_status()

    assert status.cpu_percent == 12.5
    assert status.ram_percent == 45.0
    assert status.cpu_temp_c == 55.0
    assert status.disk_root_percent == 60.0
    assert status.disk_nas_percent == 30.0
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
