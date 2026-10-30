"""
Command handlers for PiTunnel.
"""
from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from pitunnel.commands.confirm import ConfirmationManager, handle_confirmation_callback
from pitunnel.commands.executor import CommandExecutor
from pitunnel.commands.registry import CommandRegistry
from pitunnel.core.auth import get_authorized_filter
from pitunnel.core.config import Config
from pitunnel.core.i18n import t
from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return

    user = update.effective_user
    if user:
        logger.info("User started bot", extra={"user_id": user.id, "username": user.username or "unknown"})

    await update.message.reply_text(t("welcome"))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if update.message is None:
        return

    registry: CommandRegistry = context.bot_data["registry"]
    help_text = registry.get_help_text(context.bot_data["config"].telegram.language)

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cmd <alias> command."""
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    args = context.args

    if not args:
        await update.message.reply_text(t("unknown_command"))
        return

    alias = args[0].lower()
    registry: CommandRegistry = context.bot_data["registry"]
    executor: CommandExecutor = context.bot_data["executor"]
    confirmation_manager: ConfirmationManager = context.bot_data["confirmation_manager"]

    cmd_info = registry.get(alias)
    if cmd_info is None:
        await update.message.reply_text(t("command_not_allowed"))
        return

    # Check if confirmation required
    if cmd_info.confirm or cmd_info.destructive:
        callback_data, keyboard = confirmation_manager.create_confirmation(
            alias=alias,
            user_id=user_id,
            chat_id=update.message.chat_id,
        )

        sent = await update.message.reply_text(
            f"⚠️ *Confirmar acción destructiva*\n\n"
            f"¿Ejecutar `{alias}`?\n"
            f"`{cmd_info.command}`",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

        # Store message_id for potential cleanup
        if callback_data in confirmation_manager._pending:
            confirmation_manager._pending[callback_data].message_id = sent.message_id

        return

    # Execute directly
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

    await update.message.reply_text(text, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history [n] command."""
    if update.message is None:
        return

    # TODO: Implement when storage is ready (T703)
    _ = context.args  # limit = int(args[0]) if args else 10

    await update.message.reply_text(t("history_empty"))


def setup_handlers(application: Any, config: Config) -> None:
    """
    Register all command handlers on the application.

    Args:
        application: PTB Application instance.
        config: Configuration object.
    """
    authorized_filter = get_authorized_filter(config)

    # Built-in commands
    application.add_handler(CommandHandler("start", start_command, filters=authorized_filter))
    application.add_handler(CommandHandler("help", help_command, filters=authorized_filter))
    application.add_handler(CommandHandler("cmd", cmd_command, filters=authorized_filter))
    application.add_handler(CommandHandler("history", history_command, filters=authorized_filter))

    # Confirmation callbacks
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^confirm:"))
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^cancel:"))

    logger.info("Command handlers registered")