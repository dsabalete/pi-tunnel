"""Sensor registry for managing sensor instances."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pitunnel.core.logging import get_logger
from pitunnel.sensors.base import Sensor, SensorReading

logger = get_logger(__name__)

# Type for sensor type mapping
SensorType = TypeVar("SensorType", bound=Sensor)


@dataclass
class SensorConfig:
    """Configuration for a single sensor."""

    id: str
    type: str
    enabled: bool = True
    interval_seconds: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)


class SensorRegistry:
    """Manages sensor instances and polling.

    Loads sensors from configuration, creates appropriate driver instances,
    and schedules periodic polling via APScheduler.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize sensor registry.

        Args:
            config: Optional configuration dict with 'sensors' key
        """
        self._config = config or {}
        self._sensors: dict[str, Sensor] = {}
        self._sensor_configs: dict[str, SensorConfig] = {}
        self._readings: dict[str, SensorReading] = {}

    def load_sensors(self) -> list[Sensor]:
        """Load sensors from configuration.

        Returns:
            List of configured and initialized Sensor instances
        """
        sensors_config = self._config.get("sensors", [])

        if not sensors_config:
            logger.info("No sensors configured")
            return []

        for sc in sensors_config:
            sensor_id = sc.get("id")
            if not sensor_id:
                logger.warning("Sensor config missing 'id' field, skipping")
                continue

            sensor_type = sc.get("type")
            enabled = sc.get("enabled", True)
            interval = sc.get("interval_seconds", 30)
            metadata = sc.get("metadata", {})

            if not enabled:
                logger.info("Sensor %s is disabled, skipping", sensor_id)
                continue

            sensor_config = SensorConfig(
                id=sensor_id,
                type=sensor_type,
                enabled=enabled,
                interval_seconds=interval,
                metadata=metadata,
            )
            self._sensor_configs[sensor_id] = sensor_config

            sensor = self._create_sensor(sensor_config)
            if sensor:
                self._sensors[sensor_id] = sensor
                logger.info(
                    "Loaded sensor %s (type: %s, interval: %ds)",
                    sensor_id,
                    sensor_type,
                    interval,
                )

        return list(self._sensors.values())

    def _create_sensor(self, config: SensorConfig) -> Sensor | None:
        """Create a sensor instance based on configuration.

        Args:
            config: Sensor configuration

        Returns:
            Sensor instance or None if type not recognized
        """
        sensor_type = config.type

        if not sensor_type:
            logger.warning("Sensor %s has no type, skipping", config.id)
            return None

        # Import driver based on type
        try:
            if sensor_type == "dht22":
                from pitunnel.sensors.drivers.dht22 import DHT22Sensor

                return DHT22Sensor(
                    sensor_id=config.id,
                    gpio_pin=config.metadata.get("gpio_pin", 4),
                )

            elif sensor_type == "ds18b20":
                from pitunnel.sensors.drivers.ds18b20 import DS18B20Sensor

                return DS18B20Sensor(
                    sensor_id=config.id,
                    device_id=config.metadata.get("device_id"),
                )

            elif sensor_type == "bme280":
                from pitunnel.sensors.drivers.bme280 import BME280Sensor

                return BME280Sensor(
                    sensor_id=config.id,
                    address=config.metadata.get("i2c_address", 0x76),
                )

            elif sensor_type == "cpu_temp":
                from pitunnel.sensors.drivers.cpu_temp import CPUTempSensor

                return CPUTempSensor(sensor_id=config.id)

            else:
                logger.warning("Unknown sensor type: %s for sensor %s", sensor_type, config.id)
                return None

        except ImportError as e:
            logger.warning(
                "Failed to import driver for sensor %s (type: %s): %s",
                config.id,
                sensor_type,
                e,
            )
            return None

    def start_polling(self, scheduler, history_logger=None):
        """Start periodic polling of all sensors.

        Args:
            scheduler: APScheduler scheduler instance
            history_logger: Optional History instance for storing readings
        """
        for sensor_id, sensor in self._sensors.items():
            config = self._sensor_configs.get(sensor_id)
            if not config:
                continue

            def poll_job(sid: str, sn: Sensor):
                """Job function to poll a single sensor."""
                try:
                    reading = sn.read()
                    if reading:
                        self._readings[sid] = reading
                        if history_logger:
                            history_logger.log_sensor_reading(
                                sensor_id=sid,
                                value=reading.value,
                                unit=reading.unit,
                            )
                        logger.debug("Sensor %s: %s %s", sid, reading.value, reading.unit)
                except Exception as e:
                    logger.warning("Error polling sensor %s: %s", sid, e)

            scheduler.add_job(
                poll_job,
                "interval",
                seconds=config.interval_seconds,
                args=(sensor_id, sensor),
                id=f"sensors_poll_{sensor_id}",
                replace_existing=True,
            )

            logger.info("Started polling sensor %s every %ds", sensor_id, config.interval_seconds)

    def get_sensor(self, sensor_id: str) -> Sensor | None:
        """Get a sensor by ID.

        Args:
            sensor_id: Unique sensor identifier

        Returns:
            Sensor instance or None if not found
        """
        return self._sensors.get(sensor_id)

    def get_all_sensors(self) -> list[Sensor]:
        """Get all configured sensors.

        Returns:
            List of all Sensor instances
        """
        return list(self._sensors.values())

    def get_reading(self, sensor_id: str) -> SensorReading | None:
        """Get the most recent reading for a sensor.

        Args:
            sensor_id: Unique sensor identifier

        Returns:
            SensorReading or None if not available
        """
        return self._readings.get(sensor_id)

    def get_all_readings(self) -> dict[str, SensorReading]:
        """Get all recent sensor readings.

        Returns:
            Dict mapping sensor_id to SensorReading
        """
        return dict(self._readings)

    def poll_all(self, history_logger=None) -> dict[str, SensorReading]:
        """Poll all sensors once and store readings.

        Args:
            history_logger: Optional History instance

        Returns:
            Dict mapping sensor_id to SensorReading
        """
        for sensor_id, sensor in self._sensors.items():
            reading = sensor.read()
            if reading:
                self._readings[sensor_id] = reading
                if history_logger:
                    history_logger.log_sensor_reading(
                        sensor_id=sensor_id,
                        value=reading.value,
                        unit=reading.unit,
                    )

        return self.get_all_readings()