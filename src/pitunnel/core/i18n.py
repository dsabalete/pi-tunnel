"""Internationalization (i18n) for PiTunnel."""
from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Self

import yaml


class I18n:
    """String loader for translations."""

    _instance: ClassVar[I18n | None] = None
    _strings: ClassVar[dict[str, dict[str, str]]] = {}
    _current_lang: ClassVar[str] = "es"

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[return-value]

    def __init__(self) -> None:
        if not self._strings:
            self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files."""
        # Search for locale directory
        locale_paths = [
            Path("/etc/pitunnel/locales"),
            Path(__file__).parent.parent.parent.parent / "locales",
            Path.cwd() / "locales",
        ]

        strings: dict[str, dict[str, str]] = {}
        for locale_path in locale_paths:
            if locale_path.exists():
                for lang_file in locale_path.glob("*.yaml"):
                    lang = lang_file.stem
                    with lang_file.open("r", encoding="utf-8") as f:
                        strings[lang] = yaml.safe_load(f) or {}
                break

        # Fallback to built-in translations if no files found
        if not strings:
            strings = self._builtin_translations()

        I18n._strings = strings

    @staticmethod
    def _builtin_translations() -> dict[str, dict[str, str]]:
        """Built-in translations as fallback."""
        return {
            "es": {
                "welcome": "¡Bienvenido a PiTunnel! 🤖\nUsa /help para ver los comandos disponibles.",
                "help_title": "📋 *Comandos disponibles:*",
                "help_cmd": "/cmd <alias> - Ejecuta un comando de la lista blanca",
                "help_status": "/status - Estado del sistema (CPU, RAM, temp, disco, red)",
                "help_history": "/history [n] - Historial de comandos (def. 10)",
                "help_start": "/start - Registra tu chat y muestra bienvenida",
                "help_help": "/help - Esta ayuda",
                "help_ai": "/ai <pregunta> - Chatea con IA",
                "help_restart_mqtt": "/restart-mqtt - Reiniciar mosquitto",
                "unauthorized": "⛔ No estás autorizado para usar este bot.",
                "unknown_command": "❓ Comando no reconocido. Usa /help.",
                "command_not_allowed": "🚫 Comando fuera de la lista permitida.",
                "confirmation_required": "⚠️ Esta acción requiere confirmación.",
                "confirmation_expired": "⏱ La confirmación ha expirado. Intenta de nuevo.",
                "command_executed": "✅ Comando ejecutado:",
                "command_failed": "❌ Error ejecutando comando:",
                "status_title": "📊 *Estado del sistema*",
                "status_cpu": "CPU: {cpu}%",
                "status_ram": "RAM: {ram}% ({used}/{free} MB)",
                "status_temp": "Temp CPU: {temp}°C",
                "status_disk": "Disco /: {disk}% ({used}/{total} GB)",
                "status_disk_nas": "Disco /mnt/nas: {disk}% ({used}/{total} GB)",
                "status_uptime": "Uptime: {uptime}",
                "status_local_ip": "IP local: {ip}",
                "status_public_ip": "IP pública: {ip}",
                "history_title": "📜 *Historial de comandos (últimos {count}):*",
                "history_entry": "`{ts}` @{user} → {alias} (exit: {exit})",
                "history_empty": "Historial vacío.",
                "startup_alert": "🟢 PiTunnel en línea",
                "shutdown_alert": "🔴 PiTunnel apagado",
            },
            "en": {
                "welcome": "Welcome to PiTunnel! 🤖\nUse /help to see available commands.",
                "help_title": "📋 *Available commands:*",
                "help_cmd": "/cmd <alias> - Execute a whitelisted command",
                "help_status": "/status - System status (CPU, RAM, temp, disk, network)",
                "help_history": "/history [n] - Command history (default 10)",
                "help_start": "/start - Register your chat and show welcome",
                "help_help": "/help - This help",
                "help_ai": "/ai <message> - Chat with AI",
                "help_restart_mqtt": "/restart-mqtt - Restart mosquitto",
                "unauthorized": "⛔ You are not authorized to use this bot.",
                "unknown_command": "❓ Unknown command. Use /help.",
                "command_not_allowed": "🚫 Command not in whitelist.",
                "confirmation_required": "⚠️ This action requires confirmation.",
                "confirmation_expired": "⏱ Confirmation expired. Try again.",
                "command_executed": "✅ Command executed:",
                "command_failed": "❌ Command failed:",
                "status_title": "📊 *System Status*",
                "status_cpu": "CPU: {cpu}%",
                "status_ram": "RAM: {ram}% ({used}/{free} MB)",
                "status_temp": "CPU Temp: {temp}°C",
                "status_disk": "Disk /: {disk}% ({used}/{total} GB)",
                "status_disk_nas": "Disk /mnt/nas: {disk}% ({used}/{total} GB)",
                "status_uptime": "Uptime: {uptime}",
                "status_local_ip": "Local IP: {ip}",
                "status_public_ip": "Public IP: {ip}",
                "history_title": "📜 *Command history (last {count}):*",
                "history_entry": "`{ts}` @{user} → {alias} (exit: {exit})",
                "history_empty": "History is empty.",
                "startup_alert": "🟢 PiTunnel online",
                "shutdown_alert": "🔴 PiTunnel offline",
            },
        }

    def set_language(self, lang: str) -> None:
        """Set current language."""
        if lang in I18n._strings:
            I18n._current_lang = lang
        else:
            # Fallback to Spanish if language not found
            I18n._current_lang = "es"

    def t(self, key: str, **kwargs: Any) -> str:
        """
        Get translated string.

        Args:
            key: Translation key.
            **kwargs: Format arguments.

        Returns:
            Translated and formatted string.
        """
        strings = I18n._strings.get(I18n._current_lang, I18n._strings.get("es", {}))
        template = strings.get(key, key)

        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @property
    def current_language(self) -> str:
        """Get current language code."""
        return I18n._current_lang


# Global instance
i18n = I18n()


def t(key: str, **kwargs: Any) -> str:
    """Convenience function for translation."""
    return i18n.t(key, **kwargs)


def set_language(lang: str) -> None:
    """Set global language."""
    i18n.set_language(lang)