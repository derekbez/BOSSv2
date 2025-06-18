# Copilot Instructions for B.O.S.S. (Board Of Switches and Screen)

## Project Overview
B.O.S.S. is a modular, Python-based application for the Raspberry Pi (OS 64-bit Lite, no GUI) that provides a physical interface to select and execute mini-apps. Users interact using eight toggle switches (combined via a 74HC151 multiplexer) to choose a value from 0–255, which is immediately displayed on a TM1637-based 7-segment display. Pressing the main "Go" button launches the mini-app mapped to that number. Mini-apps can interact with a 7-inch screen, four color-coded LEDs and buttons (Red, Yellow, Green, Blue), and optionally a speaker. Remote management over WiFi is also supported via a secure API.

## System Requirements and Installation
- **Hardware:**
  - Raspberry Pi running Raspberry Pi OS 64bit Lite (no GUI)
  - 8 toggle switches (through a 74HC151 multiplexer)
  - 4 color-coded buttons and 4 color-coded LEDs
  - Main "Go" button
  - TM1637 7-segment display
  - 7-inch screen
  - Optional speaker for audio output
- **Software Setup:**
  - Python 3.11+
  - Virtual environment recommended
  - Required libraries include: `gpiozero`, `pigpio`, `rpi-tm1637`, and others as specified in `requirements.txt`
  - Configuration is managed in a JSON file (`BOSSsettings.json`)
  - For development on non-RPi platforms, support for remote GPIO (via PiGPIOFactory) allows emulation/testing

## High-Level Architecture & Components
- **Language & Platform:** Python 3.11+, Raspberry Pi OS 64bit Lite  
- **Design Patterns:**
  - **Dependency Injection:** For flexible hardware abstraction and unit testing
  - **Observer/Event Pattern:** Manages button and switch events
  - **Plugin Pattern:** Dynamically load mini-apps from the `apps/` directory
  - **Singleton:** Centralized configuration and logging
  - **Factory Pattern:** Instantiates hardware interfaces uniformly
  - **OOP/Class-based Design:** Encourages maintainability and extensibility

### Key Components & Directory Structure
- **Entry Point:** `main.py` – Initializes hardware, logging, configuration, and the app lifecycle.
- **Core Modules (in `core/`):**
  - `app_manager.py`: Loads/unloads mini-apps and manages their lifecycle with timeouts.
  - `event_bus.py`: Publishes hardware events to system and mini-app subscribers.
  - `config.py`: Loads and validates JSON configuration from `BOSSsettings.json`, mapping switch values to apps.
  - `logger.py`: Implements a centralized logging system with rotation and error tracking.
  - `api.py`: Provides a controlled API for mini-apps to interact with hardware (screen, LEDs, buttons, etc.).
  - `remote.py`: Exposes a secure REST API for remote management and configuration via WiFi.
- **Hardware Abstraction (in `hardware/`):**
  - `switch_reader.py`: Reads the 8 toggle switches using a 74HC151 multiplexer.
  - `button.py`: Handles debounced button inputs.
  - `led.py`: Controls individual LEDs.
  - `display.py`: Manages the TM1637 7-segment display.
  - `screen.py`: Interfaces with the 7-inch screen using direct or framebuffer draws.
  - `speaker.py`: Handles optional audio output.
- **Mini-Apps (in `apps/`):** Each app is a Python module (e.g., `app_matrixrain.py`, `app_showtext.py`), following a standard interface such as `run(stop_event, api)`.  
  - Each app should also include a minimal manifest (in JSON or as module-level metadata) providing its name, description, and hardware usage.
- **Supporting Assets & Tests:**
  - `assets/`: Contains images, sounds, or other resources used by apps.
  - `tests/`: Unit and integration tests for hardware abstraction, core logic, and app interactions.
- **Documentation:**
  - Documentation and user stories are maintained in `docs/` (e.g., `docs/user-stories.md`).

## App Development Guidelines
- **API Usage:**
  - Mini-apps **MUST** access all hardware through the provided API in `api.py`. No direct GPIO or hardware calls are allowed.
  - The API layer exposes functions for screen drawing, LED control, button input, and optionally network access.
- **Lifecycle & Thread Management:**
  - Each mini-app must run in its own thread and periodically check a provided `stop_event` for shutdown requests.
  - The system will enforce a timeout on mini-apps and, if needed, force stop execution.
- **Configuration & Mapping:**
  - The mapping of toggle switch values to mini-apps and their parameters is maintained in the JSON file (`BOSSsettings.json`). Default configurations are auto-generated when missing.
- **Code Quality:**
  - Use type hints and thorough docstrings for every module and function.
  - Follow the single-responsibility principle and maintain clear separation between hardware and business logic.
  - Ensure that any new code is covered by unit tests and, where applicable, integration tests.

## Testing Requirements
- **Unit Testing:**
  - Use `pytest` to cover all critical modules, particularly hardware abstraction layers and core functionalities.
  - Leverage dependency injection to mock physical hardware for tests.
- **Integration Testing:**
  - Create tests for app lifecycle events: loading, executing, and forced shutdown.
  - Validate configuration formats and error handling paths.
- **CI Integration:**
  - Automated tests should run via CI pipelines (e.g., GitHub Actions) with coverage reporting.
- **Emulation & Simulation:**
  - Provide emulation modules to simulate GPIO inputs/outputs when running in non-RPi environments.

## Best Practices & Git Workflow
- **Coding Standards & Documentation:**
  - Adhere to GB English conventions.
  - Document every module, function, and app with clear docstrings.
  - Maintain an up-to-date README with architecture diagrams, setup instructions, and contribution guidelines.
- **Version Control:**
  - The `main` branch must always be deployable.
  - Develop features in well-scoped branches with atomic PRs.
  - Use squash and rebase practices to maintain a clean commit history.
  - Follow semantic versioning for releases.
- **Security & Error Handling:**
  - All hardware interactions must be wrapped in try/except blocks with appropriate fallbacks.
  - The remote management API must implement secure authentication (e.g., JWT tokens) on all end points.
  - Validate all configuration and user inputs to prevent system crashes.

## Acceptance Criteria
- **Robustness:** Meets all functional requirements and gracefully handles hardware errors.
- **Modularity:** New apps and hardware can be added without core system modifications.
- **Testing:** Complete coverage of core logic and hardware abstraction via unit and integration tests.
- **Documentation:** Comprehensive documentation is provided for setup, development, and usage.
- **Remote & OTA Support:** Remote management APIs are secure, and the system supports future OTA app sync capabilities.

---

*This document guides GitHub Copilot and human developers in understanding the B.O.S.S. project's scope, architecture, and best practices. Please update this file as needed to reflect evolving requirements and implementation details.*
