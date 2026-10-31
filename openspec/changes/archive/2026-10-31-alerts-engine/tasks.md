# Tasks

## 1. Alerts engine module

- [x] 1.1 Create `src/pitunnel/alerts/engine.py` with `AlertEngine` class and `evaluate_rules(readings) -> list[dict]` stub returning triggered rules, verify import succeeds
- [x] 1.2 Implement rule expression evaluation using bounded namespace `eval()` of `when` field with reading value accessible as `value`, verify correct behavior for `>`, `<`, `==` operators
- [x] 1.3 Implement cooldown enforcement: check SQLite `alert_history` for `last_sent_ts` per rule, suppress if within `cooldown_min`, verify returns suppressed flag
- [x] 1.4 Implement startup notification dispatch: send "🟢 PiTunnel online" to all authorized users on bot init, verify no duplicate send if called twice

## 2. Rule configuration

- [x] 2.1 Add `alerts.rules` to `config.yaml.example` with sample entries: sensor_id `temp-salon`, `when: "> 27.5"`, `cooldown_min: 30`, `enabled: true`, verify YAML parses
- [x] 2.2 Add `alerts` table schema to SQLite (`alert_history`) with columns `rule_id`, `sensor_id`, `last_sent_ts`, verify migrations work

## 3. Command integration

- [x] 3.1 Add `/alerts` handler in `commands/handlers.py` listing all rules with sensor id, threshold, cooldown, and status (OK/FIRING/COOLDOWN), verify handler is registered
- [x] 3.2 Integrate `AlertEngine.evaluate_rules()` into scheduler job that runs every 30s, verify readings are fetched and rules evaluated
- [x] 3.3 Add i18n strings for alert labels in ES/EN (`status_title`, `alert_rule`, `alert_status_ok`, `alert_status_firing`, `alert_status_cooldown`), verify `/alerts` output uses configured language

## 4. Documentation

- [x] 4.1 Add `/alerts` usage example to `README.md`, verify documentation renders correctly
- [x] 4.2 Add alert rule configuration notes to `docs/OPERATIONS.md`, verify note is present and accurate

## Workflow follow-up

- Archive the change after review and validation passes
- Verify archived spec `alerts/proactive` is present in main specs