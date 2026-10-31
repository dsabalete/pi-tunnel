# Design

## Context

PiTunnel has a basic `alert_history` table created by the alerts engine for cooldown tracking. There's no unified storage module, no schema migration system, and no persistence for command history or sensor readings. The database file lives at `/app/data/db.sqlite3` (Docker) or `db.sqlite3` (native).

## Goals / Non-Goals

**Goals:**
- Create `storage/db.py` with SQLite WAL connection, schema version tracking, and migration runner
- Create three tables: `command_history`, `sensor_readings`, `alert_history` (extended)
- Create `storage/history.py` with `log_command()`, `get_history()`, `purge_older_than()`
- Integrate command logging into `CommandExecutor`
- Integrate alert history into `AlertEngine` (replace ad-hoc table with unified schema)
- Add daily APScheduler purge job (30-day default retention)
- Implement `/history` command handler

**Non-Goals:**
- ORM or query builder (raw SQL is fine for this scope)
- Backup/restore tooling (T704 - separate task)
- Sensor reading ingestion (sensors not yet implemented - T401-T404)
- Metrics/analytics API (T1101 - separate task)

## Decisions

**SQLite WAL mode:** Use `PRAGMA journal_mode=WAL` for concurrent access. Rationale: Allows readers during writes; simpler than connection pooling.

**Schema version table:** Single-row table `schema_version(version INTEGER)` with `user_version` pragma as fallback. Rationale: Minimal, no migration library needed.

**Migration system:** Inline SQL migrations in `db.py` as list of `(version, sql)` tuples, applied sequentially at startup. Rationale: Zero dependencies; schema is small and stable.

**Table schemas:**
- `command_history(ts REAL, user_id INTEGER, alias TEXT, args TEXT, exit_code INTEGER, stdout TEXT, stderr TEXT)` with index on `ts`
- `sensor_readings(ts REAL, sensor_id TEXT, value REAL, unit TEXT)` with index on `(sensor_id, ts)`
- `alert_history(ts REAL, rule_id TEXT, sensor_id TEXT, value REAL)` with index on `(rule_id, ts)`

**Retention purge:** Daily APScheduler job at 03:00 local time calling `purge_older_than(days)` with config value (default 30). Rationale: Off-peak; simple cron-style.

**Database path:** Use `/app/data/db.sqlite3` (Docker) or `db.sqlite3` (native). Configurable via `Config.storage.database_path`.

**WAL checkpointing:** Periodic `PRAGMA wal_checkpoint(TRUNCATE)` in purge job to control WAL file size.

## Risks / Trade-offs

**Schema migration failures** → Migration runs at startup; if it fails, bot exits with clear error. Mitigation: test migrations in CI; keep migrations idempotent where possible.

**SQLite locking under load** → WAL helps but heavy concurrent writes can still block. Mitigation: use short transactions; `command_history` writes are fast; sensor reads are batched.

**WAL file growth** → Uncheckpointed WAL can grow large. Mitigation: `wal_checkpoint(TRUNCATE)` in daily purge job.

**Disk space** → Unbounded history could fill disk. Mitigation: default 30-day retention; configurable; purge job runs daily.

## Migration Plan

1. Create `storage/db.py` and `storage/history.py`
2. Run bot once - migrations create tables automatically
3. Verify `/history` returns empty list (no commands yet)
4. Execute a test command - verify it appears in `/history`
5. Trigger an alert - verify it appears in `alert_history` with full schema
6. Deploy - no manual DB steps needed

## Open Questions

- Should `sensor_readings` use `REAL` for value or support `TEXT` for string states? (Deferrable; current sensors return numeric)
- Should purge job run in separate process to avoid blocking bot? (Deferrable; current job is fast)