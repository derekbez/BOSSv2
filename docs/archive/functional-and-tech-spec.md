# B.O.S.S. (Board Of Switches and Screen)
## Functional & Technical Specification
**Version:** 2.0  
**Date:** 2025-07-21  
**Author:** BOSS Development Team  
**Status:** IMPLEMENTED - New Simplified Architecture

---

## 1. Purpose
Implement a robust, maintainable, and extensible B.O.S.S. application for Raspberry Pi, providing a physical interface for selecting and running mini-apps via switches, buttons, LEDs, a 7-segment display, and a screen. The new implementation follows Clean Architecture principles with simplified patterns appropriate for the project scale.

**Note**: This specification reflects the **implemented system** using the new simplified architecture that removed over-engineered patterns like CQRS while maintaining Clean Architecture benefits.

---

## 2. Functional Specification

### 2.1. User Stories
User stories and personas are now maintained in [docs/user-stories.md](./user-stories.md) for clarity and reuse.

### 2.2. Functional Requirements

**FR1.** The 7-segment display must update immediately when the toggle switches change, even while a mini-app is running.  
**FR2.** The number input mechanism (switches + multiplexer) must be abstracted to allow for future replacement (e.g., dial, keypad).  
**FR3.** The system must read 8 toggle switches via a multiplexer to determine a value (0–255).  
**FR4.** The current value must be displayed on a TM1637 7-segment display.  
**FR5.** Pressing the main "Go" button launches the mapped mini-app.  
**FR6.** Mini-apps must interact with hardware only via a provided API, not direct access.  
**FR7.** Mini-apps must be able to use the screen, LEDs, and color buttons for I/O via the API.  
**FR8.** The system must support dynamic loading/unloading of mini-apps.  
**FR9.** The mapping of switch values to apps must be configurable via a JSON file.  
**FR10.** The system must provide clean startup and forced shutdown of mini-apps (with timeout).  
**FR11.** The system must log key events and errors for debugging and support.  
**FR12.** The system must be robust to hardware errors and support safe shutdown.  
**FR13.** The system must be extensible for new hardware or app types.  
**FR14.** The system must provide user feedback and status on the 7-inch screen.  
**FR15.** The system must support remote management and configuration over WiFi.  
**FR16.** The system must support future apps that fetch/store data from the internet.  
**FR17.** The system must run on Raspberry Pi OS 64bit Lite (no GUI).  
**FR18.** The system must provide a consistent API for apps to display data on the screen.  
**FR19.** Only a subset of apps will use the speaker for audio output.  
**FR20.** System and apps will use GB English only.

---

## 3. Technical Specification

### 3.1. Architecture Overview ✅ **IMPLEMENTED**
- **Language:** Python 3.11+
- **Platform:** Raspberry Pi OS 64bit Lite (no GUI)
- **Hardware:** RPi, 8 toggle switches (via 74HC151), 7-segment display (TM1637), 7" screen, 4 color buttons, 4 color LEDs, main "Go" button, speaker.
- **Architecture**: Clean Architecture with simplified patterns:
  - **Domain Layer**: Core models, events, and interfaces
  - **Application Layer**: Service classes and event bus (no CQRS)
  - **Infrastructure Layer**: Hardware abstraction (GPIO/WebUI/Mock)
  - **Presentation Layer**: Physical UI, API endpoints (future)
- **Design Patterns:**
  - Dependency Injection for hardware abstraction
  - Simple Event Bus for system communication
  - Factory pattern for hardware implementations
  - App API for hardware isolation
  - Service-oriented design for business logic

### 3.2. System Components

#### 3.2.1. Core Application
- **Entry Point:** `main.py`
- **Responsibilities:**
  - Initialize logger and configuration
  - Initialize hardware interfaces
  - Monitor switches and buttons
  - Manage app lifecycle (start/stop, enforce timeout)
  - Provide API to apps for all hardware and display access
  - Handle errors and logging
  - Manage remote configuration and management interface

#### 3.2.2. Hardware Abstraction Layer
- **Classes:**
  - `SwitchReader`: Reads value from 8 switches via multiplexer (abstracted for future input types)
  - `Button`: Handles debounced input for each button
  - `LED`: Controls each LED
  - `SevenSegmentDisplay`: Controls TM1637 display
  - `Screen`: Abstraction for 7" display output (framebuffer or direct draw)
  - `Speaker`: (Optional) for audio output
- **Design:**
  - All hardware classes implement a common interface for mocking/testing
  - All hardware modules must use try/except for robustness
  - Hardware errors are caught and logged, with fallback to safe state

#### 3.2.3. App Management
- **AppLoader:** Dynamically loads mini-apps as Python modules from a designated directory.
- **AppInterface:** All apps must implement a standard interface (e.g., `run(stop_event, api)`), where `api` is the only way to access hardware/display.
- **AppAPI:** Exposes methods for display, LED, button, and (optionally) network access.
- **AppContext:** Provides apps with access to the API and shared state.
- **App Timeout:** Apps run in threads; forcibly stopped if they exceed allowed runtime.
- **App Manifest:** Each app should provide a minimal JSON or metadata manifest (name, description, hardware used, etc.)
- **Class-based Apps:** Apps should be class-based where possible for maintainability.

#### 3.2.4. Configuration
- **ConfigManager:** Loads and validates configuration from a JSON file (e.g., `BOSSsettings.json`).
- **Mapping:** Switch value → app name → parameters.
- **Remote Management:** Exposes a secure API (REST or similar) for remote configuration and status.
- **Format:** Configuration is stored in JSON, not INI.

#### 3.2.5. Event System
- **EventBus:** Publishes hardware events (button press, switch change) to subscribers (core, apps).

#### 3.2.6. Logging
- **Logger:** Centralized logging to file and console, with log rotation and error levels.

---

### 3.3. Directory Structure

The project directory structure is designed for modularity, scalability, and maintainability. The following layout is recommended:

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
    app_showtext/
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

**Notes:**
- All code is inside the `boss/` package for import clarity and best practice.
- Each app is a subdirectory with its own code, manifest, and optional assets.
- Configuration files are in `config/`.
- Documentation is in `docs/`.
- Utility scripts are in `scripts/`.
- The `tests/` directory mirrors the main package structure for clarity.
- Add `.env.example` and document secret management if environment variables are used.

---

### 3.4. Key Workflows

#### 3.4.1. Startup
1. Initialize logger and configuration.
2. Initialize hardware interfaces.
3. Display current switch value on 7-segment display.
4. Wait for main button press.

#### 3.4.2. App Launch
1. On "Go" button press, read switch value.
2. Lookup app mapping in JSON config.
3. Load and start app in a separate thread, passing API and stop event.
4. Monitor for button presses and forward to app via API.
5. On next "Go" press or timeout, signal app to stop, forcibly terminate if needed, then repeat.

#### 3.4.3. Error Handling
- All hardware and app errors are caught, logged, and trigger safe shutdown or fallback.

#### 3.4.4. Remote Management
- Device connects to WiFi and exposes a secure remote management API for configuration and status.
- Future: Allow remote app configuration, status monitoring, and possibly app upload.

---

### 3.5. Extensibility
- New apps: Drop new `app_*.py` in `apps/` and update config.
- New hardware: Implement new hardware class and register in API.
- New events: Extend event bus and subscribe as needed.
- Future: Apps can fetch/store data from the internet via provided API.
- Support for future OTA (Over-the-Air) app sync and update, with secure fetching from a remote repository.

---

### 3.6. Testing
- **Unit Tests:** For all hardware abstraction and core logic.
- **Integration Tests:** For app loading and lifecycle.
- **Mocking:** Use dependency injection to mock hardware for tests.
- **Emulation:** Support for hardware emulation/mocking for development on Windows or without hardware.
- **CI:** Recommended to use GitHub Actions or similar for automated testing.

---

### 3.7. Security & Safety
- All GPIO access must be validated to prevent hardware damage.
- Configuration files must be validated for correctness.
- System must handle power loss and restart gracefully.
- Remote management API must be authenticated and secure.

---

## 4. Open Questions (Resolved)
1. **App API:** Apps must not access hardware directly; all interaction is via a provided API.
2. **Configuration Format:** Use JSON for all configuration and app mapping.
3. **App Termination:** Apps will be forcibly killed if they exceed a timeout (threaded execution).
4. **User Feedback:** All system and app feedback will be provided on the 7-inch screen.
5. **Remote Management:** Device will be on WiFi and support remote management/configuration.
6. **Localization:** GB English only.
7. **Audio:** Only a subset of apps will use the speaker.
8. **Internet Access:** Future apps may fetch/store data from the internet via the API.

---

## 5. Acceptance Criteria
- All functional requirements are met.
- System is robust to hardware errors and supports clean shutdown.
- New apps can be added without modifying core code.
- Codebase follows modern Python best practices (type hints, docstrings, modularity).
- All core logic is covered by unit tests.
- Documentation is up to date.

---

## 6. Future Improvements & Planned Refactoring
- Refactor to OOP/class-based design for maintainability.
- Wrap all hardware modules in try/except for robustness.
- Convert legacy apps to class-based structure.
- Add more apps and expand configuration.
- Improve shutdown/cleanup logic for running apps.
- Enhance cross-platform support and emulation.
- Define and implement OTA app sync/update.

---
