
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
  - Uses `gpiozero` and `lgpio` for hardware abstraction
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
  - Loads app mappings 
  - Instantiates the event bus and registers all core event types (see [event_schema.md](./event_schema.md))
  - Subscribes display and other handlers to relevant events (e.g., switch changes, button presses)
  - Runs the startup mini-app, then enters the main event-driven loop
  - All hardware events (button, switch, etc.) are published to the event bus; all display/LED/screen updates are event-driven
  - Handles clean shutdown and resource cleanup

- **Configuration:**
  - System configuration is in `boss/config/boss_config.json` (hardware pins, system settings)
  - App mappings are in `boss/config/app_mappings.json` (switch-to-app assignments)
  - Configuration is co-located with the main code for modularity
  - If missing, auto-generated with defaults and validated at startup

- **App Management:**
  - Apps are Python modules or packages under `apps/`, each with a standard interface (`run(stop_event, api)`)
  - Dynamically loaded and run in threads (with forced termination on timeout)
  - App lifecycle events are published to the event bus
  - Apps interact with hardware only via the provided API object

- **Event Bus:**
  - Central event bus (`application/events/event_bus.py`) for all hardware, system, and app events
  - Supports publish/subscribe, event filtering, async/sync delivery, and custom event types
  - All hardware and app events are logged for auditing

- **Hardware Abstraction:**
  - All hardware (buttons, LEDs, display, screen, speaker) is abstracted in `infrastructure/hardware/` with real, WebUI and mock implementations
  - Hardware errors are caught and logged; system falls back to mocks for seamless dev/testing

- **Display:**
  - TM1637 7-segment display shows current switch value or status messages
  - HDMI screen output 
  - All updates are event-driven (no polling)

- **Remote Management:**
  - Secure API for remote configuration and status (see `core/remote.py`)

- **Testing:**
  - All core and hardware modules are unit/integration tested with mocks (see `tests/`)


---


## Supported Mini-Apps (Examples)
- Matrix screensaver
- Simple games (e.g., guess the number)
- Display quotes, movie clips, test patterns, clock, weather, text-to-speech, fractals, text

---


## Development & Deployment

- **Setup:**
  - Designed for Raspberry Pi OS Lite (no GUI)
  - Use Python 3.11+ and a virtual environment
  - Install dependencies: `gpiozero`, `lgpio`, `python-tm1637`, `pytest`, `rich`, `textual` (Pillow optional/legacy)
  - All configuration is in `boss/config/` (co-located with main code)
  - For Windows/dev, hardware is mocked automatically

- **Startup:**
  - **Production Hardware**: Use systemd service for reliability:
    ```bash
    sudo systemctl start boss
    sudo journalctl -u boss -f
    ```
  - **Remote Development**: Manage from Windows/VSCode:
    ```bash
    python scripts/boss_remote_manager.py
    ```
  - **Local Testing**: Run directly for development/testing:
    ```bash
    cd ~/boss
    python3 -m boss.main
    ```
  - Configuration is automatically loaded from `boss/config/boss_config.json`
  - App mappings are loaded from `boss/config/app_mappings.json`
  - Open the Web UI debug dashboard at [http://localhost:8080/](http://localhost:8080/) for live hardware and event inspection (when webui hardware mode is enabled)
  - Can be started manually or as a systemd service (see `docs/remote_development.md`)

- **Testing:**
  - Use `pytest` for all tests (see `tests/`)
  - All hardware is mocked for tests
  - Run tests with `pytest` and coverage

> `https://pypi.org/project/python-tm1637/`
---


## Screen troubleshooting (real hardware)

If LEDs work but nothing appears on the HDMI screen after starting the service:

1) Verify framebuffer and geometry
- Check that /dev/fb0 exists and note its geometry and bpp:
  ```bash
  ls -la /dev/fb0
  fbset -fb /dev/fb0 -i
  cat /sys/class/graphics/fb0/virtual_size
  cat /sys/class/graphics/fb0/bits_per_pixel
  ```
- Ensure boss/config/boss_config.json matches the framebuffer size (screen_width, screen_height). If they differ, update the config and restart the service.

2) (Legacy) Pillow framebuffer backend
- Only enable if you specifically need direct framebuffer image drawing.
- In boss/config/boss_config.json set:
  ```json
  "screen_backend": "pillow"
  ```
- Deprecated: prefer the textual backend for simplicity and robustness.

3) Confirm permissions and service config
- The service/user must have video group access to write /dev/fb0:
  ```bash
  groups
  # Expect to see: gpio video audio
  ```
- The systemd unit should include:
  - Group=gpio
  - SupplementaryGroups=video audio

4) Restart and watch logs
```bash
sudo systemctl restart boss
sudo journalctl -u boss -n 100 -f
```
You should see lines like:
- TextualScreen initialized (textual backend)
- Detected framebuffer size: WxH
- Screen updated: text

5) Quick screen test (optional)
- Run the included test script to draw to the framebuffer:
  ```bash
  python3 scripts/test_pillow_screen.py
  ```
  If this shows text but the service does not, compare logs and config.

6) Console overlay notes
- The Linux login console may still be visible; Pillow writes directly over it. If you never see updates, double-check bpp and geometry, and that the service logs no framebuffer write errors.

If issues persist, capture the last 200 lines of the boss journal and the outputs of fbset and share them.




**Best Practices:**
- **Clean Architecture:** Layer separation (Presentation, Application, Domain, Infrastructure) with dependency inversion
- **Co-location:** All code, config, and mini-apps are inside the `boss/` package for import clarity and modularity
- **Configuration:** All system configuration is in `boss/config/` - no external config directories
- **Mini-apps:** All mini-apps are in `boss/apps/` with standardized structure (main.py, manifest.json, assets/)
- **Testing:** All tests are in `tests/`, mirroring the main structure with mocks for hardware
- **Type Safety:** Use type hints and docstrings throughout for clarity and maintainability
- **Event-Driven:** All hardware and app events use the event bus - no direct hardware access in apps
- **Hardware Abstraction:** Real, WebUI, and mock implementations enable dev/testing on any platform

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


## Mini-App Structure & Configuration

### Mini-App Directory Structure
Each mini-app is a subdirectory under `boss/apps/`, e.g.:

```
boss/apps/
  list_all_apps/           # System app for browsing available apps
    __init__.py
    main.py               # Entry point with run(stop_event, api)
    manifest.json         # App metadata and configuration
    assets/               # Optional: images, sounds, data files
  hello_world/            # Example basic app
    main.py
    manifest.json
  current_weather/        # Example network-enabled app
    main.py
    manifest.json
    assets/
      weather_icons/
```

### Manifest File Structure
Apps use `manifest.json` for metadata. The system supports two formats:

**Standard Format (Recommended):**
```json
{
  "name": "Hello World",
  "description": "Simple hello world app demonstrating event-driven API",
  "version": "1.0.0",
  "author": "BOSS Team",
  "entry_point": "main.py",
  "timeout_seconds": 60,
  "requires_network": false,
  "requires_audio": false,
  "tags": ["example", "basic"]
}
```

**Legacy Format (Auto-converted):**
```json
{
  "id": "list_all_apps",
  "title": "Mini-App Directory Viewer",
  "description": "Displays a paginated list of all available mini-apps",
  "entry_point": "main.py",
  "config": {
    "entries_per_page": 15
  },
  "instructions": "Uses yellow/blue buttons for navigation"
}
```

### Configuration Files

**System Configuration (`boss/config/boss_config.json`):**
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
    "log_file": "logs/boss.log",
    "event_queue_size": 1000,
    "app_timeout_seconds": 300
  }
}
```

**App Mappings (`boss/config/app_mappings.json`):**
```json
{
  "app_mappings": {
    "0": "list_all_apps",
    "1": "hello_world",
    "8": "joke_of_the_moment",
    "10": "current_weather",
    "252": "admin_wifi_configuration",
    "254": "admin_boss_admin", 
    "255": "admin_shutdown"
  },
  "parameters": {}
}
```

### App Development Notes
- Apps load assets at runtime using `api.get_asset_path("filename")`
- All hardware/display access must use the provided API object
- Apps run in separate threads with clean shutdown via `stop_event`
- Both standard and legacy manifest formats are supported with auto-conversion
- Use the `boss/apps/app_template/` directory as a starting point for new apps

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


