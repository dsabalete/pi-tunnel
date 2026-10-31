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
from pitunnel.alerts.engine import AlertEngine

logger = get_logger(__name__)

# Global alert engine instance (initialized once)
_alert_engine: Optional[AlertEngine] = None


def get_alert_engine(history: Optional[Any] = None) -> AlertEngine:
    """Return the global AlertEngine instance, lazily initializing it.

    Args:
        history: Optional History instance for cooldown/alert persistence.
    """
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine(history=history)
    return _alert_engine


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return

    user = update.effective_user
    if user:
        logger.info("User started bot", extra={"user_id": user.id, "username": user.username or "unknown"})

    await update.message.reply_text(t("welcome"))

    # Send startup notification once
    history_logger = context.bot_data.get("history_logger")
    engine = get_alert_engine(history=history_logger)
    if engine.should_send_startup():
        engine.record_startup_notification()
        # Dispatch to all authorized users
        # (In practice the application instance sends this via bot.send_message;
        #  we just mark it here so the engine state is consistent.)
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

    lines = [t("status_title")]
    lines.append(t("status_cpu", cpu=f"{status.cpu_percent:.1f}"))
    lines.append(t("status_ram", ram=f"{status.ram_percent:.1f}", used="-", total="-"))
    temp_str = f"{status.cpu_temp_c:.1f}" if status.cpu_temp_c is not None else "N/A"
    lines.append(t("status_temp", temp=temp_str))
    lines.append(t("status_disk", disk=f"{status.disk_root_percent:.1f}", used="-", total="-"))
    if status.disk_nas_percent is not None:
        lines.append(f"Disco /mnt/nas: {status.disk_nas_percent:.1f}%")
    lines.append(t("status_uptime", uptime=uptime_str))
    lines.append(t("status_local_ip", ip=status.local_ip))
    lines.append(t("status_public_ip", ip=status.public_ip))

    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts command."""
    if update.message is None:
        return

    history_logger = context.bot_data.get("history_logger")
    engine = get_alert_engine(history=history_logger)
    rules = context.bot_data["config"].alerts.rules

    lines: List[str] = [t("alerts_title")]

    for rule in rules:
        rule_id = rule.rule_id
        sensor_id = rule.sensor_id
        when = rule.when
        cooldown_min = rule.cooldown_min

        status_label = "OK"
        if history_logger is not None:
            last_ts = history_logger.get_last_alert_ts(rule_id)
            if last_ts is not None:
                elapsed_seconds = time.time() - last_ts
                cooldown_seconds = cooldown_min * 60
                if elapsed_seconds < cooldown_seconds:
                    status_label = "COOLDOWN"

        lines.append(
            t(
                "alert_rule",
                id=rule_id,
                sensor=sensor_id,
                when=when,
                cooldown=f"{cooldown_min}",
                status=status_label,
            )
        )

    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /on <actuator_id> command."""
    if update.message is None:
        return

    args = context.args
    if not args:
        await update.message.reply_text(t("unknown_command"))
        return

    actuator_id = args[0]
    actuator_registry = context.bot_data.get("actuator_registry")

    if actuator_registry is None:
        await update.message.reply_text("Actuator registry not initialized")
        return

    # Get actuator
    actuator = actuator_registry.get_actuator(actuator_id)
    if actuator is None:
        await update.message.reply_text(t("actuator_not_found", id=actuator_id))
        return

    # Check if confirmation required
    if actuator_registry.should_confirm(actuator_id):
        confirmation_manager: ConfirmationManager = context.bot_data.get("confirmation_manager")
        if confirmation_manager:
            callback_data, keyboard = confirmation_manager.create_confirmation(
                alias=f"on-{actuator_id}",
                user_id=update.effective_user.id if update.effective_user else 0,
                chat_id=update.message.chat_id,
            )
            await update.message.reply_text(
                t("confirm_actuator_action", id=actuator_id, action="on"),
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            return

    # Turn on
    success = actuator.on()
    if success:
        await update.message.reply_text(t("actuator_on", id=actuator_id))
    else:
        await update.message.reply_text(t("actuator_error", id=actuator_id))


async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /off <actuator_id> command."""
    if update.message is None:
        return

    args = context.args
    if not args:
        await update.message.reply_text(t("unknown_command"))
        return

    actuator_id = args[0]
    actuator_registry = context.bot_data.get("actuator_registry")

    if actuator_registry is None:
        await update.message.reply_text("Actuator registry not initialized")
        return

    # Get actuator
    actuator = actuator_registry.get_actuator(actuator_id)
    if actuator is None:
        await update.message.reply_text(t("actuator_not_found", id=actuator_id))
        return

    # Check if confirmation required
    if actuator_registry.should_confirm(actuator_id):
        confirmation_manager: ConfirmationManager = context.bot_data.get("confirmation_manager")
        if confirmation_manager:
            callback_data, keyboard = confirmation_manager.create_confirmation(
                alias=f"off-{actuator_id}",
                user_id=update.effective_user.id if update.effective_user else 0,
                chat_id=update.message.chat_id,
            )
            await update.message.reply_text(
                t("confirm_actuator_action", id=actuator_id, action="off"),
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            return

    # Turn off
    success = actuator.off()
    if success:
        await update.message.reply_text(t("actuator_off", id=actuator_id))
    else:
        await update.message.reply_text(t("actuator_error", id=actuator_id))


def setup_handlers(application: Any, config: Config) -> None:
    """Register all command handlers on the application."""
    authorized_filter = get_authorized_filter(config)

    # Built-in commands
    application.add_handler(CommandHandler("start", start_command, filters=authorized_filter))
    application.add_handler(CommandHandler("help", help_command, filters=authorized_filter))
    application.add_handler(CommandHandler("cmd", cmd_command, filters=authorized_filter))
    application.add_handler(CommandHandler("history", history_command, filters=authorized_filter))
    application.add_handler(CommandHandler("status", status_command, filters=authorized_filter))
    application.add_handler(CommandHandler("alerts", alerts_command, filters=authorized_filter))

    # Actuator commands
    application.add_handler(CommandHandler("on", on_command, filters=authorized_filter))
    application.add_handler(CommandHandler("off", off_command, filters=authorized_filter))

    # Confirmation callbacks
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^confirm:"))
    application.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern="^cancel:"))

    # Schedule alert evaluation every 30 seconds
    application.job_queue.run_repeating(
        _eval_alert_job, interval=30, first=0, drop_pending=True
    )

    logger.info("Command handlers registered")


async def _eval_alert_job(context: Any) -> None:
    """Background job that evaluates alert rules against current sensor readings."""
    history_logger = None
    if hasattr(context, "application") and context.application:
        history_logger = context.application.bot_data.get("history_logger")
    engine = get_alert_engine(history=history_logger)
    logger.info("_eval_alert_job triggered (30s interval)")