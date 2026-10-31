# Design

## Context

The implementation for Sprint 2 capabilities already exists in the codebase:
- `src/pitunnel/system/status.py` - Complete system status collection with caching
- `src/pitunnel/storage/db.py` - SQLite WAL-mode database with migrations
- `src/pitunnel/storage/history.py` - High-level history API for commands, sensors, alerts
- `src/pitunnel/commands/handlers.py` - Command handlers for `/status`, `/history`, `/alerts`

This design documents the existing architecture and identifies any gaps for test coverage.

## Goals / Non-Goals

**Goals:**
- Document the existing implementation architecture for system status and storage
- Define test strategy for integration and unit tests
- Ensure alert engine properly uses storage for cooldown persistence

**Non-Goals:**
- Refactoring existing implementation (it's complete and functional)
- Adding new features beyond what's in Sprint 2 specs
- Changing database schema or API contracts

## Decisions

### 1. System Status Collection Architecture
**Decision**: Use `psutil` for system metrics with direct `/sys/class/thermal` read for CPU temperature, `urllib` for public IP with in-memory cache.

**Rationale**: 
- `psutil` is cross-platform, well-maintained, and already a project dependency
- Direct thermal zone read works on Raspberry Pi without additional deps
- In-memory cache with 600s TTL avoids external API rate limits
- Module-level cache dict is simple and sufficient for single-process bot

**Alternatives considered**:
- `aiohttp` for async public IP fetch - rejected (adds dependency, overkill for 1 request/10min)
- External service wrapper class - rejected (current function-based approach is sufficient)

### 2. SQLite Storage Architecture
**Decision**: Use `sqlite3` standard library with WAL mode, context manager for connections, schema migrations via versioned SQL scripts.

**Rationale**:
- Zero dependencies, part of Python stdlib
- WAL mode enables concurrent reads/writes (bot + scheduler)
- Explicit migration list in code ensures reproducibility
- Context manager pattern ensures proper connection cleanup

**Alternatives considered**:
- `aiosqlite` for async - rejected (sync is fine for SQLite, simpler)
- ORM (SQLAlchemy) - rejected (overhead not justified for 3 tables)
- Separate migration files - rejected (inline list is more portable)

### 3. Alert Engine Cooldown Integration
**Decision**: AlertEngine reads `alert_history` directly via `History.get_last_alert_ts()` for cooldown checks.

**Rationale**:
- Single source of truth for alert timestamps
- Cooldown persists across restarts (survives in SQLite)
- Decouples alert evaluation from storage implementation

**Alternatives considered**:
- In-memory cooldown tracking - rejected (loses state on restart)
- Separate cooldown table - rejected (redundant with alert_history)

### 4. Test Strategy
**Decision**: 
- Unit tests for `get_system_status()` with mocked `psutil` and `urllib`
- Unit tests for `History` class with temporary SQLite database
- Integration tests for `/status` and `/history` handlers using PTB's `TestClient`

**Rationale**:
- Mocking external deps (psutil, network) keeps unit tests fast and deterministic
- Temporary SQLite DB ensures isolation for storage tests
- PTB TestClient enables async handler testing without real Telegram

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Public IP cache not thread-safe | Single-threaded bot process; if scaled to multi-worker, use Redis |
| SQLite WAL file growth under heavy write load | `purge_older_than()` includes `wal_checkpoint(TRUNCATE)` |
| CPU temp read fails on non-Pi hardware | Falls back to `psutil.sensors_temperatures()` then returns `None` |
| Schema migrations not idempotent if run twice | Migrations check `schema_version` before applying |
| Handler tests depend on global `_alert_engine` | Reset global in test setup/teardown |

## Migration Plan

No migration needed - implementation is complete and deployed. This change adds documentation and tests only.

## Open Questions

None - all technical decisions are resolved in existing code.