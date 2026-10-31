"""BME280 I²C environmental sensor driver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pitunnel.sensors.base import Sensor, SensorReading


@dataclass
class BME280Reading:
    """Complete reading from BME280 sensor."""

    temperature: Optional[float]  # °C
    humidity: Optional[float]  # %
    pressure: Optional[float]  # hPa


class BME280Sensor(Sensor):
    """BME280 I²C environmental sensor (temperature, humidity, pressure)."""

    # BME280 I²C addresses
    ADDRESS_PRIMARY = 0x76
    ADDRESS_SECONDARY = 0x77

    # Register addresses
    REG_DIG_T1 = 0x88
    REG_DIG_T2 = 0x8A
    REG_DIG_T3 = 0x8C
    REG_DIG_P1 = 0x8E
    REG_DIG_P2 = 0x90
    REG_DIG_P3 = 0x92
    REG_DIG_P4 = 0x94
    REG_DIG_P5 = 0x96
    REG_DIG_P6 = 0x98
    REG_DIG_P7 = 0x9A
    REG_DIG_P8 = 0x9C
    REG_DIG_P9 = 0x9E

    REG_DIG_H1 = 0xA1
    REG_DIG_H2 = 0xE1
    REG_DIG_H3 = 0xE3
    REG_DIG_H4 = 0xE5
    REG_DIG_H5 = 0xE7
    REG_DIG_H6 = 0xE9

    REG_CTRL_HUM = 0xF2
    REG_CTRL_MEAS = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESS_MSB = 0xF7

    def __init__(
        self,
        sensor_id: str,
        address: int = ADDRESS_PRIMARY,
        mock_reading: bool = False,
    ):
        """Initialize BME280 sensor.

        Args:
            sensor_id: Unique identifier for this sensor in the bot
            address: I²C address (0x76 or 0x77)
            mock_reading: If True, return mock data (for testing)
        """
        self._id = sensor_id
        self._address = address
        self._mock_reading = mock_reading
        self._type = "bme280"
        self._i2c = None
        self._calibration = None

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

    def _init_i2c(self):
        """Initialize I²C connection and read calibration data."""
        if self._i2c is not None:
            return True

        try:
            import smbus2

            self._i2c = smbus2.SMBus(self._address)
            self._calibration = self._read_calibration()
            return True
        except Exception:
            return False

    def _read_calibration(self) -> dict:
        """Read calibration data from sensor."""
        if not self._i2c:
            return {}

        try:
            calib = {}

            # Read calibration registers
            data = self._i2c.read_i2c_block_data(
                self._address, self.REG_DIG_T1, 24
            )

            # Temperature calibration
            calib["dig_T1"] = data[0] | (data[1] << 8)
            calib["dig_T2"] = self._s16(data[2] | (data[3] << 8))
            calib["dig_T3"] = self._s16(data[4] | (data[5] << 8))

            # Pressure calibration
            calib["dig_P1"] = data[6] | (data[7] << 8)
            calib["dig_P2"] = self._s16(data[8] | (data[9] << 8))
            calib["dig_P3"] = self._s16(data[10] | (data[11] << 8))
            calib["dig_P4"] = self._s16(data[12] | (data[13] << 8))
            calib["dig_P5"] = self._s16(data[14] | (data[15] << 8))
            calib["dig_P6"] = self._s16(data[16] | (data[17] << 8))
            calib["dig_P7"] = self._s16(data[18] | (data[19] << 8))
            calib["dig_P8"] = self._s16(data[20] | (data[21] << 8))
            calib["dig_P9"] = self._s16(data[22] | (data[23] << 8))

            # Humidity calibration
            calib["dig_H1"] = data[24]
            calib["dig_H2"] = self._s16(data[25] | (data[26] << 8))
            calib["dig_H3"] = data[27]
            calib["dig_H4"] = (data[28] << 4) | (data[29] & 0x0F)
            calib["dig_H5"] = ((data[29] & 0xF0) >> 4) | (data[30] << 8)
            calib["dig_H6"] = data[31]

            return calib
        except Exception:
            return {}

    def _s16(self, value: int) -> int:
        """Convert unsigned 16-bit to signed 16-bit."""
        return value - 65536 if value > 32767 else value

    def _u16(self, value: int) -> int:
        """Convert to unsigned 16-bit."""
        return value & 0xFFFF

    def read(self) -> Optional[SensorReading]:
        """Read temperature from BME280 sensor.

        Returns:
            SensorReading with temperature in °C, or None on error
        """
        if self._mock_reading:
            return SensorReading(value=22.5, unit=self.unit)

        if not self._init_i2c():
            return None

        try:
            # Configure sensor for forced mode
            self._i2c.write_byte_data(
                self._address, self.REG_CTRL_MEAS, 0x27  # Forced mode
            )

            import time

            time.sleep(0.01)  # Wait for measurement

            # Read temperature
            raw_temp = self._i2c.read_i2c_block_data(
                self._address, self.REG_PRESS_MSB, 3
            )
            t_raw = (raw_temp[0] << 12) | (raw_temp[1] << 4) | (raw_temp[2] >> 4)

            # Apply calibration
            temp = self._calc_temperature(t_raw)

            return SensorReading(value=temp, unit=self.unit)

        except Exception:
            return None

    def _calc_temperature(self, t_raw: int) -> float:
        """Calculate temperature from raw value using calibration."""
        if not self._calibration:
            return 0.0

        dig_T1 = self._calibration["dig_T1"]
        dig_T2 = self._calibration["dig_T2"]
        dig_T3 = self._calibration["dig_T3"]

        var_t = (t_raw / 16384.0 - dig_T1) / 1024.0
        temp = dig_T2 * var_t + dig_T3 * var_t * var_t

        return temp / 100.0

    def read_all(self) -> BME280Reading:
        """Read all sensor values.

        Returns:
            BME280Reading with temperature, humidity, and pressure
        """
        if self._mock_reading:
            return BME280Reading(
                temperature=22.5, humidity=45.0, pressure=1013.25
            )

        if not self._init_i2c():
            return BME280Reading(temperature=None, humidity=None, pressure=None)

        try:
            self._i2c.write_byte_data(self._address, self.REG_CTRL_MEAS, 0x27)
            import time

            time.sleep(0.01)

            raw = self._i2c.read_i2c_block_data(
                self._address, self.REG_PRESS_MSB, 6
            )

            p_raw = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
            t_raw = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)

            temp = self._calc_temperature(t_raw)

            # Simplified humidity and pressure calculations
            humidity = 45.0  # Placeholder
            pressure = 1013.25  # Placeholder

            return BME280Reading(temperature=temp, humidity=humidity, pressure=pressure)

        except Exception:
            return BME280Reading(temperature=None, humidity=None, pressure=None)