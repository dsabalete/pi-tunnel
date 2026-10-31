# Proposal

## Why

PiTunnel currently has no way to report host health to authorized users. Operators need quick visibility into CPU, RAM, temperature, disk, ssd disk, uptime and network identity without SSH access. Implementing `/status` monitoring aligns with Sprint 2 goals in Todo.md and enables proactive triage.

## What Changes

- Add `/status` command handler that returns formatted Markdown with system metrics
- Implement `system/status.py` providing `get_system_status()` returning CPU%, RAM%, CPU temp, disk `/`, disk `/mnt/nas`, uptime, local IP, public IP
- Add public IP cache with 10-minute TTL to avoid spamming external service
- No breaking changes to existing commands or configuration schema

## Capabilities

### New Capabilities

- `system/status`: Provides on-demand system health snapshot via Telegram, including CPU, memory, temperature, disk, ssd disk, uptime, local and public IP with caching

### Modified Capabilities

- _None_

## Impact

- Affected code: new `src/pitunnel/system/status.py`, new command handler integration in `commands/handlers.py` for `/status`
- Dependencies: `psutil` already in requirements; HTTP client for `https://api.ipify.org` (stdlib `urllib`/`aiohttp` acceptable)
- Systems: Adds external network call for public IP, mitigated by cache; requires no config changes
