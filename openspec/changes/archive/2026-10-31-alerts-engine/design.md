# Design

## Context

PiTunnel has sensor drivers that produce readings stored in SQLite, a command system with whitelist validation, and `/status` already implemented. No alerting engine exists. Rules in `config.yaml` use simple expressions like `> 27.5`.

## Goals / Non-Goals

**Goals:**
- Implement `alerts/engine.py` that evaluates rules against sensor readings from SQLite
- Provide per-rule cooldown enforcement (`cooldown_min`)
- Dispatch proactive Telegram messages on alert triggers and bot startup
- Add `/alerts` command listing rule status
- Reuse existing storage layer and APScheduler for periodic checks

**Non-Goals:**
- Persistent alert history beyond SQLite
- Grafana or external monitoring integration
- Rich UI for rule management; `/alerts` output only
- Sensor driver changes beyond read interface

## Decisions

**Rule storage:** Alert definitions live in `config.yaml` under `alerts.rules` as list of dicts with keys: `id`, `sensor_id`, `when` (expression), `cooldown_min`, `enabled`. Rationale: avoids new schema, leverages existing config infrastructure.

**Expression evaluator:** Simple `eval()` of `when` expression with bounded variable namespace: `value = reading.value`. No arbitrary Python exec. Rationale: safe for this scope; avoids dependency on `sympy` or custom parser.

**Cooldown enforcement:** APScheduler job checks all rules on every run. Timestamp stored in SQLite `alert_history` row with `last_sent_ts`. Rationale: reuse existing DB, no extra tables needed.

**Startup notification:** On `on_startup` (T603 from Todo.md §7), send a single one-time message via `bot.send_message`. Rationale: aligns with existing alert engine startup flow.

**Telegram dispatch:** Single message per trigger per rule, no markdown formatting beyond labels, to avoid rate limiting. Rationale: simplicity and reliability.

## Risks / Trade-offs

**Expression safety** → `eval()` on bounded namespace. Mitigation: only expose `value` variable, validate expression chars, reject anything with `__`.

**Cooldown drift** → On bot restart, cooldown timestamps are lost. Mitigation: acceptable – alerts resume after first trigger.

**Sensor read frequency** → APScheduler interval too frequent may impact performance. Mitigation: use 30s interval per Todo.md §6, throttle per-rule.

## Migration Plan

1. Add `alerts` package with `engine.py` and rules definition in `config.yaml.example`
2. APScheduler job on bot start reads config, evaluates rules, dispatches alerts
3. Register `/alerts` handler in `commands/handlers.py`
4. Test with mocked sensor readings and verify Telegram messages and `/alerts` output
5. Rollback: remove scheduler job, delete config entries, revert code

## Open Questions

- Should cooldown timestamps survive bot restart? Deferrable; default: survive via SQLite, explicitly configurable.