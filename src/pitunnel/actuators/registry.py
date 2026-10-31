"""Actuator registry for managing actuator instances."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ActuatorConfig:
    """Configuration for a single actuator."""

    id: str
    type: str
    enabled: bool = True
    gpio_pin: int = 17
    confirm: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ActuatorRegistry:
    """Manages actuator instances.

    Loads actuators from configuration, creates appropriate driver instances,
    and provides lookup by ID.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize actuator registry.

        Args:
            config: Optional configuration dict with 'actuators' key
        """
        self._config = config or {}
        self._actuators: dict[str, Any] = {}
        self._actuator_configs: dict[str, ActuatorConfig] = {}

    def load_actuators(self) -> list[Any]:
        """Load actuators from configuration.

        Returns:
            List of configured and initialized Actuator instances
        """
        actuators_config = self._config.get("actuators", [])

        if not actuators_config:
            logger.info("No actuators configured")
            return []

        for ac in actuators_config:
            actuator_id = ac.get("id")
            if not actuator_id:
                logger.warning("Actuator config missing 'id' field, skipping")
                continue

            actuator_type = ac.get("type")
            enabled = ac.get("enabled", True)
            gpio_pin = ac.get("gpio_pin", 17)
            confirm = ac.get("confirm", False)
            metadata = ac.get("metadata", {})

            if not enabled:
                logger.info("Actuator %s is disabled, skipping", actuator_id)
                continue

            actuator_config = ActuatorConfig(
                id=actuator_id,
                type=actuator_type,
                enabled=enabled,
                gpio_pin=gpio_pin,
                confirm=confirm,
                metadata=metadata,
            )
            self._actuator_configs[actuator_id] = actuator_config

            actuator = self._create_actuator(actuator_config)
            if actuator:
                self._actuators[actuator_id] = actuator
                logger.info(
                    "Loaded actuator %s (type: %s, pin: %d)",
                    actuator_id,
                    actuator_type,
                    gpio_pin,
                )

        return list(self._actuators.values())

    def _create_actuator(self, config: ActuatorConfig) -> Any | None:
        """Create an actuator instance based on configuration.

        Args:
            config: Actuator configuration

        Returns:
            Actuator instance or None if type not recognized
        """
        actuator_type = config.type

        if not actuator_type:
            logger.warning("Actuator %s has no type, skipping", config.id)
            return None

        try:
            if actuator_type == "relay":
                from pitunnel.actuators.relay import RelayActuator

                return RelayActuator(
                    actuator_id=config.id,
                    gpio_pin=config.gpio_pin,
                    mock_mode=True,  # Use mock mode for safety in tests
                )

            elif actuator_type == "led":
                from pitunnel.actuators.led import LEDActuator

                return LEDActuator(
                    actuator_id=config.id,
                    gpio_pin=config.gpio_pin,
                    mock_mode=True,  # Use mock mode for safety in tests
                )

            else:
                logger.warning(
                    "Unknown actuator type: %s for actuator %s",
                    actuator_type,
                    config.id,
                )
                return None

        except ImportError as e:
            logger.warning(
                "Failed to import driver for actuator %s (type: %s): %s",
                config.id,
                actuator_type,
                e,
            )
            return None

    def get_actuator(self, actuator_id: str) -> Any | None:
        """Get an actuator by ID.

        Args:
            actuator_id: Unique actuator identifier

        Returns:
            Actuator instance or None if not found
        """
        return self._actuators.get(actuator_id)

    def get_all_actuators(self) -> list[Any]:
        """Get all configured actuators.

        Returns:
            List of all Actuator instances
        """
        return list(self._actuators.values())

    def get_config(self, actuator_id: str) -> ActuatorConfig | None:
        """Get actuator configuration.

        Args:
            actuator_id: Unique actuator identifier

        Returns:
            ActuatorConfig or None if not found
        """
        return self._actuator_configs.get(actuator_id)

    def should_confirm(self, actuator_id: str) -> bool:
        """Check if an actuator requires confirmation.

        Args:
            actuator_id: Unique actuator identifier

        Returns:
            True if confirmation is required
        """
        config = self._actuator_configs.get(actuator_id)
        return config.confirm if config else False