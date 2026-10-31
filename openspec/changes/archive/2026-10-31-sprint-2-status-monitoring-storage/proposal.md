# Proposal

## Why

Sprint 2 tasks (T301–T302, T701–T703) define system monitoring (`/status`) and SQLite persistence with command/sensor history. The implementation for these capabilities already exists in the codebase:
- `src/pitunnel/system/status.py` provides full system metrics collection (CPU, RAM, temperature, disk, uptime, local/public IP) with 10-minute public IP caching
- `src/pitunnel/storage/db.py` and `history.py` provide SQLite WAL-mode database with schema migrations, command history, sensor readings, and alert history persistence
- Command handlers for `/status`, `/history`, and `/alerts` are implemented in `src/pitunnel/commands/handlers.py`

This change documents the current implementation state, verifies alignment with existing specs, and adds any missing test coverage or integration points to mark Sprint 2 complete.

## What Changes

- Document existing `/status` implementation and verify it meets all requirements in `system/status` spec
- Document existing storage persistence implementation and verify it meets all requirements in `storage/persistence` spec
- Add integration tests for `/status` and `/history` commands
- Add unit tests for system status collection and storage history API
- Ensure alert history integration with storage is functional (used by alert engine for cooldown)

## Capabilities

### Modified Capabilities
- `system/status`: No requirement changes - implementation complete per existing spec
- `storage/persistence`: No requirement changes - implementation complete per existing spec

### New Capabilities
None - all capabilities already exist in main specs.

## Impact

- **Affected code**: `src/pitunnel/system/status.py`, `src/pitunnel/storage/db.py`, `src/pitunnel/storage/history.py`, `src/pitunnel/commands/handlers.py`
- **Tests**: New integration tests needed for `/status` and `/history` commands; unit tests for status collection and history API
- **Dependencies**: No new dependencies - uses existing `psutil`, `sqlite3`, `aiofiles`
- **Systems**: None - implementation is complete and working