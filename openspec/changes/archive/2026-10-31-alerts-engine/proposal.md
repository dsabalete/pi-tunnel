# Proposal

## Why

PiTunnel sensors currently provide raw readings but lack an alerting mechanism to notify users of critical system events (e.g., high temperature). Implementing proactive notifications ensures operators can take timely action.

## What Changes

- Add `alerts/engine.py` to evaluate sensor reading rules (e.g., `> 27.5`) against readings saved in SQLite.
- Implement per-rule cooldown logic (`cooldown_min`) to prevent notification spam.
- Add `on_startup` notification to alert operators when the bot is online.
- Add `/alerts` command to list active rules and their current status (OK / FIRING / COOLDOWN).

## Capabilities

### New Capabilities

- `alerts/proactive`: Enables rules-based monitoring of sensor readings, proactive notifications to authorized users, rule cooldowns, and status reporting via Telegram.

### Modified Capabilities

- *None*

## Impact

- Affected code: New `src/pitunnel/alerts/` package, integration with `sensors` registry, `storage` layer for rule state (cooldowns).
- Dependencies: None added.
- Systems: Adds scheduled task (APScheduler) for alerting, relies on existing sensor readings in SQLite.
