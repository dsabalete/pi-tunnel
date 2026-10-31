# Design

## Context

PiTunnel has bot core, command registry, and auth in place. `src/pitunnel/system/` exists but contains only `__init__.py`. No system metrics collection exists today. `psutil` is already a dependency. Public IP requires external HTTP call to `https://api.ipify.org`.

## Goals / Non-Goals

**Goals:**

- Provide `/status` command returning CPU, RAM, temp, disk, ssd disk, uptime, local IP, public IP
- Cache public IP for 10 minutes in memory to limit external calls
- Use `psutil` for CPU/RAM/disk/ssd disk/uptime and `/sys/class/thermal` for CPU temp on Pi
- Keep implementation within `src/pitunnel/system/status.py` and handler integration

**Non-Goals:**

- Persistent storage for metrics history
- Graphing or Prometheus export
- Sensor integration beyond system metrics
- Changing authentication or logging mechanisms

## Decisions

**Metric collection:** Use `psutil.cpu_percent(interval=0.5)`, `psutil.virtual_memory()`, `psutil.disk_usage('/')`, `psutil.disk_usage('/mnt/nas')`, `psutil.boot_time()`. CPU temperature read from `/sys/class/thermal/thermal_zone0/temp` with fallback to `psutil.sensors_temperatures()`. Rationale: `psutil` already present, minimal dependencies.

**Local IP:** Determine primary interface via `psutil.net_if_addrs()` filtering for `AF_INET` and non-loopback. Alternative `socket.gethostbyname` rejected due to DNS dependency.

**Public IP:** HTTP GET to `https://api.ipify.org?format=text` with 3s timeout using `urllib.request`. Alternative `aiohttp` rejected to avoid async dependency for simple call. Cache in module-level dict with timestamp.

**Cache:** In-memory TTL cache keyed by service, 600s TTL. Simpler than Redis/SQLite for this scope. Trade-off: cache lost on restart, acceptable.

**Command integration:** Add handler in `commands/handlers.py` for `/status` that calls `get_system_status()` and formats Markdown. Reuse existing i18n `t()` for labels.

## Risks / Trade-offs

**External IP failure** → Timeout or network down. Mitigation: 3s timeout, fallback to `unknown`, log warning.

**Thermal path varies** → Some Pi models use different thermal zone. Mitigation: try multiple zones, fallback to `N/A`.

**psutil overhead** → CPU percent with interval adds latency. Mitigation: use short interval and async-safe call in handler.

## Migration Plan

- Deploy code, `/status` becomes available to authorized users immediately
- No config changes required
- Rollback: remove handler registration, revert code

## Open Questions

- Should local IP prefer specific interface name (`eth0`/`wlan0`)? Deferrable; current heuristic works for most setups.
