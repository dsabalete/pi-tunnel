"""
PiTunnel Bot core class.
"""
from __future__ import annotations

import signal
import sys
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
)

from pitunnel.commands.confirm import ConfirmationManager
from pitunnel.commands.executor import CommandExecutor
from pitunnel.commands.handlers import setup_handlers
from pitunnel.commands.registry import CommandRegistry
from pitunnel.core.config import Config, load_env
from pitunnel.core.errors import error_handler
from pitunnel.core.i18n import set_language
from pitunnel.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


class PiTunnelBot:
    """
    Main bot class extending PTB Application.

    Handles initialization, signal handling, and graceful shutdown.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize the bot.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.token = self._get_token()

        # Set up logging
        setup_logging(json_format=True)

        # Set language
        set_language(config.telegram.language)

        # Build application
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )

        # Store config in bot_data for access in handlers
        self.application.bot_data["config"] = config

        # Initialize components
        self.registry = CommandRegistry(config)
        self.executor = CommandExecutor(config)
        self.confirmation_manager = ConfirmationManager()

        # Store in bot_data for handlers
        self.application.bot_data["registry"] = self.registry
        self.application.bot_data["executor"] = self.executor
        self.application.bot_data["confirmation_manager"] = self.confirmation_manager

        # Set up error handler
        self.application.add_error_handler(error_handler)

        # Set up command handlers
        setup_handlers(self.application, config)

        # Register signal handlers
        self._setup_signals()

    def _get_token(self) -> str:
        """Get bot token from environment."""
        import os
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token or token == "your_bot_token_here":
            logger.error("TELEGRAM_BOT_TOKEN not set in environment")
            sys.exit(1)
        return token

    def _setup_signals(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame: Any) -> None:
            logger.info("Shutdown signal received", extra={"signal": signum})
            self.application.stop_running()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def initialize(self) -> None:
        """Initialize the application."""
        await self.application.initialize()
        logger.info("PiTunnel bot initialized")

    async def start(self) -> None:
        """Start the bot (long polling)."""
        await self.application.start()
        logger.info("PiTunnel bot started")

        # Send startup alert
        await self._send_startup_alert()

    async def _send_startup_alert(self) -> None:
        """Send startup notification to authorized users."""
        from pitunnel.core.i18n import t

        for user_id in self.config.telegram.authorized_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=t("startup_alert"),
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to send startup alert",
                    extra={"user_id": user_id, "error": str(e)}
                )

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        logger.info("Stopping PiTunnel bot...")

        # Send shutdown alert
        from pitunnel.core.i18n import t
        for user_id in self.config.telegram.authorized_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=t("shutdown_alert"),
                )
            except Exception:  # noqa: BLE001
                logger.debug("Failed to send shutdown alert", extra={"user_id": user_id})

        await self.application.stop()
        await self.application.shutdown()
        logger.info("PiTunnel bot stopped")

    def run(self) -> None:
        """Run the bot (blocking)."""
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )


def create_bot(config: Config | None = None) -> PiTunnelBot:
    """
    Factory function to create PiTunnelBot.

    Args:
        config: Optional Config object. If None, loads from default locations.

    Returns:
        Initialized PiTunnelBot instance.
    """
    if config is None:
        load_env()
        config = Config.load()

    return PiTunnelBot(config)