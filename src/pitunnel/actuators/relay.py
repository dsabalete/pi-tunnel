"""Relay actuator using gpiozero OutputDevice."""

from __future__ import annotations

from typing import Optional

from pitunnel.core.logging import get_logger

from .base import Actuator

logger = get_logger(__name__)


class RelayActuator(Actuator):
    """Relay actuator controlling a GPIO pin via gpiozero OutputDevice.

    The relay is typically used to control high-voltage devices (lights,
    appliances) from the low-voltage GPIO.
    """

    def __init__(
        self,
        actuator_id: str,
        gpio_pin: int = 17,
        active_high: bool = True,
        mock_mode: bool = False,
    ):
        """Initialize relay actuator.

        Args:
            actuator_id: Unique identifier for this relay
            gpio_pin: GPIO pin number (BCM numbering)
            active_high: If True, HIGH turns relay on
            mock_mode: If True, skip actual GPIO operations (for testing)
        """
        self._id = actuator_id
        self._gpio_pin = gpio_pin
        self._active_high = active_high
        self._mock_mode = mock_mode
        self._type = "relay"
        self._device: Optional[object] = None
        self._state = False  # Track state in mock mode

    @property
    def id(self) -> str:
        return self._id

    @property
    def actuator_type(self) -> str:
        return self._type

    @property
    def gpio_pin(self) -> int:
        return self._gpio_pin

    def _get_device(self):
        """Get or create the gpiozero OutputDevice."""
        if self._mock_mode:
            return None

        if self._device is None:
            try:
                from gpiozero import OutputDevice

                self._device = OutputDevice(self._gpio_pin, active_high=self._active_high)
            except Exception as e:
                logger.warning("Failed to create GPIO device for %s: %s", self._id, e)
                return None
        return self._device

    def on(self) -> bool:
        """Turn relay on.

        Returns:
            True if successful
        """
        if self._mock_mode:
            self._state = True
            return True

        device = self._get_device()
        if device is None:
            return False

        try:
            device.on()
            self._state = True
            return True
        except Exception as e:
            logger.warning("Failed to turn on relay %s: %s", self._id, e)
            return False

    def off(self) -> bool:
        """Turn relay off.

        Returns:
            True if successful
        """
        if self._mock_mode:
            self._state = False
            return True

        device = self._get_device()
        if device is None:
            return False

        try:
            device.off()
            self._state = False
            return True
        except Exception as e:
            logger.warning("Failed to turn off relay %s: %s", self._id, e)
            return False

    def state(self) -> bool:
        """Get current relay state.

        Returns:
            True if relay is on, False if off
        """
        if self._mock_mode:
            return self._state

        device = self._get_device()
        if device is None:
            return False

        try:
            state = device.is_active
            self._state = state  # Sync our tracking
            return state
        except Exception:
            return False

    def close(self) -> None:
        """Close the GPIO device."""
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None