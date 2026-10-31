# system/status Specification

## Purpose

Provide authorized users with an on-demand system health snapshot via Telegram, enabling remote monitoring of PiTunnel host metrics without SSH access.

## Requirements

### Requirement: System status retrieval

The system SHALL provide a `get_system_status` operation that returns CPU percentage, RAM percentage, CPU temperature, disk usage for `/`, disk usage for `/mnt/nas`, system uptime, local IP address of default interface, and public IP address.

#### Scenario: Status includes all metrics

- **WHEN** authorized user sends `/status` command
- **THEN** bot replies with Markdown containing CPU%, RAM%, CPU temp, Disk `/`, Disk `/mnt/nas`, Uptime, Local IP, Public IP

### Requirement: Public IP caching

The system SHALL cache public IP results for 10 minutes to avoid repeated external HTTP requests.

#### Scenario: Cache prevents repeated calls

- **WHEN** user requests `/status` twice within 10 minutes
- **THEN** second response uses cached public IP and no external HTTP request is made

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