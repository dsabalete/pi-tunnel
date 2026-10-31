"""DHT22 sensor driver using gpiozero."""

from __future__ import annotations

from typing import Optional

from pitunnel.sensors.base import Sensor, SensorReading


class DHT22Sensor(Sensor):
    """DHT22 temperature and humidity sensor.

    Note: For actual hardware, uses bit-banged protocol via RPi.GPIO.
    For testing, can be instantiated with mock_reading=True.
    """

    def __init__(
        self,
        sensor_id: str,
        gpio_pin: int = 4,
        mock_reading: bool = False,
    ):
        """Initialize DHT22 sensor.

        Args:
            sensor_id: Unique identifier for this sensor
            gpio_pin: GPIO pin number (BCM numbering)
            mock_reading: If True, return mock data (for testing)
        """
        self._id = sensor_id
        self._gpio_pin = gpio_pin
        self._mock_reading = mock_reading
        self._type = "dht22"

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
        """Read temperature from DHT22 sensor.

        Returns:
            SensorReading with temperature in °C, or None on error
        """
        if self._mock_reading:
            return SensorReading(value=25.0, unit=self.unit)

        try:
            import RPi.GPIO as gpio
            import time

            # Setup GPIO
            gpio.setmode(gpio.BCM)
            gpio.setup(self._gpio_pin, gpio.OUT)

            # Send start signal
            gpio.output(self._gpio_pin, gpio.LOW)
            time.sleep(0.02)  # 20ms start signal
            gpio.output(self._gpio_pin, gpio.HIGH)
            time.sleep(0.000028)  # 28us wait
            gpio.setup(self._gpio_pin, gpio.IN)

            # Wait for response
            while gpio.input(self._gpio_pin) == gpio.HIGH:
                pass
            while gpio.input(self._gpio_pin) == gpio.LOW:
                pass
            while gpio.input(self._gpio_pin) == gpio.HIGH:
                pass

            # Read data bits
            data = [0] * 40

            for i in range(40):
                while gpio.input(self._gpio_pin) == gpio.LOW:
                    pass
                while gpio.input(self._gpio_pin) == gpio.HIGH:
                    pass

                # Measure pulse length
                count = 0
                start = time.time()
                while gpio.input(self._gpio_pin) == gpio.HIGH:
                    count += 1
                    time.sleep(0.000001)
                    if time.time() - start > 0.0001:
                        break

                # Bit value based on pulse width
                data[i] = 1 if count > 40 else 0

            # Cleanup GPIO
            gpio.cleanup()

            # Convert to temperature
            # Data format: 5 bytes (humidity int, humidity dec, temp int, temp dec, checksum)
            humidity_int = data[0]
            humidity_dec = data[1]
            temp_int = data[2] & 0x7F  # Mask sign bit
            temp_dec = data[3]
            checksum = sum(data[:4]) & 0xFF

            # Verify checksum
            if checksum != data[4]:
                return None

            temperature = temp_int + temp_dec / 10

            return SensorReading(value=temperature, unit=self.unit)

        except Exception:
            # On error, return None (will be logged by caller)
            return None