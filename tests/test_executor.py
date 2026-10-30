"""
Tests for command executor.
"""
from __future__ import annotations

from pitunnel.commands.executor import CommandExecutor
from pitunnel.core.config import Config, LimitsConfig, TelegramConfig


def make_config(timeout: int = 10, max_output: int = 4000) -> Config:
    """Create a test config."""
    return Config(
        telegram=TelegramConfig(authorized_users=[123456789]),
        limits=LimitsConfig(command_timeout_s=timeout, max_output_chars=max_output),
    )


def test_executor_run_simple_command() -> None:
    """Test running a simple command."""
    config = make_config()
    executor = CommandExecutor(config)

    result = executor.run_alias("echo", "echo hello")

    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.stderr == ""


def test_executor_run_command_with_stderr() -> None:
    """Test running a command that writes to stderr."""
    config = make_config()
    executor = CommandExecutor(config)

    # Use a command that writes to stderr (ls non-existent file)
    result = executor.run_alias("stderr", "ls /nonexistent_directory_xyz")

    assert result.exit_code != 0
    assert result.stdout == ""
    assert "No such file" in result.stderr or "not found" in result.stderr.lower()


def test_executor_run_failing_command() -> None:
    """Test running a command that fails."""
    config = make_config()
    executor = CommandExecutor(config)

    result = executor.run_alias("false", "false")

    assert result.exit_code == 1


def test_executor_timeout() -> None:
    """Test command timeout."""
    config = make_config(timeout=1)
    executor = CommandExecutor(config)

    # sleep 2 should timeout with 1s limit
    result = executor.run_alias("sleep", "sleep 2")

    assert result.exit_code == -1
    assert "timed out" in result.stderr.lower() or result.duration_ms > 900


def test_executor_output_truncation() -> None:
    """Test output truncation."""
    config = make_config(max_output=20)
    executor = CommandExecutor(config)

    # Generate output longer than 20 chars
    result = executor.run_alias("long", "echo 'this is a very long output line'")

    assert len(result.stdout) <= 40  # 20 + truncation suffix
    assert result.truncated is True


def test_executor_invalid_command() -> None:
    """Test running an invalid command."""
    config = make_config()
    executor = CommandExecutor(config)

    result = executor.run_alias("invalid", "nonexistent_command_xyz")

    assert result.exit_code == -1
    assert "No such file" in result.stderr or "not found" in result.stderr.lower()