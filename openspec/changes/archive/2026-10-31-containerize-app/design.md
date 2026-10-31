# Design

## Context

PiTunnel runs as a Python package under a venv, configured via `config/config.yaml` and `config/pitunnel.env`, and is currently launched manually or via systemd. Source lives in `src/pitunnel`, dependencies are declared in `pyproject.toml` and `requirements.txt`. The bot requires access to GPIO/SMBus for sensors/actuators on Raspberry Pi and network access to Telegram API. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Provide a reproducible Docker image that encapsulates Python runtime and dependencies.
- Enable deployment via `docker compose up` with host-mounted config and env files.
- Keep configuration external to image; no secrets baked in.
- Support both arm64 Raspberry Pi and amd64 development machines via multi-platform builds.
- Preserve existing entrypoint `python -m pitunnel.main` and behavior.

**Non-Goals:**
- Running production with Kubernetes or orchestration.
- Modifying application code, command handling, or sensor logic.
- Providing a web UI for container management.
- Automatic GPIO device passthrough configuration; document privileged mode requirement for hardware access.

## Decisions

**Base image:** `python:3.11-slim-bookworm`
- Rationale: Matches requires-python >=3.11, small size, Debian base compatible with `gpiozero`/`smbus2` wheels. Alternative `alpine` rejected due to musl compatibility concerns for GPIO libraries.

**Build context:** Copy `src/`, `pyproject.toml`, `requirements.txt`, install via `pip install -e .` or `pip install -r requirements.txt`. 
- Rationale: Reuses existing packaging metadata. Alternative `poetry` not used in project.

**Configuration mounting:** Volume mount `./config:/app/config:ro` and load env via `dotenv` at runtime.
- Rationale: Aligns with existing `Config.load()` and `load_env()`. Keeps secrets out of image.

**User:** Run as non-root user `appuser` inside container where possible; allow `--privileged` or `--device` flags for GPIO when needed.
- Rationale: Security best practice. Trade-off: GPIO access may require privileged mode on Pi.

**Compose file:** `docker-compose.yml` with service `pitunnel`, restart policy `unless-stopped`, environment `PYTHONUNBUFFERED=1`.
- Alternatives considered: Podman-compose, systemd-nspawn. Compose chosen for simplicity and dev familiarity.

**Multi-arch:** Use Docker Buildx with platforms `linux/arm64,linux/amd64`. Document `docker buildx build --platform linux/arm64`.
- Rationale: Developers on amd64 can build amd64, Pi builds arm64.

## Risks / Trade-offs

**Hardware access** → GPIO/SMBus may require `--privileged` or `--device /dev/gpiomem` and host `/dev/i2c*` mounts. Mitigation: document required flags and provide example compose override.

**Secrets leakage** → Accidentally copying `.env` into image. Mitigation: `.dockerignore` excludes `config/*.env`, `.venv`, tests, and uses build args only for build-time metadata.

**Size vs slim** → `python-slim` still pulls many system deps for `gpiozero`. Trade-off accepted for compatibility.

**Configuration drift** → Users may edit config inside container. Mitigation: mount config read-only, document host path.

## Migration Plan

1. Build image locally: `docker build -t pitunnel:latest .`
2. Start with compose: `docker compose up -d`
3. Verify bot connects to Telegram and responds.
4. Optional: replace systemd service with `docker compose` managed service.
5. Rollback: stop compose and revert to venv entrypoint.

## Open Questions

- Should we publish image to a registry or keep local builds only? Deferrable; design supports both.
- Exact device mounts needed for specific sensors; defer to per-deployment override.
