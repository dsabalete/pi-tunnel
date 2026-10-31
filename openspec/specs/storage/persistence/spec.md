# storage/persistence Specification

## Purpose

Provide durable SQLite storage with schema migrations for command history, sensor readings, and alert history; expose query APIs for history commands and analytics.

## Requirements

### Requirement: Database connection with WAL mode
The system SHALL provide a SQLite connection using WAL journal mode for concurrent read/write access, with automatic schema version tracking.

#### Scenario: Connection opens with WAL
- **WHEN** the storage module initializes
- **THEN** the SQLite connection uses WAL mode and has a `schema_version` table

#### Scenario: Schema version recorded
- **WHEN** migrations run
- **THEN** `schema_version` table reflects the latest applied migration number

#### Scenario: WAL checkpoint on purge
- **WHEN** `purge_older_than()` completes
- **THEN** WAL checkpoint (TRUNCATE mode) is attempted to control file size

### Requirement: Command history persistence
The system SHALL store every executed command with timestamp, user ID, alias, arguments, exit code, stdout, and stderr.

#### Scenario: Command logged on execution
- **WHEN** a command runs via the executor
- **THEN** a row is inserted into `command_history` with all fields populated

#### Scenario: History query returns recent commands
- **WHEN** `/history N` is invoked
- **THEN** the system returns the last N commands ordered by timestamp descending

#### Scenario: Handler integrates with history API
- **WHEN** `/history [n]` command is received
- **THEN** handler calls `History.get_history(limit=n)` and formats response as Markdown

### Requirement: Sensor readings persistence
The system SHALL store sensor readings with timestamp, sensor ID, value, and unit.

#### Scenario: Reading stored on sensor poll
- **WHEN** a sensor driver produces a reading
- **THEN** a row is inserted into `sensor_readings` with sensor_id, value, unit, and timestamp

#### Scenario: Readings queryable by sensor and time range
- **WHEN** querying readings for a sensor ID within a time window
- **THEN** the system returns matching rows ordered by timestamp

### Requirement: Alert history persistence
The system SHALL store alert events with timestamp, rule ID, sensor ID, and the reading value that triggered the alert.

#### Scenario: Alert event stored on trigger
- **WHEN** an alert rule evaluates to true and is not suppressed by cooldown
- **THEN** a row is inserted into `alert_history` with rule_id, sensor_id, value, and timestamp

#### Scenario: Cooldown lookup uses alert history
- **WHEN** the alert engine checks cooldown for a rule
- **THEN** it queries the latest `last_alert_ts` from `alert_history` for that rule_id

### Requirement: Configurable retention purge
The system SHALL provide a purge function that deletes rows older than a configurable number of days (default 30) from all history tables.

#### Scenario: Daily purge job runs
- **WHEN** the APScheduler daily job executes
- **THEN** `purge_older_than(30)` removes rows older than 30 days from all three history tables

#### Scenario: Purge respects per-table retention
- **WHEN** different retention periods are configured per table
- **THEN** each table is purged according to its own retention setting

### Requirement: History command handler integration

The system SHALL provide a `/history [n]` command handler that calls `History.get_history()` and formats the response for Telegram.

#### Scenario: Handler returns formatted history
- **WHEN** authorized user sends `/history 5`
- **THEN** handler calls `History.get_history(limit=5)` and formats entries with timestamp, user_id, alias, and exit_code

#### Scenario: Handler handles empty history
- **WHEN** authorized user sends `/history` with no entries in database
- **THEN** handler returns "No history available" message

### Requirement: Alert command handler integration with storage

The system SHALL provide an `/alerts` command handler that queries alert rules and their cooldown status from `alert_history`.

#### Scenario: Handler lists rule statuses
- **WHEN** authorized user sends `/alerts`
- **THEN** handler loads rules from config, queries `alert_history` for last alert timestamps, determines status (OK/COOLDOWN), and formats as Markdown table
