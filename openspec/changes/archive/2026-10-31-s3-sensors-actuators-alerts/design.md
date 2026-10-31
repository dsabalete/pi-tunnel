# Design

## Context

The project currently has empty `sensors/` and `actuators/` package stubs. Storage is implemented via SQLite with WAL mode. APScheduler is available for periodic polling. This change builds on the existing `storage/persistence` spec and integrates with the command handlers framework.

See `proposal.md` for motivation and scope.

## Goals / Non-Goals

**Goals:**
- Implement sensor abstraction with concrete drivers for DHT22, DS18B20, BME280, and CPU temperature
- Implement actuator abstraction with GPIO relay and LED control
- Provide `/sensors` command for querying readings
- Provide `/on`/`/off` commands for actuator control
- Store sensor readings via existing History API
- Handle hardware errors gracefully without bot crashes

**Non-Goals:**
- Camera integration (T801-T802) - separate change
- Alert engine evaluation (T601-T604) - separate change
- Web UI for sensor visualization - future enhancement

## Decisions

### 1. Sensor Protocol Design
**Decision:** Use ABC protocol with `read()` returning `SensorReading` dataclass containing value, unit, timestamp.

**Rationale:** 
- Consistent interface for all sensor types
- Easy to mock in tests
- Extensible for new sensor types

**Alternatives considered:**
- Generic dict return type - rejected (no type safety)
- Separate read methods per sensor type - rejected (inconsistent interface)

### 2. Driver Implementation Strategy
**Decision:** Implement each sensor driver in its own file under `sensors/drivers/` with factory pattern for instantiation.

**Rationale:**
- Isolation of hardware-specific code
- Easy to add/remove drivers
- Clear separation of concerns

**Drivers:**
- `dht22.py`: gpiozero-based DHT22 (temperature + humidity)
- `ds18b20.py`: 1-Wire interface (temperature)
- `bme280.py`: I²C bus via smbus2 (temperature, humidity, pressure)
- `cpu_temp.py`: psutil fallback for CPU temperature

### 3. APScheduler Polling
**Decision:** Use existing APScheduler scheduler from config/core to poll sensors at configurable intervals.

**Rationale:**
- No new dependencies
- Consistent with existing scheduler pattern
- Job persists across restarts via SQLite storage

### 4. Actuator GPIO Strategy
**Decision:** Use gpiozero `OutputDevice` for relay control, PWM-capable pins for LED control.

**Rationale:**
- gpiozero already in requirements
- Simple, well-documented API
- Context manager support for cleanup

**Alternatives considered:**
- Direct RPi.GPIO calls - rejected (more verbose)
- pigpio library - rejected (additional system dependency)

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| GPIO access requires root/sudo | Document in OPERATIONS.md; use systemd service user |
| Sensor drivers may fail on non-Pi hardware | Fallback drivers or test mocks |
| APScheduler jobs accumulate without cleanup | Limit concurrent jobs; job IDs based on sensor ID |
| Missing pull-up resistor on 1-Wire | Error handling in DS18B20 driver |

## Migration Plan

1. Create `sensors/base.py` with protocol and dataclasses
2. Create `actuators/base.py` with protocol
3. Implement each sensor driver
4. Create sensor registry with config loading
5. Implement actuator classes
6. Add command handlers for `/sensors`, `/on`, `/off`
7. Add APScheduler job setup in bot initialization
8. Create unit tests for all components
9. Create integration tests with mocked GPIO

## Open Questions

1. **Sensor ID generation**: Should sensor IDs be auto-generated (UUID) or configured manually in config.yaml?
   - Default: Use configured `id` field from config; if missing, derive from sensor type + pin

2. **Error retry policy**: Should failed sensor reads be retried immediately or skipped?
   - Default: Skip reading, log error, return null value for that cycle