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
  - 7-inch HDMI screen
  - Speaker (optional)
- **Setup:**
  - Python 3.11+
  - Use a Python virtual environment
  - Install dependencies:  `gpiozero`, `pigpio`, `python-tm1637`, `pytest`, `Pillow`, `numpy`, etc.
  - All configuration is in `config/BOSSsettings.json`

## Directory Structure
```
boss/
  __init__.py
  main.py
  core/
    __init__.py
    app_manager.py
    event_bus.py
    config.py
    logger.py
    api.py
    remote.py
  hardware/
    __init__.py
    switch_reader.py
    button.py
    led.py
    display.py
    screen.py
    speaker.py
  apps/
    app_matrixrain/
      __init__.py
      main.py
      manifest.json
      assets/
    ...
  assets/
    images/
    sounds/
  config/
    BOSSsettings.json
  tests/
    core/
    hardware/
    apps/
  scripts/
  docs/
  requirements.txt
  README.md
```

## Key Principles & Coding Guidelines
- **Event-Driven:** All hardware and app events are published to the event bus. Display, LED, and screen updates are event-driven (no polling in production code).
- **Hardware Abstraction:** All hardware (buttons, LEDs, display, screen, speaker) is abstracted in `hardware/` with real and mock implementations. Fallback to mocks if hardware is not detected, enabling dev/testing on any platform.
- **App API:** Mini-apps must not access hardware directly. All hardware and display access is via the provided API object.
- **Threading:** Mini-apps run in threads, with forced termination if they exceed a timeout. Use `stop_event` for clean shutdown.
- **Configuration:** All app mappings and parameters are in `config/BOSSsettings.json` (JSON format). If missing, auto-generated with defaults.
- **Logging:** Use the central logger for all events and errors. All hardware and app events are logged for auditing.
- **Remote Management:** The system exposes a secure API for remote configuration and status.
- **Testing:** Use dependency injection and mocks for hardware in tests. Place all tests in `tests/`, mirroring the main structure. Use `pytest` and ensure coverage.
- **Extensibility:**
  - Add new apps by creating a new subdirectory in `apps/` with `main.py`, `manifest.json`, and any assets.
  - Add new hardware by extending the hardware abstraction layer.
  - Register new event types with the event bus as needed.
- **Type Hints & Docstrings:** Use type hints and docstrings throughout for clarity and maintainability.
- **Validation:** Validate all configuration and user input.
- **Single Responsibility:** Keep code modular and follow the single-responsibility principle.
- **Dependency Injection:** Pass dependencies (e.g., hardware, event bus) into constructors instead of creating them inside classes.

## Best Practices
- Print/log all pin assignments and a hardware startup summary at launch, indicating which devices are real or mocked.
- Use event-driven patterns for all hardware events and outputs.
- Document all new apps and hardware modules.
- All code is inside the `boss/` package for import clarity.
- Each app is a subdirectory with its own code, manifest, and assets.
- All configuration is in `config/`.
- All documentation is in `docs/`.
- All tests are in `tests/`, mirroring the main structure.

## App Structure
- Each mini-app is a subdirectory under `apps/`, e.g.:
  - `main.py`: Entry point, must implement `run(stop_event, api)`
  - `manifest.json`: Metadata (name, description, etc.)
  - `assets/`: Data files (e.g., images, sounds, JSON)
- Apps load assets at runtime and use the API for all hardware/display access.
- All mini-apps and tests use real or mock hardware as appropriate.

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
