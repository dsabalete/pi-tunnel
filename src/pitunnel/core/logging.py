"""
Structured JSON logging for PiTunnel.
"""
from __future__ import annotations

import logging
import sys
import time
from contextvars import ContextVar, Token
from typing import Any, Self

import orjson

# Context variables for structured logging
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
command_var: ContextVar[str | None] = ContextVar("command", default=None)
duration_var: ContextVar[float | None] = ContextVar("duration", default=None)
exit_code_var: ContextVar[int | None] = ContextVar("exit_code", default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables if present
        user_id = user_id_var.get()
        if user_id is not None:
            log_data["user_id"] = user_id

        command = command_var.get()
        if command is not None:
            log_data["command"] = command

        duration = duration_var.get()
        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)

        exit_code = exit_code_var.get()
        if exit_code is not None:
            log_data["exit_code"] = exit_code

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "getMessage"
            }:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return orjson.dumps(log_data).decode("utf-8")


def setup_logging(level: int = logging.INFO, json_format: bool = True) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level.
        json_format: If True, use JSON formatter; otherwise use standard formatter.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from third-party libraries
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class LoggingContext:
    """Context manager for structured logging context."""

    def __init__(
        self,
        user_id: int | None = None,
        command: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.command = command
        self.start_time = time.monotonic()
        self._user_token: Token[int | None] | None = None
        self._command_token: Token[str | None] | None = None
        self._duration_token: Token[float | None] | None = None

    def __enter__(self) -> Self:
        if self.user_id is not None:
            self._user_token = user_id_var.set(self.user_id)
        if self.command is not None:
            self._command_token = command_var.set(self.command)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration = time.monotonic() - self.start_time
        self._duration_token = duration_var.set(duration)

        if self._user_token is not None:
            user_id_var.reset(self._user_token)
        if self._command_token is not None:
            command_var.reset(self._command_token)
        if self._duration_token is not None:
            duration_var.reset(self._duration_token)

    def set_exit_code(self, code: int) -> None:
        """Set exit code for current context."""
        exit_code_var.set(code)