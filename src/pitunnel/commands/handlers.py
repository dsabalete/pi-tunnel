"""
Command handlers for PiTunnel.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, List, Optional

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
from pitunnel.ai.manager import AIEventManager
from pitunnel.ai.providers.groq import GroqProvider

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return

    user = update.effective_user
    if user:
        logger.info("User started bot", extra={"user_id": user.id, "username": user.username or "unknown"})

    await update.message.reply_text(t("welcome"))

    logger.info("Startup notification sent to authorized users")


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
    cmd_args = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    result = executor.run_alias(alias, cmd_info.command, user_id=user_id, cmd_args=cmd_args)

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

    # Get limit from args (default 10)
    limit = 10
    if context.args:
        try:
            limit = int(context.args[0])
            if limit < 1 or limit > 100:
                limit = 10
        except ValueError:
            limit = 10

    # Get history from storage
    history_logger = context.bot_data.get("history_logger")
    if history_logger is None:
        await update.message.reply_text(t("history_empty"))
        return

    entries = history_logger.get_history(limit=limit)

    if not entries:
        await update.message.reply_text(t("history_empty"))
        return

    # Format history entries
    lines = [t("history_title", count=len(entries))]
    for entry in entries:
        ts = entry["ts"]
        from datetime import datetime
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        user = entry["user_id"]
        alias = entry["alias"]
        exit_code = entry["exit_code"]
        lines.append(t("history_entry", ts=dt, user=user, alias=alias, exit=exit_code))

    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if update.message is None:
        return

    try:
        disk_root_path = context.bot_data["config"].storage.get("disk_root_path", "/")
        status = get_system_status(disk_root_path=disk_root_path)
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

    lines = [t("status_title")]
    lines.append(t("status_cpu", cpu=f"{status.cpu_percent:.1f}"))
    lines.append(
        t(
            "status_ram",
            ram=f"{status.ram_percent:.1f}",
            used=f"{status.ram_used_mb:.0f}",
            free=f"{status.ram_free_mb:.0f}",
        )
    )
    temp_str = f"{status.cpu_temp_c:.1f}" if status.cpu_temp_c is not None else "N/A"
    lines.append(t("status_temp", temp=temp_str))
    lines.append(t("status_disk", disk=f"{status.disk_root_percent:.1f}", used=f"{status.disk_root_used_gb:.1f}", total=f"{status.disk_root_total_gb:.1f}"))
    if status.disk_nas_percent is not None:
        lines.append(t("status_disk_nas", disk=f"{status.disk_nas_percent:.1f}", used=f"{status.disk_nas_used_gb:.1f}", total=f"{status.disk_nas_total_gb:.1f}"))
    lines.append(t("status_uptime", uptime=uptime_str))
    lines.append(t("status_local_ip", ip=status.local_ip))
    lines.append(t("status_public_ip", ip=status.public_ip))

    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ai <message> command for AI chat."""
    if update.message is None:
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "🤖 Comando de IA\n\n"
            "Uso: /ai <tu pregunta>\n\n"
            "Ejemplo: /ai ¿Qué hora es?"
        )
        return

    user_message = " ".join(args)

    # Get AI config
    ai_config = context.bot_data.get("config").ai
    if not ai_config or not ai_config.enabled:
        await update.message.reply_text("🤖 La funcionalidad de IA no está habilitada.")
        return

    # Create AI event manager
    ai_manager = context.bot_data.get("ai_manager")
    if ai_manager is None:
        if ai_config.provider == "groq" and ai_config.api_key:
            provider = GroqProvider(api_key=ai_config.api_key, model=ai_config.model)
            ai_manager = AIEventManager(provider=provider)
            context.bot_data["ai_manager"] = ai_manager
        else:
            await update.message.reply_text(
                "🤖 AI no configurado.\n\n"
                "Configura la sección 'ai' en config.yaml o añade al .env:"
                r"`AI_API_KEY=your_key`"
            )
            return

    # Generate response
    response = await ai_manager.generate_response(
        system_prompt=ai_config.system_prompt,
        user_message=user_message,
        max_tokens=ai_config.max_tokens,
        temperature=ai_config.temperature,
    )

    if response is None:
        await update.message.reply_text("🤖 Error al generar respuesta. Verifica la configuración de la API.")
        return

    await update.message.reply_text(response.content, parse_mode="Markdown")


def setup_handlers(application: Any, config: Config) -> None:
    """Register all command handlers on the application."""
    authorized_filter = get_authorized_filter(config)

    # Built-in commands
    application.add_handler(CommandHandler("start", start_command, filters=authorized_filter))
    application.add_handler(CommandHandler("help", help_command, filters=authorized_filter))
    application.add_handler(CommandHandler("cmd", cmd_command, filters=authorized_filter))
    application.add_handler(CommandHandler("ai", ai_command, filters=authorized_filter))
    application.add_handler(CommandHandler("history", history_command, filters=authorized_filter))
    application.add_handler(CommandHandler("status", status_command, filters=authorized_filter))

    # Confirmation callbacks
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^confirm:"))
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^cancel:"))

    logger.info("Command handlers registered")


