# Tasks

## 1. Sensor Protocol and Base Types

- [x] 1.1 Create `sensors/base.py` with `Sensor` protocol and `SensorReading` dataclass
- [x] 1.2 Verify protocol with simple test mock implementation

## 2. Sensor Drivers

- [x] 2.1 Implement `sensors/drivers/dht22.py` - DHT22Sensor using gpiozero (temperature + humidity)
- [x] 2.2 Implement `sensors/drivers/ds18b20.py` - DS18B20Sensor using w1thermsensor (temperature)
- [x] 2.3 Implement `sensors/drivers/bme280.py` - BME280Sensor using smbus2 (temp, humidity, pressure)
- [x] 2.4 Implement `sensors/drivers/cpu_temp.py` - CPUTempSensor using psutil (CPU temperature)
- [x] 3.1 Create `sensors/registry.py` with SensorRegistry class
- [x] 3.2 Implement config loading for sensors list from `config.yaml`
- [x] 3.3 Implement driver factory pattern for creating sensor instances
- [ ] 2.5 Add unit tests for each sensor driver with hardware mocks
- [ ] 2.6 Test sensor error handling (disconnected sensor returns null gracefully)

## 3. Sensor Registry

- [ ] 3.1 Create `sensors/registry.py` with SensorRegistry class
- [ ] 3.2 Implement config loading for sensors list from `config.yaml`
- [ ] 3.3 Implement driver factory pattern for creating sensor instances
- [ ] 3.4 Add integration test for sensor registry with mock config

## 4. APScheduler Polling

- [ ] 4.1 Add `start_polling()` method to SensorRegistry for APScheduler
- [ ] 4.2 Configure polling interval from config (default: 30s)
- [ ] 4.3 Verify readings stored via `History.log_sensor_reading()` on poll
- [ ] 4.4 Add unit test for polling job execution

## 5. Actuator Protocol and Base Types

- [ ] 5.1 Create `actuators/base.py` with `Actuator` protocol (on, off, state methods)
- [ ] 5.2 Define ActuatorReading or metadata for actuator status

## 6. Actuator Implementations

- [ ] 6.1 Implement `actuators/relay.py` - RelayActuator using gpiozero OutputDevice
- [ ] 6.2 Implement `actuators/led.py` - LEDActuator with PWM support
- [ ] 6.3 Add unit tests for actuator classes with mocked GPIO

## 7. Actuator Registry

- [ ] 7.1 Create `actuators/registry.py` for actuator management
- [ ] 7.2 Implement config loading for actuators list from `config.yaml`
- [ ] 7.3 Handle actuator ID validation and lookup

## 8. Command Handlers

- [ ] 8.1 Add `/sensors` command handler in `commands/handlers.py`
- [ ] 8.2 Add `/on <id>` command handler for actuator control
- [ ] 8.3 Add `/off <id>` command handler for actuator control
- [ ] 8.4 Add unit tests for sensor and actuator command handlers
- [ ] 8.5 Verify response formatting with Markdown labels

## 9. Update Bot Initialization

- [ ] 9.1 Integrate sensor polling job into bot startup
- [ ] 9.2 Register actuators in bot_data for handler access
- [ ] 9.3 Verify APScheduler job runs on bot start

## 10. Run Full Test Suite

- [ ] 10.1 Run `pytest` and verify all new tests pass
- [ ] 10.2 Run `pytest --cov=pitunnel --cov-fail-under=85` to ensure coverage threshold met
- [ ] 10.3 Run `ruff check .` to ensure code quality

## Workflow follow-up

- Archive the change after implementation verification and test coverage are complete