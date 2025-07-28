# Copilot Instructions for B.O.S.S. (Board Of Switches and Screen)

## Project Overview
B.O.S.S. is a modular, event-driven Python application for Raspberry Pi. It provides a physical interface to select and run mini-apps using 8 toggle switches (0–255), a 7-segment display, 4 color LEDs, 4 color buttons, a main "Go" button, a 7-inch screen, and optionally a speaker. The system is designed for extensibility, robust hardware abstraction, and seamless development/testing with or without real hardware.

## System Requirements & Installation
- **Hardware:**
  - Raspberry Pi (64bit Lite OS, no GUI)
  - 8 toggle switches (via 74HC151 multiplexer)
  - 4 color buttons (Red, Yellow, Green, Blue)
  - 4 color LEDs (Red, Yellow, Green, Blue)
  - Main "Go" button
  - TM1637 7-segment display
  - 7-inch HDMI screen (output via `rich` library)
  - Speaker (optional)
- **Setup:**
  - Python 3.11+
  - Use a Python virtual environment
  - Install dependencies:  `gpiozero`, `pigpio`, `python-tm1637`, `pytest`, `rich`, `numpy`, etc.
  - All configuration is in `boss/config/` (co-located with main code for modularity)
    - `boss/config/boss_config.json` - Hardware pins, system settings
    - `boss/config/app_mappings.json` - Switch-to-app mappings

## Directory Structure
```
boss/
├── __init__.py
├── main.py                     # Entry point with dependency injection setup
├── presentation/              # UI/API interfaces (no business logic)
│   ├── __init__.py
│   ├── physical_ui/
│   │   ├── __init__.py
│   │   ├── button_handler.py   # Physical button event handling
│   │   └── switch_handler.py   # Switch state monitoring
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rest_api.py        # REST endpoints for remote management
│   │   ├── websocket_api.py   # Real-time event streaming
│   │   └── web_ui.py          # Development web interface
│   └── cli/
│       ├── __init__.py
│       └── debug_cli.py       # Debug and maintenance commands
├── application/               # Service classes and business logic
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── app_manager.py     # App lifecycle management
│   │   ├── app_runner.py      # Thread management for mini-apps
│   │   ├── switch_monitor.py  # Switch state monitoring and events
│   │   ├── hardware_service.py # Hardware coordination
│   │   └── system_service.py  # System health and shutdown
│   ├── events/
│   │   ├── __init__.py
│   │   ├── event_bus.py       # Simple, robust event bus
│   │   └── event_handlers.py  # System event handlers
│   └── api/
│       ├── __init__.py
│       └── app_api.py         # API provided to mini-apps
├── domain/                    # Core models and business rules
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── app.py            # App entity and business rules
│   │   ├── hardware_state.py # Hardware state models
│   │   └── config.py         # Configuration models
│   ├── events/
│   │   ├── __init__.py
│   │   └── domain_events.py  # Domain event definitions
│   └── interfaces/
│       ├── __init__.py
│       ├── hardware.py       # Hardware abstraction interfaces
│       ├── app_api.py        # App API interface
│       └── services.py       # Service interfaces
├── infrastructure/           # Hardware, config, logging implementations
│   ├── __init__.py
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── factory.py        # Hardware factory (GPIO/WebUI/Mock)
│   │   ├── gpio/             # Real hardware implementations
│   │   │   ├── __init__.py
│   │   │   ├── buttons.py
│   │   │   ├── leds.py
│   │   │   ├── display.py
│   │   │   ├── switches.py
│   │   │   ├── screen.py
│   │   │   └── speaker.py
│   │   ├── webui/           # Web UI implementations for development
│   │   │   ├── __init__.py
│   │   │   ├── webui_buttons.py
│   │   │   ├── webui_leds.py
│   │   │   └── webui_display.py
│   │   └── mocks/           # Mock implementations for testing
│   │       ├── __init__.py
│   │       ├── mock_buttons.py
│   │       ├── mock_leds.py
│   │       ├── mock_display.py
│   │       └── mock_switches.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py  # JSON config loading and validation
│   │   └── config_manager.py # Runtime config management
│   └── logging/
│       ├── __init__.py
│       ├── logger.py         # Centralized logging setup
│       └── formatters.py     # Log formatting
├── apps/                     # Mini-apps directory
│   ├── __init__.py
│   ├── app_template/         # Template for new apps
│   └── app_matrixrain/       # Example app
└── tests/                    # Test structure mirrors main structure
    ├── __init__.py
    ├── unit/
    ├── integration/
    └── test_fixtures/
```

## Key Principles & Coding Guidelines
- **Clean Architecture:** Layer separation (Presentation, Application, Domain, Infrastructure) with dependency inversion
- **Event-Driven:** All hardware and app events are published to the event bus. Display, LED, and screen updates are event-driven (no polling in production code)
- **Hardware Abstraction:** All hardware (buttons, LEDs, display, screen, speaker) is abstracted with real, WebUI, and mock implementations. Fallback to mocks if hardware is not detected, enabling dev/testing on any platform
- **Hardware Parity Principle:** The WebUI is a development emulation layer that mirrors real hardware behavior exactly. Any behavior implemented for real GPIO hardware must work identically in the WebUI, and any feature developed/tested in the WebUI must work identically on real hardware. This ensures seamless development-to-production transitions
- **App API:** Mini-apps must not access hardware directly. All hardware and display access is via the provided API object
- **Threading:** Mini-apps run in threads, with forced termination if they exceed a timeout. Use `stop_event` for clean shutdown
- **Configuration:** System config in `boss/config/boss_config.json`, app mappings in `boss/config/app_mappings.json` (JSON format). Co-located with main code for modularity. If missing, auto-generated with defaults
- **Logging:** Use the central logger for all events and errors. All hardware and app events are logged for auditing
- **Remote Management:** The system exposes a secure API for remote configuration and status
- **Testing:** Use dependency injection and mocks for hardware in tests. Place all tests in `tests/`, mirroring the main structure. Use `pytest` and ensure coverage
- **Extensibility:**
  - Add new apps by creating a new subdirectory in `boss/apps/` with `main.py`, `manifest.json`, and any assets
  - Add new hardware by extending the hardware abstraction layer (for screen output, use `rich` instead of Pillow)
  - Register new event types with the event bus as needed
- **Type Hints & Docstrings:** Use type hints and docstrings throughout for clarity and maintainability
- **Validation:** Validate all configuration and user input
- **Single Responsibility:** Keep code modular and follow the single-responsibility principle
- **Dependency Injection:** Pass dependencies (e.g., hardware, event bus) into constructors instead of creating them inside classes

## Best Practices
- Print/log all pin assignments and a hardware startup summary at launch, indicating which devices are real or mocked.
- Use event-driven patterns for all hardware events and outputs.
  - Document all new apps and hardware modules. For screen output, use the `rich` library for text and simple graphics.
- All code is inside the `boss/` package for import clarity.
- Each app is a subdirectory in `boss/apps/` with its own code, manifest, and assets.
  - All configuration is co-located in `boss/config/`.
  - All documentation is in `docs/`.
  - All tests are in `tests/`, mirroring the main structure.
  - The HDMI screen is driven by the `rich` library (not Pillow).

## App Structure
- Each mini-app is a subdirectory under `boss/apps/`, e.g.:
  - `main.py`: Entry point, must implement `run(stop_event, api)`
  - `manifest.json`: Metadata (name, description, etc.) - supports both standard and legacy formats with auto-conversion
  - `assets/`: Data files (e.g., images, sounds, JSON)
- Apps load assets at runtime and use the API for all hardware/display access.
- All mini-apps and tests use real or mock hardware as appropriate.

## Critical UX Pattern: LED/Button Coordination
**IMPORTANT**: Mini-apps MUST follow this LED/Button pattern for consistent user experience across BOTH real hardware and WebUI development:

### LED State Rule (Hardware Parity)
- **LEDs indicate which buttons are active/expected** (applies to both physical LEDs and WebUI LED indicators)
- If app expects RED button press → RED LED should be ON (physical LED on Pi, virtual LED in WebUI)
- If app expects BLUE and YELLOW buttons → BLUE and YELLOW LEDs ON, others OFF (both environments)
- If no button expected → ALL LEDs OFF (both environments)
- **Button presses are filtered**: If LED is OFF, button press is ignored (both physical buttons and WebUI buttons)
- LEDs provide immediate visual feedback about available actions in both development and production

### Hardware Parity Implementation
- **Real Hardware**: Physical button press when LED is OFF → no event reaches app
- **WebUI Development**: Virtual button click when LED is OFF → no event reaches app  
- **Behavioral Consistency**: What works in WebUI development works identically on real hardware

### Implementation Pattern
```python
def setup_button_state():
    # Example: App expects Red and Blue buttons
    api.hardware.set_led('red', True)     # RED button available
    api.hardware.set_led('blue', True)    # BLUE button available  
    api.hardware.set_led('yellow', False) # YELLOW not used
    api.hardware.set_led('green', False)  # GREEN not used

def cleanup_leds():
    # Always turn off all LEDs when app exits
    for color in ['red', 'yellow', 'green', 'blue']:
        api.hardware.set_led(color, False)
```

### Event Subscription
- Use `api.event_bus.subscribe('button_pressed', handler)` for button presses
- Use `api.event_bus.subscribe('button_released', handler)` for button releases  
- Check `event.get('button_id')` or `event.get('button')` for button color
- Always unsubscribe in `finally` block: `api.event_bus.unsubscribe(sub_id)`

## Configuration Files Structure

### System Configuration (`boss/config/boss_config.json`)
```json
{
  "hardware": {
    "switch_data_pin": 18,
    "button_pins": {"red": 5, "yellow": 6, "green": 13, "blue": 19},
    "led_pins": {"red": 21, "yellow": 20, "green": 26, "blue": 12},
    "display_clk_pin": 2,
    "display_dio_pin": 3,
    "screen_width": 800,
    "screen_height": 480,
    "enable_audio": true
  },
  "system": {
    "apps_directory": "apps",
    "log_level": "INFO",
    "app_timeout_seconds": 300
  }
}
```

### App Mappings (`boss/config/app_mappings.json`)
```json
{
  "app_mappings": {
    "0": "list_all_apps",
    "1": "hello_world",
    "255": "admin_shutdown"
  },
  "parameters": {}
}
```

## Workflow & Usage
- Always run the BOSS app from the project root for correct module resolution:
  ```
  cd ~/boss
  python3 -m boss.main
  ```
- Do NOT run from inside the boss/boss subfolder.
- At startup, the system prints/logs all pin assignments and a hardware startup summary.
- Each hardware device falls back to a mock if not detected, allowing seamless development and testing without hardware.

## Git Workflow
- Main branch must always be deployable.
- Use feature branches for new development.
- Keep PRs focused and atomic; squash and rebase as needed.
- Ignore generated files and sensitive config.
- Tag releases with semantic versioning.

## Testing Framework
  - Use `pytest` for all tests.
  - Mock hardware interfaces in tests.
  - Run tests with `pytest` and coverage.
  - Place all tests in `tests/`.
  - For screen output, use the `rich` library for all new development.

## Acceptance Criteria
- Meets all functional requirements
- Robust to hardware errors
- Clean shutdown support
- No direct hardware access in apps
- Modular and extensible design
- Complete test coverage
- Up-to-date documentation
- Remote management support
- WiFi connectivity
- Secure API endpoints

## User Stories
- When working from User Stories, always update the user story after implementing the feature to reflect the actual implementation. Set the status, add relevant implementation notes, and any todos for future improvements.

---

*This file guides GitHub Copilot and human developers in understanding the BOSS project's architecture, patterns, and requirements. Update as needed to reflect the latest best practices and system design.*
