# Operations Runbook

## System Monitoring

The `/status` command reports host metrics via Telegram.

Public IP caching: The public IP address fetched from `https://api.ipify.org` is cached in-memory for 10 minutes (600s TTL) to avoid rate-limiting external service. Cache is per-process and resets on bot restart. After TTL expiry, next `/status` call triggers a fresh HTTP request with 3s timeout. On timeout or error, public IP is reported as `unknown`.

## Alerts & Notifications

The `/alerts` command lists all configured alert rules and their status.

### Configuration

Alert rules are defined in `config.yaml` under `alerts.rules`:

```yaml
alerts:
  rules:
    - rule_id: temp-high
      sensor_id: temp-salon
      when: "> 27.5"
      cooldown_min: 30
      enabled: true
```

- `rule_id`: Unique identifier for the rule
- `sensor_id`: Must match a sensor ID defined in the `sensors` section
- `when`: Comparison expression (`>`, `<`, `>=`, `<=`, `==`, `!=`) with a numeric threshold
- `cooldown_min`: Minimum minutes between repeated alerts for the same rule
- `enabled`: Toggle to activate/deactivate the rule

### Behavior

- On each sensor reading cycle (configured by sensor's `interval_s`), the alert engine evaluates all rules against current readings
- If a rule's expression evaluates to true, a Telegram message is sent to all authorized users
- Cooldown is enforced per-rule: duplicate alerts within `cooldown_min` are suppressed
- Startup notification "🟢 PiTunnel online" is sent once on bot start
- Cooldown timestamps are stored in SQLite `alert_history` table and persist across restarts

### Commands

- `/alerts` – Show all rules with current status (OK / FIRING / COOLDOWN)

### Monitoring Tips

- Check `/alerts` regularly to verify cooldown is working and no rules are stuck in COOLDOWN unexpectedly
- Adjust `cooldown_min` based on sensor frequency: for 60s interval sensors, 30 min cooldown prevents ~30 messages per alert event
- Disable rules temporarily by setting `enabled: false` without removing configuration

## Storage & Persistence

PiTunnel uses SQLite for persistent storage of command history, sensor readings, and alert events.

### Database Location

- Docker: `/app/data/db.sqlite3` (mounted from host `./data/`)
- Native: `db.sqlite3` in working directory

### Tables

- `command_history`: Timestamp, user ID, command alias, arguments, exit code, stdout, stderr
- `sensor_readings`: Timestamp, sensor ID, value, unit
- `alert_history`: Timestamp, rule ID, sensor ID, value that triggered the alert
- `schema_version`: Tracks database schema version for migrations

### Retention Policy

Configured via `config.yaml` under `limits.history_retention_days` (default: 30 days).

A daily APScheduler job runs at 03:00 local time to purge entries older than the retention period from all three history tables. The job also performs a WAL checkpoint (`TRUNCATE` mode) to control WAL file size.

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