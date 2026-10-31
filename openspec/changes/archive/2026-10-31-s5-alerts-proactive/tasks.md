# Tasks

## 1. Alert Engine Implementation

- [x] 1.1 Complete `alerts/engine.py` with `evaluate_rules()` method
- [x] 1.2 Implement `_eval_expression()` for parsing rule expressions (`> 27.5`, `< 10`, `== 1`)
- [x] 1.3 Implement `_check_cooldown()` using `History.get_last_alert_ts()`
- [x] 1.4 Implement `record_startup_notification()` and `should_send_startup()`
- [x] 1.5 Add unit tests for all `AlertEngine` methods

## 2. Alert Command Handler

- [x] 2.1 Add `/alerts` command handler in `commands/handlers.py`
- [x] 2.2 Implement rule status display (OK/FIRING/COOLDOWN)
- [x] 2.3 Query alert history from SQLite for cooldown status
- [x] 2.4 Add unit tests for `/alerts` command handler

## 3. Startup Notification

- [x] 3.1 Integrate startup notification call in bot initialization
- [x] 3.2 Track `_startup_notification_sent` flag in `AlertEngine`
- [x] 3.3 Test startup notification sent once on bot start

## 3. Alert History Integration

- [x] 4.1 Ensure `History.log_alert()` works with cooldown tracking
- [x] 4.2 Verify `History.get_last_alert_ts()` returns correct timestamps
- [x] 4.3 Test cooldown enforcement with multiple rule triggers

## 4. Run Test Suite

- [x] 5.1 Run `pytest` and verify all new tests pass
- [x] 5.2 Run `pytest --cov=pitunnel --cov-fail-under=85` to ensure coverage threshold met
- [x] 5.3 Run `ruff check .` and `mypy src/` to ensure code quality

## Workflow follow-up

- Archive the change after implementation verification and test coverage are complete