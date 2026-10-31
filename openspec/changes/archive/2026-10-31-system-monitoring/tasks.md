# Tasks

## 1. System status module

- [x] 1.1 Create `src/pitunnel/system/status.py` with `SystemStatus` dataclass and `get_system_status()` stub returning all required fields, verify import succeeds
- [x] 1.2 Implement CPU%, RAM%, disk usage on `/`, disk usage on `/mnt/nas`, uptime, local IP using `psutil`, verify values are numeric and within expected ranges
- [x] 1.3 Implement CPU temperature reading from `/sys/class/thermal/thermal_zone0/temp` with fallback to `psutil.sensors_temperatures()`, verify returns float or `N/A`
- [x] 1.4 Implement public IP fetch via `https://api.ipify.org?format=text` with 3s timeout and in-memory TTL cache 600s, verify second call within TTL does not trigger HTTP request

## 2. Command integration

- [x] 2.1 Add `/status` handler in `commands/handlers.py` calling `get_system_status()` and formatting Markdown response, verify handler is registered
- [x] 2.2 Add i18n strings for status labels in ES/EN, verify `/status` output uses configured language
- [x] 2.3 Add unit test for `get_system_status()` with mocked `psutil` and HTTP, verify test passes

## 3. Documentation

- [x] 3.1 Update `README.md` with `/status` usage example, verify documentation renders correctly
- [x] 3.2 Add note about public IP cache behavior to `docs/OPERATIONS.md`, verify note is present

## Workflow follow-up

- Archive the change after review and validation passes
- Verify archived spec `system/status` is present in main specs
