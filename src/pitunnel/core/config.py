"""
Configuration loading for PiTunnel.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    authorized_users: list[int] = field(default_factory=list)
    language: str = "es"


@dataclass
class CommandAlias:
    """Single command alias configuration."""
    command: str
    destructive: bool = False
    confirm: bool = False
    description: str = ""


@dataclass
class CommandsConfig:
    """Commands configuration."""
    aliases: dict[str, CommandAlias] = field(default_factory=dict)


@dataclass
class SensorConfig:
    """Single sensor configuration."""
    id: str
    type: str
    pin: int | None = None
    interval_s: int = 60
    address: int | None = None
    alert: dict[str, Any] | None = None


@dataclass
class SensorsConfig:
    """Sensors configuration."""
    sensors: list[SensorConfig] = field(default_factory=list)


@dataclass
class ActuatorConfig:
    """Single actuator configuration."""
    id: str
    type: str
    pin: int
    confirm: bool = False


@dataclass
class ActuatorsConfig:
    """Actuators configuration."""
    actuators: list[ActuatorConfig] = field(default_factory=list)


@dataclass
class LimitsConfig:
    """Limits configuration."""
    command_timeout_s: int = 10
    max_output_chars: int = 4000
    history_retention_days: int = 30


@dataclass
class Config:
    """Main configuration container."""
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    sensors: SensorsConfig = field(default_factory=SensorsConfig)
    actuators: ActuatorsConfig = field(default_factory=ActuatorsConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> Config:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml. If None, searches default locations.

        Returns:
            Parsed Config object.
        """
        if config_path is None:
            # Search default locations
            search_paths = [
                Path("/etc/pitunnel/config.yaml"),
                Path(__file__).parent.parent.parent.parent / "config" / "config.yaml",
                Path.cwd() / "config" / "config.yaml",
            ]
            for path in search_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                raise FileNotFoundError("config.yaml not found in default locations")

        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        return cls._parse(raw)

    @classmethod
    def _parse(cls, raw: dict[str, Any]) -> Config:
        """Parse raw YAML into Config object."""
        config = Config()

        # Telegram
        if "telegram" in raw:
            tg = raw["telegram"]
            config.telegram = TelegramConfig(
                authorized_users=tg.get("authorized_users", []),
                language=tg.get("language", "es"),
            )

        # Commands
        if "commands" in raw:
            cmd = raw["commands"]
            aliases = {}
            # Check for duplicate aliases (case-insensitive)
            seen = set()
            for alias in cmd.get("aliases", {}):
                lower = alias.lower()
                if lower in seen:
                    raise ValueError(f"Duplicate command alias (case-insensitive): {alias}")
                seen.add(lower)
            for alias, value in cmd.get("aliases", {}).items():
                if isinstance(value, str):
                    aliases[alias] = CommandAlias(command=value)
                elif isinstance(value, dict):
                    aliases[alias] = CommandAlias(
                        command=value.get("command", ""),
                        destructive=value.get("destructive", False),
                        confirm=value.get("confirm", False),
                        description=value.get("description", ""),
                    )
            config.commands = CommandsConfig(aliases=aliases)

        # Sensors
        if "sensors" in raw:
            sensors = []
            for s in raw["sensors"]:
                sensors.append(SensorConfig(
                    id=s["id"],
                    type=s["type"],
                    pin=s.get("pin"),
                    interval_s=s.get("interval_s", 60),
                    address=s.get("address"),
                    alert=s.get("alert"),
                ))
            config.sensors = SensorsConfig(sensors=sensors)

        # Actuators
        if "actuators" in raw:
            actuators = []
            for a in raw["actuators"]:
                actuators.append(ActuatorConfig(
                    id=a["id"],
                    type=a["type"],
                    pin=a["pin"],
                    confirm=a.get("confirm", False),
                ))
            config.actuators = ActuatorsConfig(actuators=actuators)

        # Limits
        if "limits" in raw:
            lim = raw["limits"]
            config.limits = LimitsConfig(
                command_timeout_s=lim.get("command_timeout_s", 10),
                max_output_chars=lim.get("max_output_chars", 4000),
                history_retention_days=lim.get("history_retention_days", 30),
            )

        return config


def load_env(env_path: str | Path | None = None) -> dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file. If None, searches default locations.

    Returns:
        Dictionary of environment variables.
    """
    if env_path is None:
        search_paths = [
            Path("/etc/pitunnel.env"),
            Path(__file__).parent.parent.parent.parent / "config" / "pitunnel.env",
            Path.cwd() / "config" / "pitunnel.env",
        ]
        for path in search_paths:
            if path.exists():
                env_path = path
                break

    env_vars = {}
    if env_path and Path(env_path).exists():
        with Path(env_path).open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
                    os.environ.setdefault(key.strip(), value.strip())

    return env_vars