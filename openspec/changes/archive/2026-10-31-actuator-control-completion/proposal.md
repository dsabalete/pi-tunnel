# Proposal

## Why

Sprint 4 (T501-T503) defines actuator control via GPIO relays and LEDs. Partially implemented:
- T501: `actuators/base.py` with `Actuator` protocol - DONE
- T502: `RelayActuator` and `LEDActuator` implementations - DONE
- T503: Handler `/on <id>` `/off <id>` - NOT DONE

This change completes the actuator implementation by adding:
- `actuators/registry.py` for actuator management from config
- `/on <id>` and `/off <id>` command handlers
- Unit tests for actuator functionality
- Integration with existing storage

## What Changes

- Create `actuators/registry.py` with ActuatorRegistry class
- Add `/on <id>` and `/off <id>` command handlers in `commands/handlers.py`
- Add actuator ID validation and existence checking
- Add unit tests for actuator registry and handlers
- Test confirmation flow for destructive actions

## Capabilities

### Modified Capabilities
None - implementation follows existing `actuators/control` spec

## Impact

- **Affected code**: `src/pitunnel/actuators/registry.py`, `src/pitunnel/commands/handlers.py`
- **Tests**: New `tests/test_actuators.py` for actuators, extend handlers tests
- **Dependencies**: gpiozero, psutil (already in requirements)
- **Systems**: Adds `/on`/`/off` commands to bot