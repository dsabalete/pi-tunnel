# Tasks

## 1. Dockerfile updates

- [x] 1.1 Update `Dockerfile` to create `/app/data` directory with correct ownership for non-root user, verify `docker build` succeeds and `docker run --rm pitunnel:latest ls -la /app/data` shows correct permissions
- [x] 1.2 Verify `Dockerfile` syntax with `hadolint` or `docker build --dry-run` check

## 2. docker-compose.yml updates

- [x] 2.1 Add volume mount `./data:/app/data` to `docker-compose.yml` for SQLite database persistence, verify `docker compose config` parses without errors
- [x] 2.2 Verify service starts with new volume and creates database file in host `./data/db.sqlite3`

## 3. Documentation updates

- [x] 3.1 Update `README.md` Docker section to document the new `./data` volume requirement and creation step
- [x] 3.2 Update `CONTAINER.md` with database persistence notes and volume mount details

## 4. Verification

- [x] 4.1 Build image with `docker buildx build --platform linux/amd64 -t pitunnel:latest --load .` and verify success
- [x] 4.2 Run container with compose, verify bot starts, `/status` and `/alerts` commands work, and `./data/db.sqlite3` is created
- [x] 4.3 Restart container and verify alert cooldown state persists (trigger alert, wait, restart, verify suppressed)

## Workflow follow-up

- Archive the change after review and validation passes
- Verify archived spec `deployment/docker` is updated in main specs