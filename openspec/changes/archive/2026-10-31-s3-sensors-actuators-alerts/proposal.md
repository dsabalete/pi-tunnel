# Proposal

## Why

Sprint 3 (T401-T404) defines sensor drivers and actuators for PiTunnel to read environmental data (temperature, humidity, pressure) and control GPIO devices (relays, LEDs). The sensors and actuators are prerequisites for Sprint 5 (Alerts) to evaluate conditions and Sprint 6 (Camera) for optional photo capture. Implementation is currently pending with only empty module stubs.

## What Changes

- Create `sensors/base.py`: `Sensor` protocol and `SensorReading` dataclass
- Create `sensors/drivers/`: Concrete implementations for DHT22, DS18B20, BME280, CPU temp
- Create `sensors/registry.py`: Load and instantiate sensors from config
- Create `actuators/base.py`: `Actuator` protocol with `on()`, `off()`, `state()` methods
- Create `actuators/relay.py`: `RelayActuator` and `LEDActuator` implementations
- Create `/sensors` and `/on` `/off` command handlers
- Add storage integration for sensor readings via `History.log_sensor_reading()`

## Capabilities

### New Capabilities
- `sensors/monitoring`: Sensor abstraction, driver implementations, automatic polling with APScheduler, and `/sensors` command interface
- `actuators/control`: Actuator abstraction, GPIO relay/LED control, and `/on` `/off` command handlers

### Modified Capabilities
None - these are new capabilities building on existing storage spec.

## Impact

- **Affected code**: New files under `src/pitunnel/sensors/` and `src/pitunnel/actuators/`
- **Tests**: New test files `tests/test_sensors.py` and `tests/test_actuators.py`
- **Dependencies**: Uses existing `gpiozero`, `smbus2`, `psutil` (already in requirements.txt)
- **Systems**: Adds sensor polling jobs and actuator handlers to bot command set