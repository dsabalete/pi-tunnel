# PiTunnel

PiTunnel is a Telegram bot that allows remote control and monitoring of a Raspberry Pi via Telegram messages.

## Features

- Execute commands on the Raspberry Pi through Telegram
- Monitor system status (CPU, RAM, temperature, disk usage)
- Read sensor data from connected sensors (temperature, humidity, etc.)
- Control actuators (relays, LEDs, etc.)
- Proactive alerts and notifications

## Requirements

- Python 3.11+
- Raspberry Pi with Raspberry Pi OS
- Telegram bot token (created with @BotFather)

## Installation

1. Clone this repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Configure the bot with your Telegram token

## Configuration

Before running the bot, you'll need to:

1. Create a Telegram bot using [@BotFather](https://t.me/BotFather)
2. Set up configuration in `config/config.yaml.example` and rename it to `config.yaml`
3. Set up environment variables in `config/pitunnel.env.example` and rename it to `pitunnel.env`

## Usage

### Native Python

Run the bot with:
```bash
python -m pitunnel.main
```

### Commands

- `/status` – Show system health: CPU, RAM, temperature, disk usage, uptime, local and public IP.
  Example output:
  ```
  📊 *System Status*
  CPU: 12.5%
  RAM: 45.0%
  CPU Temp: 55.0°C
  Disk /: 72.9%
  Uptime: 0d 1h 23m
  Local IP: 192.168.0.16
  Public IP: 37.222.144.110
  ```

### Docker

Build the image:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t pitunnel:latest .
```

Run with Compose:
```bash
docker compose up -d
```

Configuration is provided via volume mount `./config:/app/config:ro` and environment file `./config/pitunnel.env`. Ensure `config/config.yaml` and `config/pitunnel.env` exist on the host before starting.

For Raspberry Pi GPIO / I2C access, run with privileged mode or device mounts. Example override in `docker-compose.override.yml`:
```yaml
services:
  pitunnel:
    privileged: true
    devices:
      - /dev/gpiomem:/dev/gpiomem
      - /dev/i2c-1:/dev/i2c-1
```

## Project Structure

- `src/pitunnel/` - Main source code
- `tests/` - Unit tests
- `config/` - Configuration files
- `scripts/` - Deployment and helper scripts
- `systemd/` - Systemd service files

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.