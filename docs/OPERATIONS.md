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