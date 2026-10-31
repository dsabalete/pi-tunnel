# Spec Delta

## Purpose

Provides sensor abstraction for reading environmental data (temperature, humidity, pressure) from DHT22, DS18B20, BME280, and CPU sensors via GPIO and I²C interfaces, with periodic polling to SQLite storage and queryable via `/sensors` Telegram command.

## ADDED Requirements

### Requirement: Sensor protocol definition
The system SHALL define a `Sensor` protocol with `read() -> SensorReading`, `id`, `type`, and `unit` attributes for consistent driver interfaces.

#### Scenario: All sensors implement protocol
- **WHEN** a sensor driver is instantiated
- **THEN** it implements the Sensor protocol with id, type, unit, and read() method

### Requirement: Sensor reading persistence
The system SHALL store sensor readings with timestamp, sensor_id, value, and unit via the existing `History.log_sensor_reading()` API.

#### Scenario: Reading stored on poll
- **WHEN** a sensor driver produces a reading during polling
- **THEN** a row is inserted into `sensor_readings` table with all fields

### Requirement: Sensor registry manages drivers
The system SHALL load sensor configurations from config, instantiate appropriate drivers, and return them for polling.

#### Scenario: Registry creates DHT22 sensor
- **WHEN** config specifies a DHT22 sensor type
- **THEN** registry returns a DHT22Sensor instance configured with GPIO pin

### Requirement: Periodic sensor polling
The system SHALL use APScheduler to poll sensors at configurable intervals and store results.

#### Scenario: Polling saves to database
- **WHEN** 30 seconds have elapsed since last poll
- **THEN** sensor.read() is called and result is stored via History.log_sensor_reading()

### Requirement: Sensors command endpoint
The system SHALL provide a `/sensors` command that returns the latest readings from all sensors or a specific sensor by ID.

#### Scenario: Query all sensors
- **WHEN** authorized user sends `/sensors`
- **THEN** bot replies with latest reading for each configured sensor

#### Scenario: Query single sensor
- **WHEN** authorized user sends `/sensors temp-salon`
- **THEN** bot replies with only that sensor's latest reading

### Requirement: Hardware error handling
The system SHALL handle sensor communication failures gracefully without crashing the bot.

#### Scenario: Sensor disconnected
- **WHEN** a sensor read times out or raises an exception
- **THEN** error is logged and `null` value returned (does not crash bot)