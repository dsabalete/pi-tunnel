# Design

## Context

The alerts system is partially implemented with the alert engine stub at `src/pitunnel/alerts/engine.py`. This design completes the implementation building on existing components:
- Sensor drivers from Sprint 3 (DHT22, DS18B20, BME280, CPU temp)
- Storage from Sprint 2 (SQLite WAL-mode, history tables)
- Bot command handlers from Sprints 1-2

See `proposal.md` for motivation and scope.

## Goals / Non-Goals

**Goals:**
- Complete alert rule evaluation against sensor readings
- Implement cooldown enforcement with SQLite persistence
- Add startup notification on bot init
- Provide `/alerts` command with full rule status display
- Integrate with existing storage and sensor infrastructure

**Non-Goals:**
- Camera integration (T801-T802) - separate change
- Advanced analytics (trends, predictions) - future enhancement
- Web dashboard for alert management - future enhancement

## Decisions

### 1. Alert Engine Design
**Decision:** Use the existing `AlertEngine` class at `src/pitunnel/alerts/engine.py` as the central component, integrating with the `History` class for cooldown persistence.

**Rationale:**
- Already exists in codebase, minimal refactoring needed
- Single source of truth for alert state
- Clean separation of concerns

**Key design decisions:**
- Rule evaluation happens in `evaluate_rules()` method
- Cooldown checks use `History.get_last_alert_ts()` 
- Startup notification tracked via `_startup_notification_sent` flag
- Alerts are dispatched to all authorized users

### 2. Command Handler Design
**Decision:** Add `/alerts` handler that queries alert history from storage and displays rule status.

**Rationale:**
- Provides user-visible status of all rules
- Integrates with storage for cooldown tracking
- Consistent with other command handlers (`/status`, `/sensors`)

### 3. Startup Notification
**Decision:** Track startup notification in `AlertEngine._startup_notification_sent` flag, sent once on bot init.

**Rationale:**
- Prevents duplicate startup messages
- Persists across bot restarts via state tracking
- Simple boolean flag, minimal complexity

### 4. Cooldown Enforcement
**Decision:** Use `History.get_last_alert_ts()` for cooldown checks, with configurable `cooldown_min` from rule configuration.

**Rationale:**
- Persists across bot restarts (stored in SQLite)
- Configurable per rule
- Reuses existing storage infrastructure

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Rule evaluation performance | Rule set is small (typically <20), performance impact minimal |
| Cooldown state loss on DB corrupt | Regular backups recommended (T704) |
| Missing sensor readings | Graceful handling - rule simply not triggered |
| Concurrent alert evaluation | Single-threaded bot execution, no race conditions |

## Migration Plan

1. Complete `alerts/engine.py` with full rule evaluation and cooldown
2. Add `/alerts` command handler in `commands/handlers.py`
3. Add startup notification call in bot initialization
4. Add unit tests for alert engine functionality
5. Run full test suite

## Open Questions

None - implementation follows existing patterns and reuses established components.