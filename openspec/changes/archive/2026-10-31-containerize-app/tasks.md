# Tasks

## 1. Docker scaffolding

- [x] 1.1 Create `.dockerignore` excluding `config/*.env`, `.venv`, `tests`, `.git`, `__pycache__` and verify `docker build` context size is reduced
- [x] 1.2 Create `Dockerfile` using `python:3.11-slim-bookworm` base, copy source, install dependencies, create non-root user, set `WORKDIR /app`, entrypoint `python -m pitunnel.main` and verify Dockerfile syntax with `hadolint` or `docker build --dry-run` check
- [x] 1.3 Create `docker-compose.yml` defining service `pitunnel`, volume mounts `./config:/app/config:ro`, environment loading, restart policy `unless-stopped`, and verify `docker compose config` parses without errors

## 2. Build and runtime verification

- [x] 2.1 Build image for linux/arm64 and linux/amd64 using Buildx and verify `docker images` shows `pitunnel:latest`
- [x] 2.2 Run container with mounted config and verify bot starts, loads Config, and logs indicate Telegram connection attempt
- [x] 2.3 Verify secrets are not baked into image by inspecting layers with `docker history` and confirming `pitunnel.env` content is absent
- [x] 2.4 Verify configuration override works by changing `config.yaml` on host, restarting compose, and observing bot reloads new settings

## 3. Documentation

- [x] 3.1 Update README.md with Docker build/run instructions, volume mount requirements, and note on GPIO privileged mode
- [x] 3.2 Add `CONTAINER.md` or section in docs describing multi-arch build, compose override for device access, and rollback to venv

## Workflow follow-up

- Archive the change after review and validation passes.
- Verify archived specs contain the new `deployment/docker` capability.
