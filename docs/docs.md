# B.O.S.S. (Board Of Switches and Screen) Deep Dive Analysis

## Overview
B.O.S.S. is a modular, hardware-interfacing Python application designed to run on a Raspberry Pi (RPi). It provides a physical interface (switches, buttons, dials) to select and run various mini-apps, with outputs to LEDs, a 7-segment display, a screen, and a speaker. The system is portable and intended for interactive use.


## General Useage
A user will use the eight toggle switches to select a number (0 - 255).  The number is shown on the 7-segemnt display.
The user may press the main "go" button, and BOSS will run the mini-app associated with the number chosen.
The mini-app can display on the 7-inch screen, and use the LEDs (Red, Yellow, Green, Blue). The user can interact with mini-app with the additional buttons (Red, Yellow, Green, Blue).
If the user presses the main "go" button again, the mini-app terminates and BOSS runs the mini-app associated with the toggle switches number.

---

## Hardware Architecture
- **Main Controls:**
  - 8 toggle switches (via 74HC151 multiplexer) provide 256 unique input combinations.
  - Additional buttons (Red, Yellow, Green, Blue) and associated LEDs.
  - Main button for selection/activation.
- **Outputs:**
  - LEDs 
  - 7-segment display (TM1637)
  - 7-inch screen
  - Speaker
- **Raspberry Pi GPIO:**
  - GPIOZero library for hardware abstraction.
  - PiGPIOFactory for remote GPIO support.

---

## Software Architecture
- **Entry Point:** `start.py`
  - Initializes GPIO, buttons, and display.
  - Loads or creates a configuration file (`BOSSsettings.conf`) mapping switch positions to apps.
  - Waits for user input (main button press) to select and launch an app.
  - Dynamically loads and runs apps in a separate thread.
  - Handles clean-up and display updates on exit.

- **Configuration:**
  - `BOSSsettings.conf` stores mappings: binary switch value → decimal → app name → parameters.
  - If missing or empty, it is auto-generated with default values.
  - Uses `configparser` for reading/writing.

- **App Management:**
  - Apps are Python modules named `app_<name>.py` (e.g., `app_matrixrain.py`).
  - Dynamically imported and executed via threading (previously supported multiprocessing).
  - Each app must have a `main(stop_event, params)` function for compatibility.
  - Apps are stopped by setting a threading event.

- **Utilities:**
  - `ConfigButtons.py`: Handles button/LED initialization and control.
  - `intervaltimer.py`: Provides `IntervalTimer` and `RepeatedTimer` for periodic tasks (e.g., updating the display).
  - `leddisplay.py`: (not shown) likely handles 7-segment display abstraction.

- **Display:**
  - TM1637 7-segment display is used for showing the current switch value or status messages.
  - Display is initialized only on RPi (not on Windows for dev/testing).

- **Dynamic Import:**
  - Uses `importlib.util` to load app modules at runtime based on switch selection.

---

## Supported Apps (Examples)
- Matrix screensaver
- Display photos (grouped)
- Play sounds (birds, songs, movie quotes)
- LED/LED strip control (patterns, color, brightness)
- Simple games (e.g., guess the number)
- Display quotes, movie clips, test patterns, clock, weather, text-to-speech, fractals, text

---

## Development & Deployment
- **Setup:**
  - Designed for RPi OS (Raspbian Lite recommended).
  - Uses Python virtual environments (`venv`).
  - Supports both local and remote GPIO (for dev on Windows, run pigpio daemon on RPi).
  - Install dependencies: `gpiozero`, `pigpio`, `pygame`, `blessed`, `windows-curses` (for Windows dev), `rpi-tm1637`.
- **Startup:**
  - Can be started manually or via systemd service for auto-boot.
  - Example systemd unit file provided in dev notes.
- **Testing:**
  - Includes test scripts and archived experiments.
  - GPIO emulation/simulation is possible for dev without hardware.

---

## Directory Structure & Best Practices

The recommended directory structure for B.O.S.S. is designed for modularity, scalability, and maintainability:

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

**Key Points:**
- All code is inside the `boss/` package for import clarity and best practice.
- Each app is a subdirectory with its own code, manifest, and optional assets.
- Configuration files are in `config/`.
- Documentation is in `docs/`.
- Utility scripts are in `scripts/`.
- The `tests/` directory mirrors the main package structure for clarity.
- Add `.env.example` and document secret management if environment variables are used.

---

## Notable Implementation Details
- **Multiplexer Reading:**
  - 8 toggle switches are read using a 74HC151 multiplexer, reducing GPIO usage to 4 pins.
  - `ReadMux()` function cycles through channels, sets select lines, and reads the output to build a binary number.
- **Threading:**
  - Apps run in their own thread, allowing main loop to remain responsive.
  - Clean shutdown via `stop_event`.
- **Extensibility:**
  - New apps can be added by creating new `app_<name>.py` modules.
  - Configuration file can be edited to map switch positions to new apps.
- **Cross-Platform:**
  - Code checks for RPi environment and disables hardware features on Windows for development.

---

## References
- Extensive links to hardware datasheets, Python docs, GPIOZero, pygame, threading, and more in `BOSS-devnotes.md` (TODO).

---

## Summary
B.O.S.S. is a flexible, extensible, and hardware-focused Python application for the Raspberry Pi, enabling physical selection and execution of a wide variety of mini-apps. It is well-documented, modular, and designed for both development and deployment on real hardware.