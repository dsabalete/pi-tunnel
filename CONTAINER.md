# Container Deployment for PiTunnel

## Overview

PiTunnel can be run as a Docker container. The image is built from `Dockerfile` and orchestrated with `docker-compose.yml`.

## Building

Multi-arch build:

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t pitunnel:latest --load .
```

The Dockerfile uses `python:3.11-slim-bookworm`, installs dependencies from `requirements.txt`, copies `src/`, sets `PYTHONPATH=/app/src`, and runs as non-root user `appuser`.

## Running

Create data directory for SQLite persistence:
```bash
mkdir -p data
```

```bash
docker compose up -d
```

Volumes mounted:

- `./config:/app/config:ro` — bot configuration (read-only)
- `./data:/app/data` — SQLite database for command history persistence
- Environment from `./config/pitunnel.env` via `env_file`

Do not bake secrets into the image. `.dockerignore` excludes `config/*.env`.

## Rollback

Stop compose and revert to venv:

```bash
docker compose down
python -m pitunnel.main
```

## Database Persistence

The `./data:/app/data` volume mount provides persistent storage for the SQLite database (`db.sqlite3`). This database stores:

- Command history

The database is created automatically on first run. History persists across container restarts.

## Notes

- Config changes on host are reflected on container restart due to volume mount.
- Image size ~195 MB.
- Secrets must stay in mounted `pitunnel.env`, never committed.