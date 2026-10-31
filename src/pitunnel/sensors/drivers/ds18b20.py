"""DS18B20 1-Wire temperature sensor driver."""

from __future__ import annotations

from typing import Optional

from pitunnel.sensors.base import Sensor, SensorReading


class DS18B20Sensor(Sensor):
    """DS18B20 1-Wire temperature sensor driver.

    The DS18B20 is a digital temperature sensor that uses the 1-Wire protocol.
    It is typically accessible via the Linux w1thermsensor kernel module.
    """

    def __init__(self, sensor_id: str, device_id: Optional[str] = None):
        """Initialize DS18B20 sensor.

        Args:
            sensor_id: Unique identifier for this sensor in the bot
            device_id: Optional ROM code of the specific DS18B20 device.
                      If None, uses the first available sensor on the bus.
        """
        self._id = sensor_id
        self._device_id = device_id
        self._type = "ds18b20"

    @property
    def id(self) -> str:
        return self._id

    @property
    def sensor_type(self) -> str:
        return self._type

    @property
    def unit(self) -> str:
        """Returns '°C' for temperature readings."""
        return "°C"

    def _get_device_path(self) -> Optional[str]:
        """Get the sysfs path for this sensor device.

        Returns:
            Path to the device's w1_slave file, or None if not found
        """
        try:
            if self._device_id:
                device_path = f"/sys/bus/w1/devices/{self._device_id}/w1_slave"
            else:
                # Find first device on the bus
                import os

                devices_dir = "/sys/bus/w1/devices/"
                if not os.path.exists(devices_dir):
                    return None

                for entry in os.listdir(devices_dir):
                    if entry.startswith("28-"):  # DS18B20 family code
                        device_path = f"{devices_dir}{entry}/w1_slave"
                        if os.path.exists(device_path):
                            return device_path

            return device_path

        except Exception:
            return None

    def read(self) -> Optional[SensorReading]:
        """Read temperature from DS18B20 sensor.

        Returns:
            SensorReading with temperature in °C, or None on error
        """
        device_path = self._get_device_path()
        if device_path is None:
            return None

        try:
            with open(device_path, "r") as f:
                content = f.read()

            # Parse the w1_slave output
            # Format:
            # 72 01 8a 7a 7f 7f 11 00 7f: crc=7f YES
            # 72 01 8a 7a 7f 7f 11 00 7f t=23125
            lines = content.strip().split("\n")
            if len(lines) < 2:
                return None

            # Check CRC
            if "YES" not in lines[0]:
                return None

            # Parse temperature from second line
            temp_str = lines[1].split("t=")[-1].strip()
            temp_celsius = float(temp_str) / 1000.0

            return SensorReading(value=temp_celsius, unit=self.unit)

        except Exception:
            return None