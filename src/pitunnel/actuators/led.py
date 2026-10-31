"""LED actuator with optional PWM support."""

from __future__ import annotations

from typing import Optional

from pitunnel.core.logging import get_logger

from .base import Actuator

logger = get_logger(__name__)


class LEDActuator(Actuator):
    """LED actuator with optional PWM brightness control.

    Uses gpiozero LED which supports PWM for brightness control.
    """

    def __init__(
        self,
        actuator_id: str,
        gpio_pin: int = 18,
        mock_mode: bool = False,
    ):
        """Initialize LED actuator.

        Args:
            actuator_id: Unique identifier for this LED
            gpio_pin: GPIO pin number (BCM numbering)
            mock_mode: If True, skip actual GPIO operations (for testing)
        """
        self._id = actuator_id
        self._gpio_pin = gpio_pin
        self._mock_mode = mock_mode
        self._type = "led"
        self._device: Optional[object] = None
        self._brightness = 0.0  # 0.0 to 1.0
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

    @property
    def brightness(self) -> float:
        """Get current brightness level (0.0 to 1.0)."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set brightness level (0.0 to 1.0)."""
        self._brightness = max(0.0, min(1.0, value))
        if not self._mock_mode:
            self._apply_brightness()

    def _get_device(self):
        """Get or create the gpiozero LED device."""
        if self._mock_mode:
            return None

        if self._device is None:
            try:
                from gpiozero import LED

                self._device = LED(self._gpio_pin)
            except Exception as e:
                logger.warning("Failed to create LED device for %s: %s", self._id, e)
                return None
        return self._device

    def _apply_brightness(self) -> None:
        """Apply current brightness to LED device."""
        if self._device is None:
            return

        try:
            self._device.value = self._brightness
        except Exception as e:
            logger.warning("Failed to set LED brightness for %s: %s", self._id, e)

    def on(self) -> bool:
        """Turn LED on at full brightness.

        Returns:
            True if successful
        """
        if self._mock_mode:
            self._brightness = 1.0
            self._state = True
            return True

        device = self._get_device()
        if device is None:
            return False

        try:
            device.on()
            self._brightness = 1.0
            self._state = True
            return True
        except Exception as e:
            logger.warning("Failed to turn on LED %s: %s", self._id, e)
            return False

    def off(self) -> bool:
        """Turn LED off (brightness 0).

        Returns:
            True if successful
        """
        if self._mock_mode:
            self._brightness = 0.0
            self._state = False
            return True

        device = self._get_device()
        if device is None:
            return False

        try:
            device.off()
            self._brightness = 0.0
            self._state = False
            return True
        except Exception as e:
            logger.warning("Failed to turn off LED %s: %s", self._id, e)
            return False

    def state(self) -> bool:
        """Get current LED state.

        Returns:
            True if LED is on, False if off
        """
        return self._brightness > 0.0

    def close(self) -> None:
        """Close the LED device."""
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None