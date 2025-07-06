
# B.O.S.S. (Board Of Switches and Screen) — System Documentation

## Overview
B.O.S.S. is a modular, event-driven Python application for Raspberry Pi, providing a physical interface to select and run mini-apps using 8 toggle switches (0–255), a 7-segment display, 4 color LEDs, 4 color buttons, a main "Go" button, a 7-inch screen, and (optionally) a speaker. The system is designed for extensibility, robust hardware abstraction, and seamless development/testing with or without real hardware.

## Overview
B.O.S.S. is a modular, hardware-interfacing Python application designed to run on a Raspberry Pi (RPi). It provides a physical interface (switches, buttons, dials) to select and run various mini-apps, with outputs to LEDs, a 7-segment display, a screen, and a speaker. The system is portable and intended for interactive use.



## General Usage
1. The user sets the 8 toggle switches to select a number (0–255), which is shown on the 7-segment display.
2. Pressing the main "Go" button launches the mapped mini-app for the current switch value.
3. Mini-apps can use the 7-inch screen, LEDs, and color buttons for interaction, and optionally the speaker.
4. Pressing the "Go" button again stops the current app and launches the app mapped to the new switch value.
5. All hardware and display access by apps is via the provided API, never direct hardware access.

---


## Hardware Architecture
- **Main Controls:**
  - 8 toggle switches (via 74HC151 multiplexer) for 256 input values
  - 4 color buttons (Red, Yellow, Green, Blue) and associated LEDs
  - Main "Go" button
- **Outputs:**
  - 4 color LEDs
  - TM1637 7-segment display
  - 7-inch HDMI screen
  - Speaker (optional)
- **Raspberry Pi GPIO:**
  - Uses `gpiozero` and `pigpio` for hardware abstraction
  - All hardware modules fall back to mocks if not detected, enabling dev/testing on any platform


## GPIO Pin Mapping & Wiring

| Component         | GPIO Pin | Physical Pin | Notes/Colour      |
|------------------|----------|--------------|-------------------|
| btnRed           | 26       | 37           | orange + grey gnd |
| btnYellow        | 19       | 35           | yellow            |
| btnGreen         | 13       | 33           | green             |
| btnBlue          | 6        | 31           | blue              |
| ledRed           | 21       | 40           |                   |
| ledYellow        | 20       | 38           |                   |
| ledGreen         | 16       | 36           |                   |
| ledBlue          | 12       | 32           |                   |
| mainBtn          | 17       | 11           | + gnd             |
| mux1 (C/9)       | 23       | 16           | orange            |
| mux2 (B/10)      | 24       | 18           | yellow            |
| mux3 (A/11)      | 25       | 22           | green             |
| muxIn            | 8        | 24           | blue              |
| TM1637 CLK       | 5        | 29           |                   |
| TM1637 DIO       | 4        | 7            |                   |

See [RPi-GPIO-Pin-Diagram.md](./RPi-GPIO-Pin-Diagram.md) or https://pinout.xyz/ for full pinout.

**Example GPIO setup:**
```python
btnRedpin = 26  # orange   + grey gnd
btnYellowpin = 19  # yellow
btnGreenpin = 13  # green
btnBluepin = 6   # blue
ledRedpin = 21
ledYellowpin = 20
ledGreenpin = 16
ledBluepin = 12
tm = tm1637.TM1637(clk=5, dio=4)
mainBtnpin = 17 # + gnd
mux1pin = 23  # C / 9    orange
mux2pin = 24  # B / 10   yellow
mux3pin = 25  # A / 11   green
muxInpin = 8  #          blue
```

---


## Software Architecture

- **Entry Point:** `main.py`
  - Initializes logging, configuration, and all hardware interfaces (with fallback to mocks)
  - Prints/logs all pin assignments and a hardware startup summary (real/mocked)
  - Loads app mappings from `config/BOSSsettings.json` (auto-generates if missing)
  - Instantiates the event bus and registers all core event types (see [event_schema.md](./event_schema.md))
  - Subscribes display and other handlers to relevant events (e.g., switch changes, button presses)
  - Runs the startup mini-app, then enters the main event-driven loop
  - All hardware events (button, switch, etc.) are published to the event bus; all display/LED/screen updates are event-driven
  - Handles clean shutdown and resource cleanup

- **Configuration:**
  - All app mappings and parameters are in `config/BOSSsettings.json` (JSON)
  - If missing, auto-generated with defaults
  - Validated at startup

- **App Management:**
  - Apps are Python modules or packages under `apps/`, each with a standard interface (`run(stop_event, api)`)
  - Dynamically loaded and run in threads (with forced termination on timeout)
  - App lifecycle events are published to the event bus
  - Apps interact with hardware only via the provided API object

- **Event Bus:**
  - Central event bus (`core/event_bus.py`) for all hardware, system, and app events
  - Supports publish/subscribe, event filtering, async/sync delivery, and custom event types
  - All hardware and app events are logged for auditing

- **Hardware Abstraction:**
  - All hardware (buttons, LEDs, display, screen, speaker) is abstracted in `hardware/` with real and mock implementations
  - Hardware errors are caught and logged; system falls back to mocks for seamless dev/testing

- **Display:**
  - TM1637 7-segment display shows current switch value or status messages
  - All updates are event-driven (no polling)

- **Remote Management:**
  - Secure API for remote configuration and status (see `core/remote.py`)

- **Testing:**
  - All core and hardware modules are unit/integration tested with mocks (see `tests/`)


---


## Supported Mini-Apps (Examples)
- Matrix screensaver
- Display photos (grouped)
- Play sounds (birds, songs, movie quotes)
- LED/LED strip control (patterns, color, brightness)
- Simple games (e.g., guess the number)
- Display quotes, movie clips, test patterns, clock, weather, text-to-speech, fractals, text

---


## Development & Deployment

- **Setup:**
  - Designed for Raspberry Pi OS 64bit Lite (no GUI)
  - Use Python 3.11+ and a virtual environment
  - Install dependencies: `gpiozero`, `pigpio`, `python-tm1637`, `pytest`, `Pillow`, `numpy`, etc.
  - All configuration is in `config/BOSSsettings.json`
  - For Windows/dev, hardware is mocked automatically

- **Startup:**
  - Run from project root: `python3 -m boss.main`
  - Open the Web UI debug dashboard at [http://localhost:8070/](http://localhost:8070/) for live hardware and event inspection
  - Can be started manually or as a systemd service (see `docs/install-steps.md`)

- **Testing:**
  - Use `pytest` for all tests (see `tests/`)
  - All hardware is mocked for tests
  - Run tests with `pytest` and coverage


---


## Directory Structure & Best Practices

The project is organized for modularity, scalability, and maintainability:

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

**Best Practices:**
- All code is inside the `boss/` package for import clarity
- Each app is a subdirectory with its own code, manifest, and assets
- All configuration is in `config/`
- All documentation is in `docs/`
- All tests are in `tests/`, mirroring the main structure
- Use dependency injection and mocks for all hardware in tests
- Use type hints and docstrings throughout
- All hardware and display access by apps is via the provided API only

---


## Notable Implementation Details

- **Multiplexer Reading:**
  - 8 toggle switches are read using a 74HC151 multiplexer (4 GPIO pins)
  - `SwitchReader` abstraction allows for future input types (dial, keypad, etc.)

- **Event-Driven Architecture:**
  - All hardware and app events are published to the event bus
  - Display and other outputs are updated only in response to events (no polling)

- **Threading:**
  - Mini-apps run in their own thread, with forced termination on timeout
  - Clean shutdown via `stop_event`

- **Extensibility:**
  - New apps: add new module/package in `apps/` and update config
  - New hardware: extend hardware abstraction layer
  - New events: register new event types with the event bus

- **Cross-Platform:**
  - Hardware is auto-mocked for dev/testing on Windows or without hardware

---


## Mini-App Structure & Assets

Each mini-app is a subdirectory under `apps/`, e.g.:

```
apps/
  app_jokes/
    __init__.py
    main.py
    manifest.json
    assets/
      jokes.json
```

- **main.py**: Entry point, must implement `run(stop_event, api)`
- **manifest.json**: Metadata (name, description, etc.)
- **assets/**: Data files (e.g., `jokes.json`)

**Example `jokes.json`:**
```json
{
  "jokes": [
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break, and it said 'No problem, I'll go to sleep.'"
  ]
}
```

- Apps load assets at runtime and use the API for all hardware/display access
- All mini-apps and tests use real or mock hardware as appropriate

---


## References
- See `docs/BOSS-devnotes.md` for hardware datasheets, Python docs, GPIOZero, threading, and more

---


## Summary
B.O.S.S. is a robust, extensible, event-driven Python system for Raspberry Pi, enabling physical selection and execution of mini-apps via switches, buttons, LEDs, and display. It is modular, testable, and designed for both real hardware and seamless development/testing on any platform.

---
bash
bash
bash
bash
bash

## Issues & Troubleshooting

### WiFi Setup on Latest Raspberry Pi OS
The Raspberry Pi Imager configures WiFi with wpa_supplicant, but the latest OS uses Network Manager. If WiFi does not work on first boot:

1. Unblock Wi-Fi:
   ```bash
   sudo rfkill unblock wifi
   ```
2. Enable Wi-Fi radio:
   ```bash
   nmcli radio wifi on
   ```
3. (Optional) Restart NetworkManager:
   ```bash
   sudo systemctl restart NetworkManager
   ```
4. Confirm interface:
   ```bash
   nmcli device status
   ```
   You should see `wlan0` as “disconnected” (ready).
5. Connect to Wi-Fi:
   - Text UI: `sudo nmtui`
   - Or CLI:
     ```bash
     nmcli device wifi list
     nmcli device wifi connect "YourSSID" password "YourPassword"
     ```

### VSCode Remote Troubleshooting
If VSCode remote server is stuck:
```bash
ls -la
rm -rf ~/.vscode-server
rm -rf ~/.cache
rm -rf ~/.config
```


