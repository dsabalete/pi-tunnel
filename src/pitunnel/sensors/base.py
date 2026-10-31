"""Sensor base protocol and types for PiTunnel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SensorReading:
    """Represents a single sensor reading.

    Attributes:
        value: The numeric reading value
        unit: Unit of measurement (e.g., "°C", "%")
        timestamp: Unix timestamp of the reading (defaults to time.time())
    """

    value: float
    unit: str
    timestamp: float = 0.0  # Will be set by caller if 0

    def __post_init__(self) -> None:
        """Set timestamp to now if not provided."""
        if self.timestamp == 0.0:
            import time

            self.timestamp = time.time()


class Sensor(ABC):
    """Abstract base class for all sensor types.

    All sensor drivers must inherit from this class and implement
    the read() method.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this sensor."""
        ...

    @property
    @abstractmethod
    def sensor_type(self) -> str:
        """Type of sensor (e.g., 'dht22', 'ds18b20', 'bme280')."""
        ...

    @property
    @abstractmethod
    def unit(self) -> str:
        """Unit of measurement for this sensor."""
        ...

    @abstractmethod
    def read(self) -> Optional[SensorReading]:
        """Read the current sensor value.

        Returns:
            SensorReading if successful, None if read fails
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r})"