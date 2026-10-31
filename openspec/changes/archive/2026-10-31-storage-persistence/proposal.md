# Proposal

## Why

PiTunnel currently lacks a persistence layer for command history, sensor readings, and alert history. The alerts engine already uses a basic SQLite table (`alert_history`) for cooldown tracking, but there's no unified storage module, schema migrations, or APIs for querying history. Implementing T701–T703 from the roadmap provides the foundation for `/history`, sensor analytics, and audit trails.

## What Changes

- Create `src/pitunnel/storage/db.py` with SQLite WAL connection, schema versioning, and migration framework
- Create database tables: `command_history`, `sensor_readings`, `alert_history` (extending the existing minimal table)
- Create `src/pitunnel/storage/history.py` with `log_command()`, `get_history(limit)`, `purge_older_than(days)` functions
- Integrate with command executor to log every command execution
- Integrate with alerts engine to use the unified `alert_history` table
- Add daily APScheduler job for 30-day retention purge (configurable)

## Capabilities

### New Capabilities

- `storage/persistence`: Provides durable SQLite storage with schema migrations for command history, sensor readings, and alert history; exposes query APIs for history commands and analytics

### Modified Capabilities

- `alerts/proactive`: The alert engine currently uses a minimal `alert_history` table; this change extends it with full schema (sensor_id, value columns) and uses the unified storage module

## Impact

- Affected code: New `src/pitunnel/storage/` module; modifications to `commands/executor.py` (command logging), `alerts/engine.py` (use unified storage), `commands/handlers.py` (`/history` handler)
- Dependencies: `aiofiles` already in requirements; `apscheduler` already used for alerts
- Systems: SQLite database file at `/app/data/db.sqlite3` (Docker) or `db.sqlite3` (native); WAL mode for concurrent access