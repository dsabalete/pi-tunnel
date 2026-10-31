# Spec Delta

## Purpose

Provides actuator abstraction for controlling GPIO-connected devices (relays, LEDs) via Telegram commands `/on <id>` and `/off <id>`, with safety confirmations for destructive actions and proper error handling for hardware failures.

## ADDED Requirements

### Requirement: Actuator protocol definition
The system SHALL define an `Actuator` protocol with `on()`, `off()`, and `state() -> bool` methods for uniform GPIO control.

#### Scenario: All actuators implement protocol
- **WHEN** an actuator is instantiated
- **THEN** it implements the Actuator protocol with on(), off(), and state() methods

### Requirement: Relay actuator implementation
The system SHALL provide a `RelayActuator` class that controls GPIO pins via gpiozero OutputDevice.

#### Scenario: Relay turns on
- **WHEN** `RelayActuator.on()` is called
- **THEN** GPIO pin is set to HIGH (relay closed)

#### Scenario: Relay turns off
- **WHEN** `RelayActuator.off()` is called
- **THEN** GPIO pin is set to LOW (relay open)

### Requirement: LED actuator PWM support
The system SHALL provide an `LEDActuator` with optional PWM support for brightness control.

#### Scenario: LED brightness control
- **WHEN** LEDActuator state is set to 0.5
- **THEN** GPIO outputs 50% PWM duty cycle

### Requirement: Actuator command handlers
The system SHALL provide `/on <id>` and `/off <id>` command handlers to control actuators by ID.

#### Scenario: Turn on actuator
- **WHEN** authorized user sends `/on luz-porche`
- **THEN** bot confirms existence, validates ID, optionally asks confirmation, and executes on()

#### Scenario: Turn off actuator
- **WHEN** authorized user sends `/off luz-porche`
- **THEN** bot confirms action, executes off(), and replies with success message

### Requirement: Actuator validation
The system SHALL validate actuator IDs exist before attempting control.

#### Scenario: Invalid actuator ID
- **WHEN** user sends `/on nonexistent`
- **THEN** bot replies with "Actuator not found" error

### Requirement: Confirmation flow
The system SHALL prompt for confirmation before executing destructive actions (configurable via `confirm: true`).

#### Scenario: Destructive action requires confirmation
- **WHEN** user sends `/cmd reboot` where reboot has `destructive: true`
- **THEN** bot shows "Confirm" and "Cancel" buttons before executing

### Requirement: Hardware error handling
The system SHALL handle actuator control failures gracefully without crashing the bot.

#### Scenario: GPIO access denied
- **WHEN** actuator control raises permission error
- **THEN** error is logged and user sees friendly error message