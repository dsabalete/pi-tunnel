"""Command registry for PiTunnel."""
from __future__ import annotations

from dataclasses import dataclass

from pitunnel.core.config import Config
from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CommandInfo:
    """Information about a registered command."""
    alias: str
    command: str
    destructive: bool
    confirm: bool
    description: str


class CommandRegistry:
    """
    Registry for whitelisted command aliases.

    Loads aliases from config and validates them.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize registry from config.

        Args:
            config: Configuration object.

        Raises:
            ValueError: If duplicate aliases found or invalid config.
        """
        self._commands: dict[str, CommandInfo] = {}
        self._load_from_config(config)

    def _load_from_config(self, config: Config) -> None:
        """Load and validate commands from config."""
        aliases = config.commands.aliases

        # Check for duplicates (case-insensitive)
        seen = set()
        for alias in aliases:
            lower = alias.lower()
            if lower in seen:
                raise ValueError(f"Duplicate command alias (case-insensitive): {alias}")
            seen.add(lower)

        # Build command info (store with lowercase key for case-insensitive lookup)
        for alias, cmd_alias in aliases.items():
            self._commands[alias.lower()] = CommandInfo(
                alias=alias,
                command=cmd_alias.command,
                destructive=cmd_alias.destructive,
                confirm=cmd_alias.confirm,
                description=cmd_alias.description,
            )

        logger.info("Command registry loaded", extra={"count": len(self._commands)})

    def get(self, alias: str) -> CommandInfo | None:
        """
        Get command info by alias (case-insensitive).

        Args:
            alias: Command alias.

        Returns:
            CommandInfo if found, None otherwise.
        """
        return self._commands.get(alias.lower())

    def requires_confirmation(self, alias: str) -> bool:
        """Check if alias requires confirmation."""
        cmd = self.get(alias)
        return cmd.confirm if cmd else False

    def is_destructive(self, alias: str) -> bool:
        """Check if alias is marked as destructive."""
        cmd = self.get(alias)
        return cmd.destructive if cmd else False

    def list_commands(self) -> list[CommandInfo]:
        """Get all registered commands sorted by alias."""
        return sorted(self._commands.values(), key=lambda c: c.alias)

    def get_help_text(self, language: str = "es") -> str:
        """
        Generate help text for built-in commands.

        Only shows commands that have direct handlers implemented.

        Args:
            language: Language code (es/en).

        Returns:
            Formatted help text.
        """
        from pitunnel.core.i18n import t

        lines = [t("help_title")]

        # Built-in commands that have direct handlers
        # (sensors, on, off are hidden - not applicable to this setup)
        built_in_handlers = [
            "cmd",
            "status",
            "alerts",
            "history",
            "start",
            "help",
        ]
        for alias in built_in_handlers:
            lines.append(t(f"help_{alias}"))

        return "\n".join(lines)

    def validate_alias(self, alias: str) -> bool:
        """Check if alias is valid (exists in registry)."""
        return alias.lower() in self._commands