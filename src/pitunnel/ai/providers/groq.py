"""Groq AI provider implementation."""
from __future__ import annotations

import httpx
from typing import Any

from pitunnel.ai.base import AIProvider, AIResponse


class GroqProvider(AIProvider):
    """Groq AI provider."""

    name = "groq"

    @property
    def default_model(self) -> str:
        """Return the default Groq model."""
        return "llama-3.3-70b-versatile"

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AIResponse:
        """
        Generate a response from Groq.

        Args:
            system_prompt: System-level instructions.
            user_message: User's message.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            AIResponse with the generated content.
        """
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        url = "https://api.groq.com/v1/chat/completions"
        messages = self.build_messages(system_prompt, user_message)

        payload = {
            "model": self.model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return AIResponse(
            content=content.strip(),
            usage=usage,
            provider=self.name,
        )

    def check_availability(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)