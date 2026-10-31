# deployment/docker Specification

## Purpose

Package PiTunnel as a reproducible container image and provide a compose-based runtime that maps configuration and secrets from the host, enabling portable deployment on Raspberry Pi and development machines.

## Requirements

### Requirement: Container image builds
The system SHALL provide a Dockerfile that builds a runnable PiTunnel image from a Python 3.11 base, installs project dependencies from pyproject.txt/requirements, copies source code, and sets an entrypoint that starts the bot.

#### Scenario: Build succeeds on arm64 and amd64
- **WHEN** `docker build` is executed with appropriate build platform
- **THEN** image builds without errors and `docker run --rm <image> --help` or entrypoint starts

### Requirement: Container runs application
The system SHALL start PiTunnel via `python -m pitunnel.main` as container entrypoint, reading configuration from mounted paths and persisting SQLite database for alert cooldown state.

#### Scenario: Bot starts with mounted config
- **WHEN** container starts with `config/config.yaml` and `config/pitunnel.env` mounted and environment loaded
- **THEN** bot initializes Config, connects to Telegram, and begins processing updates

#### Scenario: Bot starts with mounted config and database
- **WHEN** container starts with `config/config.yaml`, `config/pitunnel.env` mounted and `data/` directory mounted for database
- **THEN** bot initializes Config, connects to Telegram, begins processing updates, and creates SQLite database in `/app/data/db.sqlite3`

#### Scenario: Alert cooldown persists across restart
- **WHEN** container restarts after triggering an alert with cooldown
- **THEN** alert cooldown state is preserved and duplicate alerts remain suppressed per rule's `cooldown_min`

### Requirement: Configuration via volumes
The system SHALL allow configuration to be supplied via host volume mounts for `config/config.yaml`, `config/pitunnel.env`, and database persistence via `data/` directory without baking secrets or state into image.

#### Scenario: Config override
- **WHEN** user mounts a host config directory into `/app/config`
- **THEN** container uses host files for configuration and changes are reflected on restart without rebuild

#### Scenario: Database directory override
- **WHEN** user mounts a host data directory into `/app/data`
- **THEN** container uses host directory for SQLite database and state persists across container restarts

### Requirement: Secrets via environment
The system SHALL support Telegram token and other secrets via environment variables loaded from `pitunnel.env` mounted or via Docker secrets, never committed.

#### Scenario: Secret not in image
- **WHEN** image layers are inspected
- **THEN** no secret values are present in layers and bot reads token at runtime from environment

### Requirement: Reproducible dependencies
The system SHALL pin dependencies via requirements derived from pyproject.toml and install them in image build.

#### Scenario: Dependency isolation
- **WHEN** container runs on a clean host without Python packages installed
- **THEN** bot starts successfully with all dependencies satisfied inside container

### Requirement: Data directory initialization
The system SHALL create the `/app/data` directory with correct permissions for the non-root appuser during image build.

#### Scenario: Data directory exists and writable
- **WHEN** container starts as non-root user
- **THEN** `/app/data` directory exists and is writable by appuser for SQLite database creation