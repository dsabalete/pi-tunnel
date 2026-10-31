# Spec Delta

## MODIFIED Requirements

### Requirement: System status retrieval

The system SHALL provide a `get_system_status` operation that returns CPU percentage, RAM percentage, CPU temperature, disk usage for `/`, disk usage for `/mnt/nas`, system uptime, local IP address of default interface, and public IP address.

#### Scenario: Status includes all metrics
- **WHEN** authorized user sends `/status` command
- **THEN** bot replies with Markdown containing CPU%, RAM%, CPU temp, Disk `/`, Disk `/mnt/nas`, Uptime, Local IP, Public IP

#### Scenario: Implementation completeness
- **WHEN** `get_system_status()` is called
- **THEN** returns a `SystemStatus` dataclass with all fields populated (cpu_percent, ram_percent, cpu_temp_c, disk_root_percent, disk_nas_percent, uptime_seconds, local_ip, public_ip)

### Requirement: Public IP caching

The system SHALL cache public IP results for 10 minutes to avoid repeated external HTTP requests.

#### Scenario: Cache prevents repeated calls
- **WHEN** user requests `/status` twice within 10 minutes
- **THEN** second response uses cached public IP and no external HTTP request is made

#### Scenario: Cache TTL is 600 seconds
- **WHEN** 600+ seconds have elapsed since last public IP fetch
- **THEN** next call triggers a fresh external HTTP request to api.ipify.org

### Requirement: Public IP timeout

The system SHALL fail gracefully for public IP lookup if the external service does not respond within 3 seconds.

#### Scenario: Timeout fallback
- **WHEN** api.ipify.org does not respond within 3s
- **THEN** status response includes public IP as `unknown` and does not raise error to user

### Requirement: Status formatting

The system SHALL format status output as Markdown with labeled fields for each metric.

#### Scenario: Readable output
- **WHEN** `/status` is executed
- **THEN** response is Markdown with clear labels and units for each metric

#### Scenario: Uptime human-readable format
- **WHEN** `/status` is executed
- **THEN** uptime displayed as `Xd Yh Zm` format (e.g., "2d 14h 32m")

## ADDED Requirements

### Requirement: Status command handler integration

The system SHALL provide a `/status` command handler that calls `get_system_status()` and formats the response for Telegram.

#### Scenario: Handler returns formatted status
- **WHEN** authorized user sends `/status`
- **THEN** handler calls `get_system_status()`, formats all metrics as Markdown, and sends response