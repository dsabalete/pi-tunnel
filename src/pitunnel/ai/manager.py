"""AI manager for coordinating providers."""
from __future__ import annotations

from typing import Any

from pitunnel.ai.base import AIProvider, AIResponse


class AIEventManager:
    """Manages AI interactions for group events."""

    def __init__(self, provider: AIProvider | None = None):
        """
        Initialize the AI event manager.

        Args:
            provider: AI provider instance to use.
        """
        self.provider = provider

    def set_provider(self, provider: AIProvider) -> None:
        """Set the AI provider."""
        self.provider = provider

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AIResponse | None:
        """
        Generate an AI response.

        Args:
            system_prompt: System-level instructions.
            user_message: User's message.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            AIResponse or None if no provider available.
        """
        if not self.provider:
            return None
        if not self.provider.check_availability():
            return None

        try:
            return self.provider.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            # Log error but don't raise
            import logging
            logger = logging.getLogger(__name__)
            logger.error("AI generation failed", exc_info=e)
            return None