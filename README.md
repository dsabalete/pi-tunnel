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

Run the bot with:
```bash
python -m pitunnel.main
```

## Project Structure

- `src/pitunnel/` - Main source code
- `tests/` - Unit tests
- `config/` - Configuration files
- `scripts/` - Deployment and helper scripts
- `systemd/` - Systemd service files

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.