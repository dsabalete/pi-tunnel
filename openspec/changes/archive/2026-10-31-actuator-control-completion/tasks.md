# Tasks

## 1. Actuator Registry Completion

- [x] 1.1 Complete `actuators/registry.py` with config loading from YAML
- [x] 1.2 Implement actuator ID validation and lookup
- [x] 1.3 Add unit tests for ActuatorRegistry
- [x] 2.1 Add `/on <id>` command handler in `commands/handlers.py`
- [x] 2.2 Add `/off <id>` command handler in `commands/handlers.py`
- [x] 2.3 Implement actuator validation in handlers (check if ID exists)
- [x] 2.4 Add confirmation flow integration for destructive actions
- [x] 3.1 Add unit tests for actuator command handlers
- [x] 3.2 Test successful actuator toggle
- [x] 3.3 Test non-existent actuator ID error
- [x] 3.4 Test confirmation flow for destructive actions
- [x] 4.1 Test `/on` handler with mocked actuator registry
- [x] 4.2 Test `/off` handler with mocked actuator registry
- [x] 4.3 Verify response formatting with Markdown labels
- [x] 5.1 Run `pytest` and verify all tests pass
- [x] 5.2 Run `ruff check .` to ensure code quality

## Workflow follow-up

- Archive the change after implementation verification