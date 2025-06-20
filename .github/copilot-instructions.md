# Copilot Instructions for B.O.S.S. (Board Of Switches and Screen)

## Project Overview
B.O.S.S. is a modular Python application for Raspberry Pi that provides a physical interface to select and run mini-apps through 8 toggle switches (0-255). The system displays the selected number on a 7-segment display and executes the corresponding app when the "Go" button is pressed. Apps can utilize a 7-inch screen, 4 color LEDs, 4 color buttons, and optionally a speaker for interaction.

## System Requirements and Installation
- **Hardware:**
  - Raspberry Pi (64bit Lite OS, no GUI)
  - 8 toggle switches (via 74HC151 multiplexer)
  - 4 color buttons (Red, Yellow, Green, Blue)
  - 4 color LEDs (Red, Yellow, Green, Blue)
  - Main "Go" button
  - TM1637 7-segment display
  - 7-inch screen
  - Speaker (optional, for some apps)
- **Setup:**
  - Python 3.11+
  - Use Python virtual environment
  - Install dependencies: `gpiozero`, `pigpio`, `rpi-tm1637`, etc.
  - All configuration is in `BOSSsettings.json`

## Key Components
- **main.py:** Entry point, initializes hardware, loads config, manages app lifecycle, handles errors and logging. At startup, prints/logs pin assignments and a hardware startup summary, indicating which devices are real or mocked. Each hardware device (button, LED, display, etc.) falls back to a mock if not detected, allowing seamless development and testing without hardware.
- **core/**: App management, event bus, config, logging, API for apps, remote management.
- **hardware/**: Abstractions for switches, buttons, LEDs, display, screen, speaker.
- **apps/**: Mini-apps, each as a Python module implementing the required API interface.
- **assets/**: Images, sounds, and other data files.
- **tests/**: Unit and integration tests for all core and hardware modules.

## Coding Guidelines
- **App API:** Apps must not access hardware directly. All hardware and display access is via the provided API object.
- **Threading:** Mini-apps run in threads, with forced termination if they exceed a timeout.
- **Configuration:** All app mappings and parameters are in `BOSSsettings.json` (JSON format).
- **Logging:** Use the central logger for all events and errors.
- **Remote Management:** The system exposes a secure API for remote configuration and status.
- **Error Handling:** Catch and log all hardware and app errors. Ensure safe shutdown.
- **Extensibility:** Add new apps by dropping new `app_*.py` modules in `apps/` and updating the config. Add new hardware by extending the hardware abstraction layer.
- **Testing:** Use dependency injection and mocks for hardware in tests. Place all tests in `tests/`.

## Best Practices
- The system prints/logs all pin assignments and a hardware startup summary at launch, indicating which devices are real or mocked.
- Each hardware device (button, LED, display, etc.) falls back to a mock if not detected, allowing seamless development and testing without hardware.
- Use type hints and docstrings throughout.
- Keep code modular and follow single-responsibility principle.
- Validate all configuration and user input.
- Use event-driven patterns for hardware events.
- Document all new apps and hardware modules.

## Directory Structure
```
boss/
  main.py
  core/
    app_manager.py
    event_bus.py
    config.py
    logger.py
    api.py
    remote.py
  hardware/
    switch_reader.py
    button.py
    led.py
    display.py
    screen.py
    speaker.py
  apps/
    app_matrixrain.py
    app_showtext.py
    ...
  assets/
    images/
    sounds/
    ...
  tests/
    test_switch_reader.py
    test_app_manager.py
    ...
  BOSSsettings.json
  requirements.txt
  README.md
```

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

---

Always run the BOSS app from the project root (~/boss) for correct module resolution.
Example:
```
cd ~/boss
python3 -m boss.main
```

Do NOT run from inside the boss/boss subfolder.

*This file guides GitHub Copilot in understanding the BOSS project's architecture, patterns, and requirements. Update as needed.*
