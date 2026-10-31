# Proposal

## Why

Sprint 4 (T501-T503) defines actuator control via GPIO relays and LEDs with Telegram command handlers. Implementation is partially complete - the base protocol and driver implementations exist, but the command handlers for `/on`/`/off` are not yet integrated with the bot.

## What Changes

- Complete `actuators/registry.py` for actuator management from config
- Add `/on <id>` and `/off <id>` command handlers in `commands/handlers.py`
- Add actuator validation and confirmation flow
- Add unit tests for actuator command handlers
- Integrate actuators into bot initialization

## Capabilities

### Modified Capabilities
- `actuators/control`: The spec already exists - this change completes the implementation

### New Capabilities
None - this is implementation work for existing specs.

## Impact

- **Affected code**: `src/pitunnel/actuators/registry.py`, `src/pitunnel/commands/handlers.py`
- **Tests**: `tests/test_actuators.py` (new), extend `tests/test_handlers.py`
- **Dependencies**: gpiozero already in requirements.txt
- **Systems**: Adds `/on`/`/off` commands to bot's command set