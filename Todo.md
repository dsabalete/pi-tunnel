# PiTunnel — Implementation Task List

**Version:** 1.0  
**Date:** 2026-10-30  
**Status:** Backlog → Sprint planning

---

## 0️⃣ Infrastructure & Project Setup

| ID       | Task                                                                                                                                                                                        | Priority | Status | DoD                                     |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | --------------------------------------- |
| **T001** | Initialize Git repo + folder structure (`src/pitunnel/`, `tests/`, `config/`, `scripts/`, `systemd/`)                                                                                       | P0       | [x]    | `git init` + folders created            |
| **T002** | `pyproject.toml` / `requirements.txt` with deps: `python-telegram-bot>=21`, `gpiozero`, `smbus2`, `psutil`, `pyyaml`, `apscheduler`, `aiofiles`, `pytest`, `pytest-asyncio`, `ruff`, `mypy` | P0       | [x]    | `pip install -r requirements.txt` works |
| **T003** | Configure **ruff** (lint) + **mypy** (strict) + **pre-commit** hooks                                                                                                                        | P0       | [x]    | `ruff check .` and `mypy src/` pass     |
| **T004** | Create `config.yaml.example` and `pitunnel.env.example` documented                                                                                                                          | P0       | [x]    | Files in `config/` with comments        |
| **T005** | Write `Makefile` / `justfile` with targets: `install`, `dev`, `test`, `lint`, `build`, `deploy`                                                                                             | P1       | [x]    | `make test` runs full suite             |

---

## 1️⃣ Bot Core (Telegram + Authorization)

| ID       | Task                                                                                                                                                           | Priority | Status | DoD                                                     |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------- |
| **T101** | `core/bot.py`: `PiTunnelBot` class extending `Application` (PTB v21), long polling setup, signal handling (SIGTERM/SIGINT)                                     | P0       | []     | `python -m pitunnel.main` starts and shuts down cleanly |
| **T102** | `core/auth.py`: `AuthorizeMiddleware` filters `Update` by `authorized_users`; logs `WARNING` with `user_id` if unauthorized                                    | P0       | []     | Unauthorized user → no response, visible log            |
| **T103** | `core/i18n.py`: ES/EN string loader from YAML; helper `t(key, **kwargs)`                                                                                       | P1       | []     | `/help` shows texts in configured language              |
| **T104** | `core/errors.py`: Typed exceptions (`UnauthorizedError`, `WhitelistError`, `TimeoutError`, `SensorError`) + global handler mapping to user messages (§4 table) | P0       | []     | Controlled errors → friendly message + structured log   |
| **T105** | `core/logging.py`: JSON config (structlog or python-json-logger) with fields: `ts`, `level`, `user_id`, `command`, `duration_ms`, `exit_code`                  | P1       | []     | `journalctl -u pitunnel -o json` shows parseable logs   |

---

## 2️⃣ Command System (Whitelist + Safe Execution)

| ID       | Task                                                                                                                                                                                   | Priority | Status | DoD                                                                             |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------------------------------- |
| **T201** | `commands/registry.py`: Load `commands.aliases` from `config.yaml`; validate no duplicate keys                                                                                         | P0       | []     | Invalid alias → startup error                                                   |
| **T202** | `commands/executor.py`: `run_alias(alias: str) -> CommandResult` using `subprocess.run(args, timeout=10, capture_output=True, text=True, shell=False)`; truncate to `max_output_chars` | P0       | []     | `restart-mqtt` executes `systemctl restart mosquitto` and returns stdout/stderr |
| **T203** | `commands/confirm.py`: Inline confirmation flow for aliases marked `destructive: true`; callback data signed (HMAC) + 60s expiry                                                       | P1       | []     | `/cmd reboot` shows "✅ Confirm" / "❌ Cancel"; executes only after ✅          |
| **T204** | Command handlers: `/start`, `/help`, `/cmd <alias>`, `/history [n]` in `handlers/admin.py`                                                                                             | P0       | []     | All respond < 2s; `/help` lists dynamically per allowlist                       |

---

## 3️⃣ System Monitoring (`/status`)

| ID       | Task                                                                                                                                                                                                | Priority | Status | DoD                                                   |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ----------------------------------------------------- |
| **T301** | `system/status.py`: `get_system_status() -> SystemStatus` (dataclass) with: CPU %, RAM %, CPU temp, disk `/`, uptime, local IP (default iface), public IP (STUN `https://api.ipify.org` timeout 3s) | P0       | []     | `/status` returns formatted Markdown with all metrics |
| **T302** | Public IP cache (TTL 10 min) to avoid spamming external service                                                                                                                                     | P1       | []     | Second `/status` call makes no external HTTP request  |

---

## 4️⃣ Sensors (GPIO / I²C / 1-Wire)

| ID       | Task                                                                                                                                                              | Priority | Status | DoD                                                                             |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------------------------------- |
| **T401** | `sensors/base.py`: `Sensor` protocol (ABC) with `read() -> SensorReading`, `id`, `type`, `unit`                                                                   | P0       | []     | Clear interface for test doubles                                                |
| **T402** | Concrete drivers: `DHT22Sensor` (gpiozero), `DS18B20Sensor` (w1thermsensor), `BME280Sensor` (smbus2), `CPUTempSensor` (psutil)                                    | P0       | []     | Each driver tested with hardware mock                                           |
| **T403** | `sensors/registry.py`: Load `sensors` list from config; instantiate drivers; `APScheduler` thread for periodic polling (`interval_s`) and save readings to SQLite | P0       | []     | `/sensors` returns latest readings of all; `/sensors temp-salon` returns single |
| **T404** | Hardware error handling: disconnected sensor → `SensorError` + log + `null` value in response                                                                     | P1       | []     | Single sensor failure doesn't crash bot                                         |

---

## 5️⃣ Actuators (Relays / GPIO out)

| ID       | Task                                                                                         | Priority | Status | DoD                                                       |
| -------- | -------------------------------------------------------------------------------------------- | -------- | ------ | --------------------------------------------------------- |
| **T501** | `actuators/base.py`: `Actuator` protocol with `on()`, `off()`, `state() -> bool`             | P0       | []     | Uniform interface                                         |
| **T502** | `RelayActuator` (gpiozero `OutputDevice`) + `LEDActuator` (optional PWM)                     | P0       | []     | `/on luz-porche` turns on GPIO 17; `/off` turns off       |
| **T503** | Handler `/on <id>` `/off <id>` with existence validation and confirmation if `confirm: true` | P0       | []     | Response "✅ luz-porche encendido" or confirmation button |

---

## 6️⃣ Alerts & Proactive Notifications

| ID       | Task                                                                                                                     | Priority | Status | DoD                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------ | -------- | ------ | -------------------------------------------------- |
| **T601** | `alerts/engine.py`: Evaluate `alert.when` rules (simple expressions: `> 27.5`, `< 10`, `== 1`) after each sensor reading | P0       | []     | Temp > 27.5 → alert sent to all `authorized_users` |
| **T602** | Cooldown per rule (`cooldown_min`): store `last_alert_ts` in SQLite; no repeat until expiry                              | P0       | []     | Second high reading in 5 min → **no** alert sent   |
| **T603** | Service startup alert: on `on_startup` send "🟢 PiTunnel online" to allowlist                                            | P1       | []     | Pi reboot → Telegram message < 60s                 |
| **T604** | Command `/alerts` lists active rules + status (OK / FIRING / COOLDOWN)                                                   | P1       | []     | Tabular Markdown output                            |

---

## 7️⃣ Persistence (SQLite + History)

| ID       | Task                                                                                                                                                                          | Priority | Status | DoD                                                           |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------------- |
| **T701** | `storage/db.py`: SQLite WAL connection + simple migrations (`schema_version` table)                                                                                           | P0       | []     | `sqlite3 /var/lib/pitunnel/db.sqlite3 ".schema"` shows tables |
| **T702** | Tables: `command_history(ts, user_id, alias, args, exit_code, stdout, stderr)`, `sensor_readings(ts, sensor_id, value, unit)`, `alert_history(ts, rule_id, sensor_id, value)` | P0       | []     | Atomic inserts + indexes on `ts`                              |
| **T703** | `storage/history.py`: `log_command()`, `get_history(limit=10)`, `purge_older_than(days)` (daily job)                                                                          | P0       | []     | `/history 20` shows last 20 rows; 30-day retention default    |
| **T704** | Weekly auto-backup (`.dump` compressed to `/var/backups/pitunnel/`)                                                                                                           | P2       | []     | systemd timer configured                                      |

---

## 8️⃣ Camera (`/snapshot`)

| ID       | Task                                                                       | Priority | Status | DoD                                                      |
| -------- | -------------------------------------------------------------------------- | -------- | ------ | -------------------------------------------------------- |
| **T801** | `camera/capture.py`: `Camera` abstraction with `capture() -> bytes` (JPEG) | P2       | []     | Works with `libcamera-jpeg` (PiCam) and `fswebcam` (USB) |
| **T802** | Handler `/snapshot` → sends `send_photo` with caption `📷 {timestamp}`     | P2       | []     | Photo received in Telegram < 5s                          |

---

## 9️⃣ Deployment & Operations

| ID       | Task                                                                                         | Priority | Status | DoD                                                          |
| -------- | -------------------------------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------------ |
| **T901** | `systemd/pitunnel.service` (per §7.2) + `systemd/pitunnel-watchdog.timer` (optional)         | P0       | []     | `systemctl enable --now pitunnel` starts and survives reboot |
| **T902** | `scripts/install.sh`: creates user, groups, dirs, venv, deploys configs, installs unit       | P1       | []     | Idempotent run on clean Pi                                   |
| **T903** | `scripts/rotate_token.sh`: generates new token, updates `/etc/pitunnel.env`, reloads service | P1       | []     | Rotation without downtime                                    |
| **T904** | `docs/OPERATIONS.md`: runbook (logs, backup, restore, troubleshooting, metrics)              | P1       | []     | Complete and tested document                                 |

---

## 🔟 Testing & Quality

| ID        | Task                                                                                 | Priority | Status | DoD                                                        |
| --------- | ------------------------------------------------------------------------------------ | -------- | ------ | ---------------------------------------------------------- |
| **T1001** | Unit tests: auth, executor, sensors, actuators, alerts, storage (coverage ≥ 85%)     | P1       | []     | `pytest --cov=pitunnel --cov-fail-under=85` passes         |
| **T1002** | Integration tests with **pytest-asyncio** + `TestClient` simulating Telegram Updates | P1       | []     | Full flow `/cmd restart-mqtt` → confirm → execute verified |
| **T1003** | Smoke test on real Pi (CI/CD optional with `act` or self-hosted runner)              | P2       | []     | Pipeline green on push to `main`                           |
| **T1004** | Stress tests: 50 concurrent commands, network cut 5 min, Pi reboot                   | P2       | []     | P95 latency < 2s; no memory leaks; auto-recovery           |

---

## 1️⃣1️⃣ Observability (Optional v1)

| ID        | Task                                                                                                                                         | Priority | Status | DoD                                           |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | --------------------------------------------- |
| **T1101** | `/metrics` endpoint (Prometheus) on port 9090 localhost only: `commands_total`, `command_duration_seconds`, `sensor_reading`, `alerts_fired` | P2       | []     | `curl localhost:9090/metrics` returns metrics |
| **T1102** | Grafana dashboard JSON (system + bot + sensors)                                                                                              | P2       | []     | Importable in local Grafana                   |

---

## 🗂 Suggested Sprint Plan (2 weeks each)

| Sprint | Key Tasks                       | Deliverable                                           |
| ------ | ------------------------------- | ----------------------------------------------------- |
| **S0** | T001–T005                       | Repo ready, CI green                                  |
| **S1** | T101–T105, T201–T204            | Bot responds `/start`, `/help`, `/cmd` with whitelist |
| **S2** | T301–T302, T701–T703            | `/status` + persistent history                        |
| **S3** | T401–T404                       | `/sensors` functional with 2+ drivers                 |
| **S4** | T501–T503                       | `/on` `/off` real actuators                           |
| **S5** | T601–T604                       | Proactive alerts + `/alerts`                          |
| **S6** | T801–T802 (optional), T901–T904 | Deploy on real Pi + runbook                           |
| **S7** | T1001–T1004, T1101–T1102        | Coverage, stress, observability                       |

---

## 🎯 Immediate Next Step

Generate project skeleton (folders, `pyproject.toml`, `config.yaml.example`, empty `main.py`, `systemd` unit) to kick off **Sprint 0**.
