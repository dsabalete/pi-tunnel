"""
Command executor for PiTunnel.
"""
from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Optional

from pitunnel.core.config import Config
from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CommandResult:
    """Result of command execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    truncated: bool = False


class CommandExecutor:
    """
    Executes whitelisted commands safely.

    Uses subprocess.run with shell=False, timeout, and output truncation.
    """

    def __init__(self, config: Config, history_logger: Optional[Any] = None) -> None:
        """
        Initialize executor with config.

        Args:
            config: Configuration object.
            history_logger: Optional History instance for logging commands.
        """
        self.timeout = config.limits.command_timeout_s
        self.max_output_chars = config.limits.max_output_chars
        self.history_logger = history_logger

    def run_alias(
        self,
        alias: str,
        command: str,
        user_id: int = 0,
        cmd_args: str = "",
    ) -> CommandResult:
        """
        Execute a command by alias.

        Args:
            alias: Command alias (for logging).
            command: Full command string to execute.
            user_id: Telegram user ID for history logging.
            cmd_args: Telegram command arguments for history logging.

        Returns:
            CommandResult with execution details.
        """
        # Parse command into args (no shell interpolation)
        args = shlex.split(command)

        logger.info(
            "Executing command",
            extra={"alias": alias, "cmd_args": args, "timeout": self.timeout}
        )

        start = time.monotonic()
        try:
            result = subprocess.run(
                args,
                check=False,
                timeout=self.timeout,
                capture_output=True,
                text=True,
                shell=False,  # Critical: never use shell=True
            )
        except subprocess.TimeoutExpired as e:
            duration = time.monotonic() - start
            logger.warning(
                "Command timed out",
                extra={"alias": alias, "timeout": self.timeout}
            )
            result = CommandResult(
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration_ms=duration * 1000,
            )
            self._log_command(alias, user_id, cmd_args, result)
            return result
        except Exception as e:
            duration = time.monotonic() - start
            logger.error(
                "Command execution failed",
                extra={"alias": alias, "error": str(e)},
                exc_info=e
            )
            result = CommandResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration * 1000,
            )
            self._log_command(alias, user_id, cmd_args, result)
            return result

        duration = time.monotonic() - start

        # Truncate output if needed
        stdout = result.stdout
        stderr = result.stderr
        truncated = False

        if len(stdout) > self.max_output_chars:
            stdout = stdout[:self.max_output_chars] + "\n… (truncado)"
            truncated = True

        if len(stderr) > self.max_output_chars:
            stderr = stderr[:self.max_output_chars] + "\n… (truncado)"
            truncated = True

        logger.info(
            "Command completed",
            extra={
                "alias": alias,
                "exit_code": result.returncode,
                "duration_ms": round(duration * 1000, 2),
                "stdout_len": len(result.stdout),
                "stderr_len": len(result.stderr),
            }
        )

        result = CommandResult(
            exit_code=result.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration * 1000,
            truncated=truncated,
        )
        self._log_command(alias, user_id, cmd_args, result)
        return result

    def _log_command(
        self,
        alias: str,
        user_id: int,
        cmd_args: str,
        result: CommandResult,
    ) -> None:
        """Log command execution to history if history_logger is set."""
        if self.history_logger is not None:
            try:
                self.history_logger.log_command(
                    user_id=user_id,
                    alias=alias,
                    args=cmd_args,
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            except Exception as e:
                logger.error(
                    "Failed to log command to history",
                    extra={"alias": alias, "error": str(e)},
                    exc_info=e,
                )