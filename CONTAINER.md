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

```bash
docker compose up -d
```

Config is mounted read-only:

- `./config:/app/config:ro`
- Environment from `./config/pitunnel.env` via `env_file`

Do not bake secrets into the image. `.dockerignore` excludes `config/*.env`.

## Hardware Access

GPIO / I2C requires host device access. Add an override:

`docker-compose.override.yml`:
```yaml
services:
  pitunnel:
    privileged: true
    devices:
      - /dev/gpiomem:/dev/gpiomem
      - /dev/i2c-1:/dev/i2c-1
```

## Rollback

Stop compose and revert to venv:

```bash
docker compose down
python -m pitunnel.main
```

## Notes

- Config changes on host are reflected on container restart due to volume mount.
- Image size ~195 MB.
- Secrets must stay in mounted `pitunnel.env`, never committed.
