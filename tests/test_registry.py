"""Tests for command registry."""
from __future__ import annotations

import pytest

from pitunnel.commands.registry import CommandRegistry
from pitunnel.core.config import CommandAlias, CommandsConfig, Config, TelegramConfig


def make_config(aliases: dict[str, CommandAlias]) -> Config:
    """Create a test config with given aliases."""
    return Config(
        telegram=TelegramConfig(authorized_users=[123456789]),
        commands=CommandsConfig(aliases=aliases),
    )


def test_registry_load_simple_aliases() -> None:
    """Test loading simple command aliases."""
    config = make_config({
        "restart-mqtt": CommandAlias(command="systemctl restart mosquitto"),
    })

    registry = CommandRegistry(config)

    assert registry.validate_alias("restart-mqtt")
    assert not registry.validate_alias("invalid")


def test_registry_case_insensitive() -> None:
    """Test that aliases are case-insensitive."""
    config = make_config({
        "Restart-MQTT": CommandAlias(command="systemctl restart mosquitto"),
    })

    registry = CommandRegistry(config)

    assert registry.validate_alias("restart-mqtt")
    assert registry.validate_alias("RESTART-MQTT")
    assert registry.validate_alias("Restart-MQTT")


def test_registry_get_command_info() -> None:
    """Test getting command info."""
    config = make_config({
        "test-cmd": CommandAlias(
            command="echo test",
            destructive=True,
            confirm=True,
            description="Test command",
        ),
    })

    registry = CommandRegistry(config)
    info = registry.get("test-cmd")

    assert info is not None
    assert info.alias == "test-cmd"
    assert info.command == "echo test"
    assert info.destructive is True
    assert info.confirm is True
    assert info.description == "Test command"


def test_registry_requires_confirmation() -> None:
    """Test checking if command requires confirmation."""
    config = make_config({
        "safe-cmd": CommandAlias(command="echo safe"),
        "destructive-cmd": CommandAlias(command="rm -rf /", destructive=True, confirm=True),
    })

    registry = CommandRegistry(config)

    assert not registry.requires_confirmation("safe-cmd")
    assert registry.requires_confirmation("destructive-cmd")


def test_registry_list_commands() -> None:
    """Test listing all commands."""
    config = make_config({
        "zebra": CommandAlias(command="echo z"),
        "alpha": CommandAlias(command="echo a"),
    })

    registry = CommandRegistry(config)
    commands = registry.list_commands()

    assert len(commands) == 2
    assert commands[0].alias == "alpha"
    assert commands[1].alias == "zebra"


def test_registry_help_text() -> None:
    """Test generating help text shows only built-in handlers.
    
    External aliases from config are not shown in help because they
    require /cmd <alias> prefix, not direct invocation.
    Built-in commands like /sensors, /on, /off are hidden as they
    are not applicable to this setup.
    """
    config = make_config({
        "test": CommandAlias(command="echo test", description="Test command"),
    })

    registry = CommandRegistry(config)
    help_text = registry.get_help_text("es")

    assert "Comandos disponibles" in help_text
    # External aliases should NOT appear in help (they need /cmd prefix)
    assert "test" not in help_text
    assert "Test command" not in help_text
    # Built-in handlers should appear
    assert "/status" in help_text
    assert "/alerts" in help_text
    assert "/ai" in help_text
    assert "/help" in help_text
    assert "/cmd" in help_text  # Important: shows whitelist command usage
    # These should NOT appear (not applicable to this setup)
    assert "/sensors" not in help_text
    assert "/on" not in help_text
    assert "/off" not in help_text


def test_registry_duplicate_alias_raises() -> None:
    """Test that duplicate aliases (case-insensitive) raise error."""
    config = Config(
        telegram=TelegramConfig(authorized_users=[123456789]),
        commands=CommandsConfig(aliases={
            "test": CommandAlias(command="echo 1"),
            "TEST": CommandAlias(command="echo 2"),
        }),
    )

    with pytest.raises(ValueError, match="Duplicate command alias"):
        CommandRegistry(config)