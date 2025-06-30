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

## GPIO Pin Mapping & Wiring

The following table summarizes the GPIO pin assignments for B.O.S.S. components:

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

- For a full pinout, see: [RPi-GPIO-Pin-Diagram.md](./RPi-GPIO-Pin-Diagram.md) or https://pinout.xyz/
- All grounds (GND) must be connected as per the diagram.
- Wire colours in comments are for reference to the physical build.

### Example GPIO Setup in Code
```python
btnRedpin = 26  # orange   + grey grd
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
mux3pin = 25  # A / 11    green
muxInpin = 8  #           blue
```

---

## Software Architecture
- **Entry Point:** `main.py`
  - Initializes GPIO, buttons, and display.
  - Loads or creates a configuration file (`BOSSsettings.json`) mapping switch positions to apps.
  - Waits for user input (main button press) to select and launch an app.
  - Dynamically loads and runs apps in a separate thread.
  - Handles clean-up and display updates on exit.
  - **At startup, the system prints/logs all pin assignments and a hardware startup summary, indicating which devices are real or mocked.**
  - **Each hardware device (button, LED, display, etc.) falls back to a mock if not detected, allowing seamless development and testing without hardware.**

- **Configuration:**
  - `BOSSsettings.json` stores mappings: binary switch value → decimal → app name → parameters.
  - If missing or empty, it is auto-generated with default values.
  - Uses JSON for reading/writing.

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

## Mini-App Structure & Assets

Each mini-app should be placed in its own subdirectory under `apps/`, following this structure:

```
apps/
  app_jokes/
    __init__.py
    main.py
    manifest.json
    assets/
      jokes.json
```

- **main.py**: Entry point for the mini-app, must follow the standard interface (e.g., `run(stop_event, api)`).
- **manifest.json**: Metadata about the app (name, description, etc.).
- **assets/**: Folder for any data files (e.g., `jokes.json`).
- **jokes.json**: JSON file containing a list of jokes for the random joke app.

### Example `jokes.json` format
```json
{
  "jokes": [
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break, and it said 'No problem, I'll go to sleep.'"
  ]
}
```

- The app should load this file at runtime and select a random joke to display.
- Future formatting (colour, size, position) can be added to the JSON or handled in code.

### Hardware/Mock Testing
- All mini-apps and tests should detect hardware and use mock or real hardware accordingly.

---

## References
- Extensive links to hardware datasheets, Python docs, GPIOZero, pygame, threading, and more in `BOSS-devnotes.md` (TODO).

---

## Summary
B.O.S.S. is a flexible, extensible, and hardware-focused Python application for the Raspberry Pi, enabling physical selection and execution of a wide variety of mini-apps. It is well-documented, modular, and designed for both development and deployment on real hardware.

---
## Issues
When imaging an SD Card from Raspberry Pi Imager with RPI OS 64bit Lite, the imager seems to configure the wifi with wpa_supplicant, but the latest OS is using Network Manager.   Wifi does not get set up when booting the rpi for the first time.

Unblocked Wi-Fi via rfkill:

bash
`sudo rfkill unblock wifi`

Enabled Wi-Fi radio with nmcli:

bash
`nmcli radio wifi on`

(Optional) Restarted NetworkManager to refresh device status:

bash
`sudo systemctl restart NetworkManager`

Confirmed the interface was available:

bash
`nmcli device status`

You should see wlan0 listed as “disconnected” (which is good—it means it’s ready).

Connected to Wi-Fi using nmtui or nmcli:

`sudo nmtui` for a text-based UI

Or:

bash
`nmcli device wifi list`
`nmcli device wifi connect "YourSSID" password "YourPassword"`

+++
When VSCode stuggles:
`ls -la`
`rm -rf ~/.vscode-server`
`rm -rf ~/.cache`
`rm -rf ~/.config`


