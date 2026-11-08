"""Tests for configuration loading."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pitunnel.core.config import Config, load_env


def test_config_load_defaults() -> None:
    """Test loading config with minimal YAML."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
  language: es
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    assert config.telegram.authorized_users == [123456789]
    assert config.telegram.language == "es"
    assert config.commands.aliases == {}
    assert config.sensors.sensors == []
    assert config.actuators.actuators == []
    assert config.limits.command_timeout_s == 10
    assert config.limits.max_output_chars == 4000
    assert config.limits.history_retention_days == 30

    Path(f.name).unlink()


def test_config_load_with_aliases() -> None:
    """Test loading config with command aliases."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
commands:
  aliases:
    restart-mqtt: "systemctl restart mosquitto"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    assert "restart-mqtt" in config.commands.aliases
    assert config.commands.aliases["restart-mqtt"].command == "systemctl restart mosquitto"

    Path(f.name).unlink()


def test_config_load_with_disk_usage_alias() -> None:
    """Test loading config still supports disk-usage alias for /cmd."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
commands:
  aliases:
    disk-usage: "df -h /"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    assert "disk-usage" in config.commands.aliases
    assert config.commands.aliases["disk-usage"].command == "df -h /"

    Path(f.name).unlink()


def test_config_load_with_destructive_alias() -> None:
    """Test loading config with destructive alias."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
commands:
  aliases:
    reboot:
      command: "sudo reboot"
      destructive: true
      confirm: true
      description: "Reboot the system"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    alias = config.commands.aliases["reboot"]
    assert alias.command == "sudo reboot"
    assert alias.destructive is True
    assert alias.confirm is True
    assert alias.description == "Reboot the system"

    Path(f.name).unlink()


def test_config_load_with_sensors() -> None:
    """Test loading config with sensors."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
sensors:
  - id: temp-salon
    type: dht22
    pin: 4
    interval_s: 60
    alert:
      when: "> 27.5"
      cooldown_min: 30
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    assert len(config.sensors.sensors) == 1
    sensor = config.sensors.sensors[0]
    assert sensor.id == "temp-salon"
    assert sensor.type == "dht22"
    assert sensor.pin == 4
    assert sensor.interval_s == 60
    assert sensor.alert is not None
    assert sensor.alert["when"] == "> 27.5"
    assert sensor.alert["cooldown_min"] == 30

    Path(f.name).unlink()


def test_config_load_with_actuators() -> None:
    """Test loading config with actuators."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
actuators:
  - id: luz-porche
    type: relay
    pin: 17
    confirm: false
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = Config.load(f.name)

    assert len(config.actuators.actuators) == 1
    actuator = config.actuators.actuators[0]
    assert actuator.id == "luz-porche"
    assert actuator.type == "relay"
    assert actuator.pin == 17
    assert actuator.confirm is False

    Path(f.name).unlink()


def test_config_load_invalid_duplicate_alias() -> None:
    """Test that duplicate aliases raise error."""
    config_yaml = """
telegram:
  authorized_users: [123456789]
commands:
  aliases:
    test: "echo test"
    TEST: "echo test2"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()

    with pytest.raises(ValueError, match="Duplicate command alias"):
        Config.load(f.name)

    Path(f.name).unlink()


def test_load_env() -> None:
    """Test loading environment variables."""
    env_content = """
TELEGRAM_BOT_TOKEN=test_token_123
OTHER_VAR=value
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        f.flush()
        env_vars = load_env(f.name)

    assert env_vars["TELEGRAM_BOT_TOKEN"] == "test_token_123"
    assert env_vars["OTHER_VAR"] == "value"

    Path(f.name).unlink()