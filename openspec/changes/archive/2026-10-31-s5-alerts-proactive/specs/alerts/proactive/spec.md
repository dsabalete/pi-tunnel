# Spec Delta

## Purpose

Provides alert rule evaluation against sensor readings, cooldown enforcement using SQLite storage, startup notification on bot init, and `/alerts` command interface for viewing rule status.

## ADDED Requirements

### Requirement: Alert rule evaluation
The system SHALL evaluate sensor readings against rules defined in the configuration file using expressions (e.g., `> 27.5`, `< 10`, `== 1`).

#### Scenario: Rule condition met
- **WHEN** a sensor reading exceeds or matches the rule threshold
- **THEN** an alert is triggered and dispatched to all authorized users

#### Scenario: Rule condition not met
- **WHEN** a sensor reading is within normal threshold
- **THEN** no alert is dispatched

### Requirement: Cooldown enforcement
The system SHALL suppress duplicate alerts for a rule if an alert was already sent within the rule's configured `cooldown_min` period, using the unified `alert_history` table for timestamp persistence.

#### Scenario: Second alert within cooldown
- **WHEN** a rule triggers again before `cooldown_min` has elapsed since the last alert
- **THEN** the system logs the condition but suppresses sending a new Telegram message

#### Scenario: Alert after cooldown expires
- **WHEN** a rule triggers after `cooldown_min` has elapsed since the last alert
- **THEN** the system dispatches a new Telegram message and updates the last alert timestamp in `alert_history`

#### Scenario: Cooldown persists across restarts
- **WHEN** the bot restarts and a rule has a recent alert in `alert_history`
- **THEN** the cooldown state is preserved and duplicate alerts remain suppressed

### Requirement: Alert history persistence
The system SHALL store alert events with timestamp, rule ID, sensor ID, and the reading value that triggered the alert in the unified `alert_history` table.

#### Scenario: Alert event stored on trigger
- **WHEN** an alert rule evaluates to true and is not suppressed by cooldown
- **THEN** a row is inserted into `alert_history` with rule_id, sensor_id, value, and timestamp

#### Scenario: Cooldown lookup uses unified alert history
- **WHEN** the alert engine checks cooldown for a rule
- **THEN** it queries the latest `last_alert_ts` from `alert_history` for that rule_id

### Requirement: Startup notification
The system SHALL dispatch a proactive notification ("🟢 PiTunnel online") to all authorized users when the bot service starts.

#### Scenario: Bot startup
- **WHEN** the PiTunnel bot finishes initializing
- **THEN** a startup message is sent to all authorized users

### Requirement: Alerts status command
The system SHALL support an `/alerts` command that lists all configured alert rules, their associated sensors, threshold conditions, cooldown settings, and current status (OK / FIRING / COOLDOWN).

#### Scenario: List active alerts
- **WHEN** an authorized user sends `/alerts`
- **THEN** the bot responds with a tabular or formatted Markdown list showing the status of each rule