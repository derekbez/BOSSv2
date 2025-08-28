## B.O.S.S. Install Guide (Raspberry Pi + Windows Dev)

This guide sets up B.O.S.S. on a Raspberry Pi for production and on Windows for WebUI development. Dependencies are centralized in requirements/base.txt and requirements/dev.txt.

Important: The screen backend is now simplified to 'textual' (Rich-based). The older Pillow and selectable Rich modes have been removed for maintenance simplicity.

### Raspberry Pi Setup (64-bit Lite OS)

1) Update system and install prerequisites (includes lgpio)
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv python3-dev build-essential \
	pkg-config libffi-dev fontconfig python3-lgpio
```



2) Clone repo and create venv
```
cd ~
git clone https://github.com/derekbez/BOSSv2.git boss
cd boss
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

3) Install Python packages
```
pip install -r requirements/base.txt -r requirements/dev.txt
```

4) GPIO backend (recommended)
- Set GPIOZERO_PIN_FACTORY=lgpio in your service environment (see scripts/boss-dev.service)

5) Optional: pigpio daemon (only if you need pigpio-specific features)
- sudo apt install -y pigpio
- sudo systemctl enable --now pigpiod  # optional

6) Power button overlay (optional; adjust pins as needed)
- echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt

7) First run (without systemd)
- source ~/boss/boss-venv/bin/activate
- python3 -m boss.main

8) Install as a service (recommended on Pi)
```
chmod +x scripts/setup_systemd_service.sh
./scripts/setup_systemd_service.sh
sudo systemctl start boss && sudo journalctl -u boss -f
```

Screen geometry note (HDMI): Ensure screen_width and screen_height in boss/config/boss_config.json match the framebuffer. Check with: fbset -fb /dev/fb0 -i

Legacy backends (Pillow/Rich) have been removed from selection; keep your config at "textual" or "auto" (auto currently resolves to textual).

### Windows WebUI Development (CMD)

1) Create a virtual environment in the repo
- cd \path\to\BOSSv2
- py -3 -m venv .venv
- .\.venv\Scripts\activate

2) Install dependencies
- pip install -r requirements/base.txt -r requirements/dev.txt

3) Verify WebUI server deps
- python -c "import uvicorn, fastapi; print('uvicorn', uvicorn.__version__)"
	- If missing, install: pip install -r requirements/dev.txt

4) Run with WebUI hardware emulation
- python -m boss.main --hardware webui

5) Change screen backend (optional)
- System-wide: edit boss/config/boss_config.json → hardware.screen_backend: "textual" | "auto" (auto resolves to textual)
- Per app: set preferred_screen_backend in the app's manifest.json

++++++++++

#!/bin/bash

# Exit on error
set -e

echo "📦 Cloning repo..."
cd ~
git clone https://github.com/derekbez/BOSSv2.git boss
cd boss

echo "🐍 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

echo "🔧 Installing direnv..."
sudo apt update
sudo apt install -y direnv

echo "🔗 Adding direnv hook to shell config..."
SHELL_RC="$HOME/.bashrc"
[[ "$SHELL" == *zsh ]] && SHELL_RC="$HOME/.zshrc"

if ! grep -q 'eval "$(direnv hook' "$SHELL_RC"; then
    echo 'eval "$(direnv hook bash)"' >> "$SHELL_RC"
fi

echo "📝 Creating .envrc for auto-activation..."
echo 'source .venv/bin/activate' > .envrc
direnv allow

echo "✅ Setup complete. Your virtual environment will auto-activate when you enter ~/boss"





