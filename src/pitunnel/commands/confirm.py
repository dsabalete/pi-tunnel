"""
Confirmation manager for destructive commands.
"""
from __future__ import annotations

import hmac
import time
from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from pitunnel.core.errors import ConfirmationExpiredError, ConfirmationRequiredError
from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PendingConfirmation:
    """Pending confirmation data."""
    alias: str
    user_id: int
    chat_id: int
    message_id: int | None
    created_at: float
    callback_data: str


class ConfirmationManager:
    """
    Manages inline button confirmations for destructive commands.

    Uses HMAC-signed callback data with 60-second expiry.
    """

    CONFIRMATION_TTL = 60  # seconds
    HMAC_SECRET = b"pitunnel-confirm-secret"  # In production, load from config

    def __init__(self) -> None:
        self._pending: dict[str, PendingConfirmation] = {}

    def create_confirmation(
        self,
        alias: str,
        user_id: int,
        chat_id: int,
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Create a confirmation request.

        Args:
            alias: Command alias.
            user_id: User requesting confirmation.
            chat_id: Chat ID.

        Returns:
            Tuple of (callback_data, keyboard_markup).
        """
        # Create callback data with timestamp and HMAC
        timestamp = int(time.time())
        data = f"{alias}:{user_id}:{timestamp}"
        signature = hmac.new(
            self.HMAC_SECRET,
            data.encode(),
            "sha256"
        ).hexdigest()[:16]
        callback_data = f"confirm:{data}:{signature}"

        # Store pending confirmation
        pending = PendingConfirmation(
            alias=alias,
            user_id=user_id,
            chat_id=chat_id,
            message_id=None,
            created_at=time.time(),
            callback_data=callback_data,
        )
        self._pending[callback_data] = pending

        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=callback_data),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel:{alias}"),
            ]
        ])

        return callback_data, keyboard

    def verify_confirmation(self, callback_data: str, user_id: int) -> PendingConfirmation:
        """
        Verify and consume a confirmation callback.

        Args:
            callback_data: Callback data from inline button.
            user_id: User who pressed the button.

        Returns:
            PendingConfirmation if valid.

        Raises:
            ConfirmationExpiredError: If confirmation expired or invalid.
            ConfirmationRequiredError: If confirmation not found.
        """
        if not callback_data.startswith("confirm:"):
            raise ConfirmationExpiredError()

        # Parse callback data: confirm:alias:user_id:timestamp:signature
        try:
            parts = callback_data.split(":")
            if len(parts) != 5:
                raise ValueError("Invalid callback data format")
            _, alias, req_user_id_str, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            req_user_id = int(req_user_id_str)
        except (ValueError, IndexError):
            raise ConfirmationExpiredError()

        # Verify HMAC
        expected_data = f"{alias}:{req_user_id}:{timestamp}"
        expected_signature = hmac.new(
            self.HMAC_SECRET,
            expected_data.encode(),
            "sha256"
        ).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid HMAC signature", extra={"callback_data": callback_data})
            raise ConfirmationExpiredError()

        # Check expiry
        if time.time() - timestamp > self.CONFIRMATION_TTL:
            self._pending.pop(callback_data, None)
            raise ConfirmationExpiredError()

        # Verify user matches
        if req_user_id != user_id:
            logger.warning(
                "Confirmation user mismatch",
                extra={"expected": req_user_id, "actual": user_id}
            )
            raise ConfirmationExpiredError()

        # Get and remove pending confirmation
        pending = self._pending.pop(callback_data, None)
        if pending is None:
            raise ConfirmationRequiredError(alias)

        return pending

    def cancel_confirmation(self, alias: str, user_id: int) -> bool:
        """
        Cancel a pending confirmation.

        Args:
            alias: Command alias.
            user_id: User who requested cancellation.

        Returns:
            True if cancelled, False if not found.
        """
        for key, pending in list(self._pending.items()):
            if pending.alias == alias and pending.user_id == user_id:
                self._pending.pop(key)
                return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove expired confirmations.

        Returns:
            Number of removed confirmations.
        """
        now = time.time()
        expired = [
            key for key, pending in self._pending.items()
            if now - pending.created_at > self.CONFIRMATION_TTL
        ]
        for key in expired:
            self._pending.pop(key)
        return len(expired)


async def handle_confirmation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle confirmation button callbacks.

    This should be registered as a CallbackQueryHandler.
    """
    from pitunnel.commands.executor import CommandExecutor
    from pitunnel.commands.registry import CommandRegistry
    from pitunnel.core.i18n import t

    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()

    confirmation_manager: ConfirmationManager = context.bot_data["confirmation_manager"]
    executor: CommandExecutor = context.bot_data["executor"]
    registry: CommandRegistry = context.bot_data["registry"]

    user_id = query.from_user.id
    callback_data = query.data

    if callback_data.startswith("cancel:"):
        alias = callback_data.split(":", 1)[1]
        confirmation_manager.cancel_confirmation(alias, user_id)
        await query.edit_message_text(t("confirmation_expired"))
        return

    try:
        pending = confirmation_manager.verify_confirmation(callback_data, user_id)
    except ConfirmationExpiredError:
        await query.edit_message_text(t("confirmation_expired"))
        return
    except ConfirmationRequiredError:
        await query.edit_message_text(t("confirmation_required", alias=alias))
        return

    # Execute the confirmed command
    alias = pending.alias
    cmd_info = registry.get(alias)
    if cmd_info is None:
        await query.edit_message_text(t("command_not_allowed"))
        return

    result = executor.run_alias(alias, cmd_info.command)

    # Format response
    if result.exit_code == 0:
        text = f"{t('command_executed')} `{alias}`\n\n"
    else:
        text = f"{t('command_failed')} `{alias}` (exit {result.exit_code})\n\n"

    if result.stdout:
        text += f"```\n{result.stdout}\n```"
    if result.stderr:
        text += f"\n```\n{result.stderr}\n```"

    await query.edit_message_text(text, parse_mode="Markdown")