# B.O.S.S. Backlog – User Stories

## User Roles & Personas
- **Primary User** (e.g., child, museum visitor, educator): Presses buttons, uses switches, runs apps.
- **System Admin** (e.g., technician, facilitator): Manages mappings, handles power/reset, remote config.
- **Developer**: Adds apps, extends system APIs.


This backlog outlines user stories for the B.O.S.S. (Board Of Switches and Screen) project in a logical order of activity. Each story is written in the standard Agile format with a brief description, priority indicator, and acceptance criteria.

---

## 1. Setup & Environment

### US-001: Development Environment & Hardware Emulation
- **As a** developer  
- **I want to** run B.O.S.S. on my Windows laptop using an emulated GPIO environment  
- **So that** I can develop and test the software without requiring physical hardware at all times.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - The system detects when it is running in a non-RPi environment and disables/hides actual hardware calls.  
  - A simulated input module is available that mimics button presses and switch state changes.  
  - Automated tests pass in the emulated environment.
- **Status: Complete.**  (1 and 2) SwitchReader abstraction (with mock) reads the 8-switch value. SevenSegmentDisplay abstraction (with mock) displays the value.
AppManager polls the switch and updates the display when the value changes.
Tests verify that the display updates only when the switch value changes.

### US-002: Initial Hardware Setup & GPIO Initialization
- **As a** developer  
- **I want to** initialize GPIO, buttons, and the display on startup (via `main.py`)  
- **So that** the core system is ready for user interaction as soon as booted.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - On system startup, all hardware interfaces are properly instantiated and logged.  
  - The 7-segment display shows the current switch value immediately.
- **Status: Complete.**

---

## 2. Core User Functionality

### US-003: Toggle Switch Selection
- **As a** user  
- **I want to** use 8 toggle switches to select a number (0–255)  
- **So that** I can choose the mini-app I want to run.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - The multiplexer (74HC151) reads the toggle switches correctly.  
  - The computed number is accurate and displayed immediately on the TM1637 7-segment display.  
  **Status: Complete.** Implemented `SwitchReader` abstraction and polling logic in `AppManager` to read and display the switch value.

### US-004: App Launch (Go Button)
- **As a** user  
- **I want to** press the main "Go" button to launch the mini-app mapped to the current switch value  
- **So that** I have direct control over which mini-app is executed.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - Pressing the "Go" button starts the app selected in configuration.  
  - If an app is running, the "Go" button stops the current app before launching another.  
  **Status: Complete.** Implemented `MockButton` and `GoButtonManager` to handle Go button presses, app launch, and termination. Includes unit tests for button logic.

### US-005: Dynamic App Execution and Termination
- **As a** user  
- **I want to** have the running mini-app terminated upon a new "Go" button press or timeout  
- **So that** I can easily switch between apps without conflicts or lingering processes.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - The app shutdown sequence is executed when the button is pressed again.  
  - In the event of an app exceeding its runtime, it is forcefully terminated and logged.  
  **Status: Complete.** Implemented `AppRunner` to manage app threads, handle stop events, and force termination with logging. Unit tests verify app start, stop, and forced termination behavior.

### US-006: Real-Time Feedback on 7-Segment Display & Screen
- **As a** user  
- **I want to** receive immediate visual feedback on both the 7-segment display and the 7-inch screen  
- **So that** I know the system is correctly registering my inputs and providing status updates.  
- **Priority:** Medium  
- **Acceptance Criteria:**  
  - The 7-segment display updates in real time in response to switch changes.  
  - Status messages and app outputs appear properly on the 7-inch screen.  
  **Status: Complete.** Implemented `MockScreen` abstraction for the 7-inch screen, with methods for status and app output. Unit tests verify real-time feedback logic.

---

## 3. App Interaction & Extensibility

### US-007: Standardized App API & Plugin Structure
- **As a** developer  
- **I want to** have mini-apps load dynamically from the `apps/` directory and follow a standard interface (e.g., `run(stop_event, api)`)  
- **So that** new apps can be added or updated without modifying core code.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - Each app exposes a standard entry function or a class-based interface.
  - A minimal JSON manifest is provided with each app (e.g., `name`, `description`, `hardware used`).
  - The core system successfully loads and runs apps, as shown in integration tests.
- **Status: Complete.** US-007: Added ConfigManager for JSON config management, with tests.

### US-008: App Mapping Configuration via JSON
- **As a** developer  
- **I want to** store the mapping of switch values to mini-apps, including parameters, in a JSON configuration file  
- **So that** configuration is clear, easily editable, and decoupled from the application logic.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - The system reads from a JSON file (e.g., `BOSSsettings.json`) at startup.  
  - Default mappings are generated if the configuration file is missing or malformed.  
  - Changing the JSON file and reloading the system updates the app mappings.
- **Status: Complete.** US-008: Apps can be added as new modules in apps/ (see app_example.py), no core changes required.

---

## 4. Remote Management & Networking

### US-009: Remote Device Management
- **As a** system administrator  
- **I want to** remotely access a secure REST API exposed by the device  
- **So that** I can monitor status, update configuration, and manage running apps without physical access.  
- **Priority:** Medium  
- **Acceptance Criteria:**  
  - A secure REST endpoint is available for device status, app mapping, and log access.  
  - Authentication is enforced on all API endpoints.  
  - Changes made via the API are reflected in the system behavior without requiring a reboot.

### US-010: OTA App Sync & Update (Future Enhancement)
- **As a** system administrator  
- **I want to** have the ability to sync new or updated mini-apps over-the-air  
- **So that** the device can be kept up-to-date without manual intervention.  
- **Priority:** Low (Future Improvement)  
- **Acceptance Criteria:**  
  - A mechanism is in place for securely fetching and updating app modules from a remote repository.  
  - The update process does not interrupt device operation more than necessary.

---

## 5. Testing, Documentation & Developer Experience

### US-011: Unit and Integration Testing for Core Modules
- **As a** developer  
- **I want to** have comprehensive unit tests for hardware abstraction and core logic  
- **So that** changes can be confidently made, and regressions are prevented.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - Unit tests cover all critical components (e.g., `SwitchReader`, `Button`, `LED`).  
  - Integration tests exist for app loading/execution cycles.  
  - Tests run in CI (e.g., via GitHub Actions).
- **Status Complete** US-011: Implemented LED abstraction (with mock for dev) and tests for LED state changes.

### US-012: Documentation and Onboarding Materials
- **As a** new contributor  
- **I want to** have an up-to-date README, architecture overview, and in-code documentation  
- **So that** I can understand the project quickly and contribute effectively.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - A README file provides project setup instructions, dependency lists, and architectural diagrams.  
  - User stories and technical specifications are maintained in docs (e.g., `docs/user-stories.md`).  
  - Code is documented with docstrings and type hints.

### US-013: Developer Tooling and Emulated Inputs for CI
- **As a** developer  
- **I want to** have utility scripts and emulation layers for simulating button presses and switches  
- **So that** I can develop and test the system without constant access to the physical hardware.  
- **Priority:** Medium  
- **Acceptance Criteria:**  
  - Emulation modules are available for GPIO input.  
  - Developer scripts can simulate hardware inputs and verify system responses.

---

## 6. Security, Safety & Robustness

### US-014: Robust Error Handling and Safe Shutdown
- **As a** user  
- **I want to** know that hardware errors or app crashes trigger safe shutdown or fallback states  
- **So that** the device isn't damaged and user data is protected.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - All hardware interfaces use robust try/except mechanisms.
  - Logs capture any errors and provide clear diagnostic information.
  - A safe fallback state is activated on hardware errors.

### US-015: Secure Remote API Authentication
- **As a** system administrator  
- **I want to** authenticate users accessing the remote management API  
- **So that** unauthorized users cannot alter device configurations or retrieve sensitive data.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - All remote API endpoints require secure authentication (e.g., JWT tokens).  
  - API documentation details the authentication process.  
  - Attempts to access endpoints without proper credentials are denied and logged.

### US-016: Central Logging Initialization
- **As a** developer or system administrator  
- **I want to** initialize a central logging facility at system startup  
- **So that** all events, errors, and important actions are recorded for debugging and support.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - Logging is initialized before any hardware or app logic runs.  
  - All modules use the central logger for output.  
  - Log files are rotated and stored persistently.  
  - Logging level can be configured (e.g., debug, info, error).  
  **Status: Complete.** Implemented a central logger with rotation and configurable levels. All startup, shutdown, and error events are logged. Tests verify log output.

### US-017: Clean Shutdown and Resource Cleanup
- **As a** user or system administrator  
- **I want to** ensure the system performs a clean shutdown and resource cleanup (hardware, threads, files) when stopping  
- **So that** hardware is left in a safe state and no data is lost.  
- **Priority:** High  
- **Acceptance Criteria:**  
  - All hardware interfaces are properly closed or reset on shutdown.  
  - Running apps and threads are terminated gracefully.  
  - Any unsaved data is written to disk.  
  - Shutdown events are logged.  
  **Status: Complete.** System startup and shutdown logic added to `main.py`, using the central logger. Cleanup is performed on exit and all actions are logged.



### US-018 document GPIO and apply 
- as a developer
- I want to know how to connect the various components to the Rpi GPIO pins
- so that the components are connected safely and work as expected
- priority high
- acceptance criteria:
	- GPIO connections are documented appropriately (**See: docs.md, RPi-GPIO-Pin-Diagram.md**)
	- GPIO is configured in the application for all components
- additional info: See docs.md for table and wiring notes. See RPi-GPIO-Pin-Diagram.md for full pinout.
- **Status: Complete.**


### US-019 mini-app for displaying random data
- as a user
- I want to select a number for my choice of mini-app. When I press the "go" button, I want see a random joke from a long list of jokes that are stored in the system.
- **Acceptance Criteria:**
    - when I toggle the switches, I see the corresponding number on the 7-segment display
    - when I press the "go" button, I see the joke displayed on the 7-inch screen

#### Implementation Q&A (2025-06-20)
1. **Switch Mapping:**
   - The app should be mapped to a number in `config/BOSSsettings.json`. For this app, use number `001`.
2. **Joke Storage:**
   - The list of jokes will be a JSON file, stored in the relevant app's folder. There should be an `assets` folder under the app's sub-folder. A sample JSON file with temporary jokes will be created for initial testing.
3. **Display:**
   - There will be a requirement to format the text with colour, size, and position in the future. Initially, if no other formats are applied, the text should be centred on the screen and remain until another app is launched.
4. **App Structure:**
   - All mini-apps should follow the same structure that allows them to be run and terminated by BOSS. No additional user interaction at this time, but future enhancements may allow user-triggered results.
5. **Testing:**
   - Tests should detect hardware and use mock or real hardware accordingly.

---

# End of Backlog


---

Old version:

## User Stories
- **US1:** As a user, I want to select a number (0–255) using toggle switches, so I can choose which mini-app to run.
- **US2:** As a user, I want to see the selected number displayed on a 7-segment display.
- **US3:** As a user, I want to press a main "Go" button to launch the mini-app mapped to the selected number.
- **US4:** As a user, I want to interact with the running mini-app using color-coded buttons (Red, Yellow, Green, Blue).
- **US5:** As a user, I want visual feedback from LEDs (Red, Yellow, Green, Blue) during app operation.
- **US6:** As a user, I want to terminate the current mini-app and launch a new one by changing the switch and pressing "Go" again.
- **US7:** As an admin, I want to configure which mini-app is mapped to each switch value, using a JSON configuration file.
- **US8:** As a developer, I want to add new mini-apps easily without modifying the core system.
- **US9:** As a user, I want to see system and app feedback on the 7-inch screen.
- **US10:** As an admin, I want to manage and configure the device remotely over WiFi.




---







