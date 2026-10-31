# Proposal

## Why

Since the initial containerization, PiTunnel has added system monitoring (`/status` command) and an alerts engine (`/alerts` command with proactive notifications). The Docker configuration needs updates to support SQLite database persistence for alert cooldown tracking and to ensure all new features work correctly in the containerized environment.

## What Changes

- Update `docker-compose.yml` to add a volume mount for SQLite database (`./data:/app/data`) so alert cooldown state persists across container restarts
- Update `Dockerfile` to create the data directory with correct permissions
- Update documentation in `README.md` and `CONTAINER.md` to reflect the new volume requirement

## Capabilities

### New Capabilities

- *None*

### Modified Capabilities

- `deployment/docker`: Add SQLite database volume mount for alert cooldown persistence; ensure data directory exists with correct permissions

## Impact

- Affected files: `Dockerfile`, `docker-compose.yml`, `README.md`, `CONTAINER.md`
- No new Python dependencies required (system monitoring and alerts use existing deps: `psutil`, `apscheduler`, `pyyaml`)
- Systems: Requires host directory `./data` for SQLite persistence; backward compatible with existing deployments (database will be created on first run)