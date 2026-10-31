"""CPU temperature sensor driver using psutil."""

from __future__ import annotations

from typing import Optional

from pitunnel.sensors.base import Sensor, SensorReading


class CPUTempSensor(Sensor):
    """CPU temperature sensor using psutil.

    Falls back to /sys/class/thermal/thermal_zone0/temp on Linux systems.
    """

    def __init__(self, sensor_id: str = "cpu-temp"):
        """Initialize CPU temperature sensor.

        Args:
            sensor_id: Unique identifier for this sensor (default: 'cpu-temp')
        """
        self._id = sensor_id
        self._type = "cpu_temp"

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

    def read(self) -> Optional[SensorReading]:
        """Read CPU temperature.

        Returns:
            SensorReading with temperature in °C, or None on error
        """
        # Try psutil first
        try:
            import psutil

            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return SensorReading(value=entries[0].current, unit=self.unit)
        except Exception:
            pass

        # Fallback to reading from sysfs (Linux only)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_celsius = int(f.read().strip()) / 1000.0
                return SensorReading(value=temp_celsius, unit=self.unit)
        except Exception:
            pass

        return None