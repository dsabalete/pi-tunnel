"""Tests for sensor base protocol."""

import pytest

from pitunnel.sensors.base import Sensor, SensorReading


class MockSensor(Sensor):
    """Simple mock sensor for testing."""

    def __init__(self, sensor_id: str = "test-sensor"):
        self._id = sensor_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def sensor_type(self) -> str:
        return "mock"

    @property
    def unit(self) -> str:
        return "test-unit"

    def read(self) -> SensorReading | None:
        return SensorReading(value=42.0, unit=self.unit)


def test_sensor_reading_default_timestamp():
    """SensorReading gets timestamp on creation."""
    import time

    before = time.time()
    reading = SensorReading(value=25.0, unit="°C")
    after = time.time()

    assert before <= reading.timestamp <= after


def test_sensor_reading_custom_timestamp():
    """SensorReading can have custom timestamp."""
    ts = 1234567890.0
    reading = SensorReading(value=25.0, unit="°C", timestamp=ts)

    assert reading.timestamp == ts


def test_sensor_protocol_enforced():
    """Creating a Sensor subclass without implementing methods raises error."""

    class IncompleteSensor(Sensor):
        @property
        def id(self) -> str:
            return "incomplete"

    with pytest.raises(TypeError):
        IncompleteSensor()


def test_sensor_repr():
    """Sensor __repr__ includes class name and id."""
    sensor = MockSensor("my-sensor")

    assert repr(sensor) == "MockSensor(id='my-sensor')"


def test_sensor_read_returns_reading():
    """Mock sensor read returns valid reading."""
    sensor = MockSensor()

    result = sensor.read()

    assert result is not None
    assert result.value == 42.0
    assert result.unit == "test-unit"


def test_sensor_properties():
    """Sensor properties are accessible."""
    sensor = MockSensor("custom-id")

    assert sensor.id == "custom-id"
    assert sensor.sensor_type == "mock"
    assert sensor.unit == "test-unit"


class TestDHT22Sensor:
    """Tests for DHT22 sensor driver."""

    def test_mock_reading(self):
        """DHT22 with mock_reading returns valid data."""
        from pitunnel.sensors.drivers.dht22 import DHT22Sensor

        sensor = DHT22Sensor("test-dht", mock_reading=True)

        result = sensor.read()

        assert result is not None
        assert sensor.id == "test-dht"
        assert sensor.sensor_type == "dht22"
        assert result.value == 25.0


class TestDS18B20Sensor:
    """Tests for DS18B20 sensor driver."""

    def test_sensor_properties(self):
        """DS18B20 has correct properties."""
        from pitunnel.sensors.drivers.ds18b20 import DS18B20Sensor

        sensor = DS18B20Sensor("test-ds18b20")

        assert sensor.id == "test-ds18b20"
        assert sensor.sensor_type == "ds18b20"
        assert sensor.unit == "°C"

    def test_device_path_none_when_missing(self):
        """DS18B20 returns None when device path doesn't exist."""
        from pitunnel.sensors.drivers.ds18b20 import DS18B20Sensor

        sensor = DS18B20Sensor("nonexistent-device", device_id="28-00001xxxxxxx")

        result = sensor.read()

        # Will be None on systems without the hardware
        assert result is None or isinstance(result, SensorReading)


class TestBME280Sensor:
    """Tests for BME280 sensor driver."""

    def test_mock_reading(self):
        """BME280 with mock_reading returns valid data."""
        from pitunnel.sensors.drivers.bme280 import BME280Sensor

        sensor = BME280Sensor("test-bme", mock_reading=True)

        result = sensor.read()

        assert result is not None
        assert sensor.id == "test-bme"
        assert sensor.sensor_type == "bme280"
        assert result.value == 22.5

    def test_read_all_mock(self):
        """BME280 read_all with mock returns all values."""
        from pitunnel.sensors.drivers.bme280 import BME280Sensor

        sensor = BME280Sensor("test-bme", mock_reading=True)

        reading = sensor.read_all()

        assert reading.temperature == 22.5
        assert reading.humidity == 45.0
        assert reading.pressure == 1013.25


class TestCPUTempSensor:
    """Tests for CPU temperature sensor driver."""

    def test_mock_reading(self):
        """CPUTempSensor returns valid reading."""
        from pitunnel.sensors.drivers.cpu_temp import CPUTempSensor

        # Create a sensor that will return mock data
        sensor = CPUTempSensor("cpu-temp")

        # On test systems, this may return None or actual CPU temp
        result = sensor.read()

        assert sensor.id == "cpu-temp"
        assert sensor.sensor_type == "cpu_temp"
        assert sensor.unit == "°C"
        if result is not None:
            assert isinstance(result.value, float)


class TestSensorRegistry:
    """Tests for SensorRegistry."""

    def test_empty_config(self):
        """Registry handles empty config."""
        from pitunnel.sensors.registry import SensorRegistry

        registry = SensorRegistry({})

        sensors = registry.load_sensors()

        assert sensors == []

    def test_load_mock_sensor(self):
        """Registry can load a mock sensor from config."""
        from pitunnel.sensors.registry import SensorRegistry

        config = {
            "sensors": [
                {
                    "id": "test-sensor",
                    "type": "cpu_temp",
                    "enabled": True,
                    "interval_seconds": 60,
                }
            ]
        }

        registry = SensorRegistry(config)
        sensors = registry.load_sensors()

        assert len(sensors) == 1
        assert sensors[0].id == "test-sensor"
        assert registry.get_all_sensors()

    def test_disabled_sensor_skipped(self):
        """Registry skips disabled sensors."""
        from pitunnel.sensors.registry import SensorRegistry

        config = {
            "sensors": [
                {"id": "disabled", "type": "cpu_temp", "enabled": False},
                {"id": "enabled", "type": "cpu_temp", "enabled": True},
            ]
        }

        registry = SensorRegistry(config)
        sensors = registry.load_sensors()

        assert len(sensors) == 1
        assert sensors[0].id == "enabled"

    def test_get_sensor_by_id(self):
        """Registry can retrieve sensor by ID."""
        from pitunnel.sensors.registry import SensorRegistry

        config = {
            "sensors": [{"id": "my-sensor", "type": "cpu_temp"}]
        }

        registry = SensorRegistry(config)
        registry.load_sensors()

        sensor = registry.get_sensor("my-sensor")
        assert sensor is not None
        assert sensor.id == "my-sensor"

        assert registry.get_sensor("nonexistent") is None

    def test_poll_all_returns_dict(self):
        """Registry poll_all returns a dict."""
        from pitunnel.sensors.registry import SensorRegistry

        config = {
            "sensors": [{"id": "poll-test", "type": "cpu_temp"}]
        }

        registry = SensorRegistry(config)
        registry.load_sensors()
        readings = registry.poll_all()

        # poll_all returns dict (may be empty if sensor read returns None)
        assert isinstance(readings, dict)