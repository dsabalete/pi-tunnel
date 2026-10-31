# Proposal

## Why

PiTunnel is currently deployed manually via a virtual environment and systemd on Raspberry Pi devices. This makes environments hard to reproduce, updates risky, and onboarding new hardware error-prone. Containerizing the application will provide reproducible builds, isolated dependencies, and a simple portable deployment model for Pi and testing environments.

## What Changes

- Add a production-ready Dockerfile for the PiTunnel Python application targeting `linux/arm64` / `linux/amd64` with Python 3.11 slim base.
- Add `docker-compose.yml` for local development and for Raspberry Pi deployment with volume mounts for `config/config.yaml` and `config/pitunnel.env`.
- Add `.dockerignore` to keep build context small and avoid shipping secrets, caches, and virtual environments.
- Update documentation to describe container build, run, and configuration override via mounted volumes and environment variables.
- No functional changes to the bot's behavior; existing command surface, sensor/actuator integrations, and configuration format remain unchanged.

## Capabilities

### New Capabilities

- `deployment/docker`: Defines how PiTunnel is packaged and run as a container image, including build requirements, runtime configuration via mounted config/env, entrypoint, and non-root user execution where possible.

### Modified Capabilities

- *None. No existing spec-level behavior changes.*

## Impact

- Affected code: packaging metadata only; no changes to `src/pitunnel/**`.
- Dependencies: Docker runtime required on target hosts; Python dependencies remain the same and are installed via pip inside image.
- Systems: Replaces manual venv + systemd setup with container-based deployment; systemd service files remain for users who prefer them, but container is now primary recommended deployment.
