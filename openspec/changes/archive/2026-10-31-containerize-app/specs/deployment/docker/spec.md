# Spec Delta

## Purpose

Package PiTunnel as a reproducible container image and provide a compose-based runtime that maps configuration and secrets from the host, enabling portable deployment on Raspberry Pi and development machines.

## ADDED Requirements

### Requirement: Container image builds
The system SHALL provide a Dockerfile that builds a runnable PiTunnel image from a Python 3.11 base, installs project dependencies from pyproject.txt/requirements, copies source code, and sets an entrypoint that starts the bot.

#### Scenario: Build succeeds on arm64 and amd64
- **WHEN** `docker build` is executed with appropriate build platform
- **THEN** image builds without errors and `docker run --rm <image> --help` or entrypoint starts

### Requirement: Container runs application
The system SHALL start PiTunnel via `python -m pitunnel.main` as container entrypoint, reading configuration from mounted paths.

#### Scenario: Bot starts with mounted config
- **WHEN** container starts with `config/config.yaml` and `config/pitunnel.env` mounted and environment loaded
- **THEN** bot initializes Config, connects to Telegram, and begins processing updates

### Requirement: Configuration via volumes
The system SHALL allow configuration to be supplied via host volume mounts for `config/config.yaml` and `config/pitunnel.env` without baking secrets into image.

#### Scenario: Config override
- **WHEN** user mounts a host config directory into `/app/config`
- **THEN** container uses host files for configuration and changes are reflected on restart without rebuild

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
