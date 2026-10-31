# Design

## Context

PiTunnel has been containerized with a Dockerfile and docker-compose.yml. Since then, system monitoring and alerts engine features were added. The alerts engine uses SQLite for alert cooldown persistence (file `db.sqlite3` in working directory). The current container configuration does not persist this database across restarts.

## Goals / Non-Goals

**Goals:**
- Add volume mount for SQLite database persistence (`./data:/app/data`)
- Create `/app/data` directory in Dockerfile with correct permissions for non-root user
- Update docker-compose.yml with the new volume
- Update documentation (README.md, CONTAINER.md)

**Non-Goals:**
- Changing base image or Python version
- Adding new Python dependencies
- Modifying application code
- Database migration tooling (schema is simple and created on first run)

## Decisions

**Database location:** Use `/app/data/db.sqlite3` inside container, mounted from `./data` on host. Rationale: keeps database separate from config, follows pattern of mounting host directories for persistence.

**Volume in docker-compose.yml:** Add `- ./data:/app/data` volume. Rationale: simple, explicit, matches existing config volume pattern.

**Dockerfile change:** Add `RUN mkdir -p /app/data && chown -R appuser:appuser /app/data` before switching to appuser. Rationale: ensures directory exists with correct ownership before user switch.

**Directory creation timing:** Create directory as root, then chown, then USER appuser. Alternative (create in entrypoint) rejected due to complexity and potential permission issues.

## Risks / Trade-offs

**Host directory permission** → User must create `./data` on host or container will create it as root. Mitigation: document in README; container will create if missing but owned by root.

**SQLite concurrency** → Multiple container instances could corrupt database. Mitigation: single instance deployment per host (current model); document limitation.

**Database schema changes** → Future schema changes may need migration. Mitigation: current schema is simple (single table); if needed, add migration logic in AlertEngine.

## Migration Plan

1. Update Dockerfile to create `/app/data` directory
2. Update docker-compose.yml with data volume
3. Build new image: `docker buildx build --platform linux/amd64,linux/arm64 -t pitunnel:latest .`
4. Create host `./data` directory: `mkdir -p data`
5. Deploy with compose: `docker compose up -d`
6. Verify `/alerts` works and cooldown persists after restart

## Open Questions

- Should the database path be configurable via environment variable? Deferrable; current hardcoded path works for single-host deployment.