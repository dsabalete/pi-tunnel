"""
Typed exceptions and error handling for PiTunnel.
"""
from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


class PiTunnelError(Exception):
    """Base exception for PiTunnel errors."""

    def __init__(self, message: str, user_message: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.user_message = user_message or "⚠ Error interno. Revisa los logs."


class UnauthorizedError(PiTunnelError):
    """Raised when user is not authorized."""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            f"Unauthorized access attempt by user {user_id}",
            "⛔ No estás autorizado para usar este bot."
        )
        self.user_id = user_id


class WhitelistError(PiTunnelError):
    """Raised when command is not in whitelist."""

    def __init__(self, alias: str) -> None:
        super().__init__(
            f"Command '{alias}' not in whitelist",
            "🚫 Comando fuera de la lista permitida."
        )
        self.alias = alias


class TimeoutError(PiTunnelError):
    """Raised when command execution times out."""

    def __init__(self, timeout: int) -> None:
        super().__init__(
            f"Command timed out after {timeout}s",
            f"⏱ Tiempo de espera agotado ({timeout} s)."
        )
        self.timeout = timeout


class CommandExecutionError(PiTunnelError):
    """Raised when command execution fails."""

    def __init__(self, alias: str, exit_code: int, stderr: str) -> None:
        super().__init__(
            f"Command '{alias}' failed with exit code {exit_code}: {stderr}",
            f"❌ Error ejecutando '{alias}' (código {exit_code})."
        )
        self.alias = alias
        self.exit_code = exit_code
        self.stderr = stderr


class ConfirmationExpiredError(PiTunnelError):
    """Raised when confirmation callback expires."""

    def __init__(self) -> None:
        super().__init__(
            "Confirmation expired",
            "⏱ La confirmación ha expirado. Intenta de nuevo."
        )


class ConfirmationRequiredError(PiTunnelError):
    """Raised when confirmation is required but not provided."""
    
    def __init__(self, alias: str) -> None:
        super().__init__(
            f"Confirmation required for '{alias}'",
            f"⚠️ Acción '{alias}' requiere confirmación."
        )
        self.alias = alias


# Error code mapping for user-facing messages
ERROR_MESSAGES: dict[str, str] = {
    "E_UNAUTHORIZED": "⛔ No estás autorizado para usar este bot.",
    "E_UNKNOWN_CMD": "❓ Comando no reconocido. Usa /help.",
    "E_WHITELIST": "🚫 Comando fuera de la lista permitida.",
    "E_TIMEOUT": "⏱ Tiempo de espera agotado (10 s).",
    "E_INTERNAL": "⚠ Error interno. Revisa los logs.",
    "E_CONFIRMATION_EXPIRED": "⏱ La confirmación ha expirado. Intenta de nuevo.",
    "E_CONFIRMATION_REQUIRED": "⚠️ Esta acción requiere confirmación.",
}


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler for the bot.

    Args:
        update: The update that caused the error.
        context: The context containing the error.
    """
    error = context.error

    # Log the error with context
    log_data: dict[str, Any] = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if isinstance(update, Update):
        if update.effective_user:
            log_data["user_id"] = update.effective_user.id
        if update.message:
            log_data["message_text"] = update.message.text
        if update.callback_query:
            log_data["callback_data"] = update.callback_query.data

    logger.error("Unhandled error", extra=log_data, exc_info=error)

    # Send user-friendly message if possible
    if isinstance(update, Update) and update.effective_message:
        user_message = "⚠ Error interno. Revisa los logs."

        if isinstance(error, PiTunnelError):
            user_message = error.user_message
        elif isinstance(error, UnauthorizedError):
            user_message = ERROR_MESSAGES["E_UNAUTHORIZED"]
        elif isinstance(error, WhitelistError):
            user_message = ERROR_MESSAGES["E_WHITELIST"]
        elif isinstance(error, TimeoutError):
            user_message = ERROR_MESSAGES["E_TIMEOUT"]
        elif isinstance(error, ConfirmationExpiredError):
            user_message = ERROR_MESSAGES["E_CONFIRMATION_EXPIRED"]
        elif isinstance(error, ConfirmationRequiredError):
            user_message = ERROR_MESSAGES["E_CONFIRMATION_REQUIRED"]

        try:
            await update.effective_message.reply_text(user_message)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to send error message to user", extra={"error": str(e)})