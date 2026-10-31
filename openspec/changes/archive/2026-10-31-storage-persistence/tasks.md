# Tasks

## 1. Storage module - Database layer (T701)

- [x] 1.1 Create `src/pitunnel/storage/db.py` with `Database` class, `connect()` returning SQLite connection with WAL mode, `init_schema()` creating `schema_version` table, verify import succeeds
- [x] 1.2 Implement migration system: list of `(version, sql)` tuples, `migrate()` applies pending migrations sequentially, verify running twice is idempotent
- [x] 1.3 Add migrations for three tables: `command_history`, `sensor_readings`, `alert_history` with indexes, verify `sqlite3 /app/data/db.sqlite3 ".schema"` shows all tables
- [x] 1.4 Add `get_connection()` context manager for safe connection handling, verify unit test can execute queries

## 2. Storage module - History API (T703)

- [x] 2.1 Create `src/pitunnel/storage/history.py` with `log_command(ts, user_id, alias, args, exit_code, stdout, stderr)`, verify row inserted into `command_history`
- [x] 2.2 Implement `get_history(limit=10) -> list[dict]` returning most recent commands, verify `/history 5` returns correct count and order
- [x] 2.3 Implement `log_sensor_reading(ts, sensor_id, value, unit)` and `get_readings(sensor_id, since_ts=None)`, verify unit test inserts and queries readings
- [x] 2.4 Implement `log_alert(ts, rule_id, sensor_id, value)` and `get_last_alert_ts(rule_id) -> float | None`, verify alert engine can use it for cooldown
- [x] 2.5 Implement `purge_older_than(days=30) -> int` returning rows deleted, verify daily APScheduler job removes old rows from all tables

## 3. Integration - Command logging (T701/T703)

- [x] 3.1 Modify `commands/executor.py` to accept `history_logger` and call `log_command()` after each execution, verify command row has all fields populated
- [x] 3.2 Update `core/bot.py` to instantiate `Database` and `History` and pass to `CommandExecutor`, verify no circular imports
- [x] 3.3 Add `/history [n]` handler in `commands/handlers.py` using `get_history()`, verify output matches i18n format

## 4. Integration - Alerts engine (T702)

- [x] 4.1 Modify `alerts/engine.py` to use `history.get_last_alert_ts()` and `history.log_alert()` instead of ad-hoc table, verify cooldown works with unified table
- [x] 4.2 Ensure `alert_history` migration includes `sensor_id` and `value` columns (extend existing table), verify existing cooldown timestamps preserved

## 5. Scheduler - Retention purge

- [x] 5.1 Add daily APScheduler job in `core/bot.py` at 03:00 calling `history.purge_older_than(config.limits.history_retention_days)`, verify job registered
- [x] 5.2 Add `history_retention_days` to `config.yaml.example` (default 30), verify config loads correctly
- [x] 5.3 Add `wal_checkpoint(TRUNCATE)` in purge job to control WAL file size, verify WAL file doesn't grow unbounded

## 6. Tests and Documentation

- [x] 6.1 Add unit tests for `db.py` (migrations, schema version), `history.py` (log/get/purge), verify `pytest tests/test_storage.py -v` passes
- [x] 6.2 Add integration test: execute command → verify `/history` shows it → trigger alert → verify `alert_history` has full row
- [x] 6.3 Update `docs/OPERATIONS.md` with storage section: database location, retention config, backup notes

## Workflow follow-up

- Archive the change after review and validation passes
- Verify archived specs `storage/persistence` and updated `alerts/proactive` in main specs