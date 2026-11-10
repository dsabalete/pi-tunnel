"""Base classes for AI providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIResponse:
    """Response from an AI provider."""
    content: str
    usage: dict[str, Any] | None = None
    provider: str | None = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str, model: str = "default"):
        """
        Initialize the AI provider.

        Args:
            api_key: API key for the provider.
            model: Model name to use.
        """
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        ...

    def build_messages(
        self,
        system_prompt: str,
        user_message: str,
    ) -> list[dict[str, str]]:
        """
        Build the messages list for the API call.

        Args:
            system_prompt: System-level instructions.
            user_message: User's message.

        Returns:
            List of message dictionaries.
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AIResponse:
        """
        Generate a response from the AI.

        Args:
            system_prompt: System-level instructions.
            user_message: User's message.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            AIResponse with the generated content.
        """
        ...

    def check_availability(self) -> bool:
        """
        Check if the provider is available (API key valid, etc.).

        Returns:
            True if the provider can be used.
        """
        return bool(self.api_key)