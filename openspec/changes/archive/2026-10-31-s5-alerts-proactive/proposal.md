# Proposal

## Why

Sprint 5 (T601-T604) defines the alerts and proactive notifications system. This is a critical feature that enables PiTunnel to monitor sensor conditions and proactively notify authorized users. The implementation builds on the existing sensor drivers (Sprint 3) and storage (Sprint 2), and is a prerequisite for the camera and advanced monitoring features in later sprints.

The current codebase has the alert engine stub (`src/pitunnel/alerts/engine.py`) but the core functionality is not yet implemented:
- Rule evaluation against sensor readings is not connected
- Cooldown enforcement is not working
- Startup notifications are not sent
- The `/alerts` command handler is partially implemented but doesn't query alert history

This change completes the alerts system that is essential for the bot's proactive monitoring capabilities.

## What Changes

- Complete `alerts/engine.py` with rule evaluation, cooldown enforcement, and startup notification
- Implement `/alerts` command handler with full rule status display
- Add startup notification on bot initialization
- Integrate alert history with SQLite storage
- Add unit tests for alert engine functionality

## Capabilities

### New Capabilities
- `alerts/proactive`: Alert rule evaluation, cooldown enforcement, and Telegram notifications

### Modified Capabilities
None - this completes the existing `alerts/proactive` specification.

## Impact

- **Affected code**: `src/pitunnel/alerts/engine.py`, `src/pitunnel/commands/handlers.py`, `src/pitunnel/storage/history.py`
- **Tests**: New test file `tests/test_alerts.py`
- **Dependencies**: Uses existing `History` class, `gpiozero`, `psutil` (already in requirements)
- **Systems**: Adds Telegram alert notifications to bot functionality