# Operations Runbook

## System Monitoring

The `/status` command reports host metrics via Telegram.

Public IP caching: The public IP address fetched from `https://api.ipify.org` is cached in-memory for 10 minutes (600s TTL) to avoid rate-limiting external service. Cache is per-process and resets on bot restart. After TTL expiry, next `/status` call triggers a fresh HTTP request with 3s timeout. On timeout or error, public IP is reported as `unknown`.

## Storage & Persistence

PiTunnel uses SQLite for persistent storage of command history.

### Database Location

- Docker: `/app/data/db.sqlite3` (mounted from host `./data/`)
- Native: `db.sqlite3` in working directory

### Tables

- `command_history`: Timestamp, user ID, command alias, arguments, exit code, stdout, stderr
- `schema_version`: Tracks database schema version for migrations

### Retention Policy

Configured via `config.yaml` under `limits.history_retention_days` (default: 30 days).

A daily APScheduler job runs at 03:00 local time to purge entries older than the retention period from the command history table. The job also performs a WAL checkpoint (`TRUNCATE` mode) to control WAL file size.

### Commands

- `/history [n]` – Show last n command executions (default 10)

### Backup & Recovery

To backup the database:
```bash
sqlite3 /path/to/db.sqlite3 ".backup /backup/location/pi-tunnel-backup.db"
```

To restore:
```bash
sqlite3 /path/to/db.sqlite3 ".restore /backup/location/pi-tunnel-backup.db"
```

### Monitoring Tips

- Check `sqlite3 /path/to/db.sqlite3 ".schema"` to verify schema version
- Monitor database file size; WAL file should remain small due to daily checkpoint
- If disk space is low, reduce `history_retention_days` in config
- The database uses WAL mode for concurrent access; ensure host filesystem supports it