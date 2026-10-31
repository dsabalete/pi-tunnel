# Spec Delta

## MODIFIED Requirements

### Requirement: Container runs application
The system SHALL start PiTunnel via `python -m pitunnel.main` as container entrypoint, reading configuration from mounted paths and persisting SQLite database for alert cooldown state.

#### Scenario: Bot starts with mounted config and database
- **WHEN** container starts with `config/config.yaml`, `config/pitunnel.env` mounted and `data/` directory mounted for database
- **THEN** bot initializes Config, connects to Telegram, begins processing updates, and creates SQLite database in `/app/data/db.sqlite3`

#### Scenario: Alert cooldown persists across restart
- **WHEN** container restarts after triggering an alert with cooldown
- **THEN** alert cooldown state is preserved and duplicate alerts remain suppressed per rule's `cooldown_min`

### Requirement: Configuration via volumes
The system SHALL allow configuration to be supplied via host volume mounts for `config/config.yaml`, `config/pitunnel.env`, and database persistence via `data/` directory without baking secrets or state into image.

#### Scenario: Database directory override
- **WHEN** user mounts a host data directory into `/app/data`
- **THEN** container uses host directory for SQLite database and state persists across container restarts

## ADDED Requirements

### Requirement: Data directory initialization
The system SHALL create the `/app/data` directory with correct permissions for the non-root appuser during image build.

#### Scenario: Data directory exists and writable
- **WHEN** container starts as non-root user
- **THEN** `/app/data` directory exists and is writable by appuser for SQLite database creation