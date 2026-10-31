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
from pitunnel.system.status import get_system_status

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


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if update.message is None:
        return

    try:
        status = get_system_status()
    except Exception as e:
        logger.error("Failed to get system status", exc_info=e)
        await update.message.reply_text(t("unknown_command"))
        return

    # Format uptime
    uptime_seconds = status.uptime_seconds
    days, rem = divmod(uptime_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"

    # Disk usage human readable
    def fmt_disk(percent):
        return f"{percent:.1f}%"

    lines = [t("status_title")]
    lines.append(t("status_cpu", cpu=f"{status.cpu_percent:.1f}"))
    lines.append(t("status_ram", ram=f"{status.ram_percent:.1f}", used="-", total="-"))
    temp_str = f"{status.cpu_temp_c:.1f}" if status.cpu_temp_c is not None else "N/A"
    lines.append(t("status_temp", temp=temp_str))
    lines.append(t("status_disk", disk=f"{status.disk_root_percent:.1f}", used="-", total="-"))
    # NAS disk if available
    if status.disk_nas_percent is not None:
        lines.append(f"Disco /mnt/nas: {status.disk_nas_percent:.1f}%")
    lines.append(t("status_uptime", uptime=uptime_str))
    lines.append(t("status_local_ip", ip=status.local_ip))
    lines.append(t("status_public_ip", ip=status.public_ip))

    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


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
    application.add_handler(CommandHandler("status", status_command, filters=authorized_filter))

    # Confirmation callbacks
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^confirm:"))
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^cancel:"))

    logger.info("Command handlers registered")