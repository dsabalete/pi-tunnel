"""Actuator base protocol for PiTunnel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ActuatorReading:
    """Status reading from an actuator."""

    is_on: bool
    timestamp: float

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            import time

            self.timestamp = time.time()


class Actuator(ABC):
    """Abstract base class for all actuator types.

    Provides uniform interface for GPIO-controlled devices.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this actuator."""
        ...

    @property
    @abstractmethod
    def actuator_type(self) -> str:
        """Type of actuator (e.g., 'relay', 'led')."""
        ...

    @abstractmethod
    def on(self) -> bool:
        """Turn the actuator on.

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def off(self) -> bool:
        """Turn the actuator off.

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def state(self) -> bool:
        """Get current state of the actuator.

        Returns:
            True if on, False if off
        """
        ...

    def toggle(self) -> bool:
        """Toggle the actuator state.

        Returns:
            True if successful, False otherwise
        """
        if self.state():
            return self.off()
        return self.on()

    def __repr__(self) -> str:
        state = "on" if self.state() else "off"
        return f"{self.__class__.__name__}(id={self.id!r}, {state})"