# Tasks

## 1. Verify System Status Implementation

- [x] 1.1 Verify `get_system_status()` returns all required metrics (CPU%, RAM%, CPU temp, disk `/`, disk `/mnt/nas`, uptime, local IP, public IP) - run `python -c "from pitunnel.system.status import get_system_status; print(get_system_status())"`
- [x] 1.2 Verify public IP caching works (second call within 10 min uses cache) - check `_public_ip_cache` module variable behavior
- [x] 1.3 Verify public IP timeout fallback (3s timeout → "unknown") - test with network delay or mock
- [x] 1.4 Verify `/status` handler formats output as Markdown with all labels - send `/status` to bot and check response format

## 2. Verify Storage Persistence Implementation

- [x] 2.1 Verify SQLite WAL mode enabled - check `PRAGMA journal_mode` returns `wal` on connection
- [x] 2.2 Verify schema migrations create tables: `command_history`, `sensor_readings`, `alert_history`, `schema_version` - inspect `sqlite3 db.sqlite3 ".schema"`
- [x] 2.3 Verify `History.log_command()` inserts row with all fields - call directly and query back
- [x] 2.4 Verify `History.get_history(limit=N)` returns N most recent commands ordered by timestamp descending
- [x] 2.5 Verify `History.log_sensor_reading()` and `get_readings(sensor_id, since_ts)` work correctly
- [x] 2.6 Verify `History.log_alert()` and `get_last_alert_ts(rule_id)` work for cooldown tracking
- [x] 2.7 Verify `History.purge_older_than(days)` deletes old rows from all three tables and runs WAL checkpoint

## 3. Verify Command Handler Integration

- [x] 3.1 Verify `/history [n]` handler returns formatted history - test with bot
- [x] 3.2 Verify `/history` with empty database returns appropriate message
- [x] 3.3 Verify `/alerts` handler loads rules, queries alert_history for cooldown, shows status (OK/COOLDOWN)
- [x] 3.4 Verify startup notification sent on bot start (check `AlertEngine.should_send_startup()`)

## 4. Add Unit Tests

- [x] 4.1 Add unit tests for `pitunnel.system.status.get_system_status()` with mocked `psutil` and `urllib` - verify all metrics returned, cache behavior, timeout fallback
- [x] 4.2 Add unit tests for `pitunnel.storage.db.Database` - test WAL mode, migrations, schema version tracking
- [x] 4.3 Add unit tests for `pitunnel.storage.history.History` - test all CRUD operations with temporary SQLite database
- [x] 4.4 Add unit tests for alert cooldown logic using `History.get_last_alert_ts()`

## 5. Add Integration Tests

- [x] 5.1 Add integration test for `/status` command using PTB `TestClient` - verify response contains all metrics in Markdown
- [x] 5.2 Add integration test for `/history` command using PTB `TestClient` - verify history entries returned correctly
- [x] 5.3 Add integration test for `/alerts` command using PTB `TestClient` - verify rule statuses displayed

## 6. Run Full Test Suite

- [x] 6.1 Run `pytest` and verify all new tests pass
- [x] 6.2 Run `pytest --cov=pitunnel --cov-fail-under=85` to ensure coverage threshold met
- [x] 6.3 Run `ruff check .` and `mypy src/` to ensure code quality

## Workflow follow-up

- Archive the change after implementation verification and test coverage are complete