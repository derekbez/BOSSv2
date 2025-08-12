# B.O.S.S. (Board Of Switches and Screen)

B.O.S.S. is a modular, hardware-driven Python application designed for Raspberry Pi (64-bit Lite OS, no GUI). It allows users to physically select and run mini-apps using toggle switches, buttons, LEDs, a 7-inch screen, and an optional speaker.

## 🔧 Features

- Select apps using **8 toggle switches** (via 74HC151 multiplexer)
- Display selected value on a **TM1637 7-segment display**
- Press a **main "Go" button** to launch mini-apps
- Interact with apps via **color-coded buttons and LEDs** (Red, Yellow, Green, Blue)
- Display output on a **7-inch screen**
- Optional **speaker support** for audio-based apps
- Easy-to-extend app plugin structure (`apps/app_*.py`)
- Remote management via a **secure REST API**
- Emulated mode for development on non-RPi systems


## 🚀 Getting Started

1. Clone this repo:
   ```bash
   git clone https://github.com/derekbez/BOSSv2.git
   cd BOSSv2
   ```

2. Set up Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements/base.txt -r requirements/dev.txt
   ```

3. Configure switch-to-app mappings in `BOSSsettings.json`

4. Run the app (from the project root):
   ```bash
   source boss-venv/bin/activate
   python3 -m boss.main
   ```

5. Open the Web UI debug dashboard in your browser:
   ```
   http://localhost:8070/
   ```

## 🛩️ Mini-App Examples

Mini-apps can be anything—simple games, jokes, fractal displays, soundboards, clocks, text-to-speech, or interactive toys.

Each app should implement:
```python
def run(stop_event, api):
    ...
```

## 📁 Project Structure

- `main.py` – System startup and core loop
- `apps/` – Mini-app modules
- `core/` – Core services (config, app manager, API)
- `hardware/` – GPIO hardware abstractions
- `assets/` – Images, sounds, etc.
- `tests/` – Unit and integration tests
- `docs/` – Documentation and developer notes

## ✅ Requirements

- Raspberry Pi with 64-bit Lite OS
- Python 3.11+
- GPIO libraries: `gpiozero`, `pigpio`, `rpi-tm1637`, etc.
- Virtual environment recommended

---

More detailed usage, hardware wiring diagrams, and developer guides will be added as the project evolves. Stay tuned!
