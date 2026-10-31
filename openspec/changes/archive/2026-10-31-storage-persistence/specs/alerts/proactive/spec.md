# Spec Delta

## MODIFIED Requirements

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
- **THEN** it queries the latest `last_sent_ts` from `alert_history` for that rule_id