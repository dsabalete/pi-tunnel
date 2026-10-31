# Design

## Context

The actuator implementation is partially complete:
- `sensors/base.py` and driver implementations are complete
- `actuators/base.py`, `relays.py`, and `led.py` are complete
- `actuators/registry.py` exists but incomplete
- Command handlers for `/on`/`/off` are not yet integrated

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Complete `actuators/registry.py` for actuator management
- Integrate `/on <id>` and `/off <id>` command handlers
- Add proper validation and error handling
- Add unit tests for complete actuator functionality

**Non-Goals:**
- Modify existing sensor implementations
- Add new sensor types

## Decisions

### 1. Actuator Registry Completion
**Decision:** Complete the existing registry with configuration loading and actuator lookup.

**Rationale:**
- Already started in s3-sensors-actuators-alerts change
- Provides uniform interface for actuator management
- Required for command handler access

### 2. Command Handler Design
**Decision:** Reuse existing confirmation flow from `/cmd` handler for destructive actions.

**Rationale:**
- Consistent user experience across all commands
- Confirmation manager already tested
- Reduces code duplication

### 3. Error Handling
**Decision:** Return None from sensor/actuator read failures, log warnings.

**Rationale:**
- Graceful degradation - bot stays up even if hardware fails
- Consistent with existing error handling patterns

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| GPIO permission denied | Document systemd service user setup |
| Actuator ID not found | Return friendly "not found" message |
| Hardware disconnect | Return None gracefully, don't crash bot |

## Migration Plan

1. Complete `actuators/registry.py` with proper config loading
2. Add `/on`/`/off` handlers to `commands/handlers.py`
3. Add unit tests for new functionality
4. Run full test suite

## Open Questions

None - implementation follows existing patterns.