# Remote Development & Debugging Guide for B.O.S.S.

This guide shows how to develop and debug B.O.S.S. from Windows/VSCode while running on a Raspberry Pi as a systemd service. It uses centralized requirements, recommends lgpio, and defaults the screen backend to "rich".

## Overview
- Service managed by systemd on the Pi (auto-restart, proper groups)
- Remote manager script from Windows (start/stop/logs/deploy)
- Live logs via journalctl
- Hardware access via gpio/video/audio groups

## Quick Start

### 1) Raspberry Pi setup
```bash
# Clone and set up the project
cd ~
git clone https://github.com/derekbez/BOSSv2.git boss
cd boss

# Create and activate venv
python3 -m venv boss-venv
source boss-venv/bin/activate
python -m pip install --upgrade pip

# Install Python dependencies (centralized files)
pip install -r requirements/base.txt -r requirements/dev.txt

# Install lgpio backend for GPIOZero (recommended)
sudo apt install -y python3-lgpio

# Install as a service (adds proper groups and config)
chmod +x scripts/setup_systemd_service.sh
./scripts/setup_systemd_service.sh

# Reboot to ensure group changes are applied
sudo reboot
```

### 2) Service commands (on the Pi)
```bash
sudo systemctl start boss
sudo systemctl status boss
sudo journalctl -u boss -f
```

### 3) Windows/VSCode remote manager
```bat
:: Optional: create a venv for running the manager locally
py -3 -m venv .venv
.\.venv\Scripts\activate

:: Run the remote manager from the repo root
python scripts\boss_remote_manager.py

:: Quick commands
python scripts\boss_remote_manager.py status
python scripts\boss_remote_manager.py restart
python scripts\boss_remote_manager.py logs
```

## Configuration files (on the Pi)
- Main config: /home/rpi/boss/boss/config/boss_config.json
- App mappings: /home/rpi/boss/boss/config/app_mappings.json

Notes
- Default screen backend is "rich". To switch globally: set hardware.screen_backend to "pillow" in boss_config.json. Per-app override via manifest preferred_screen_backend.
- For HDMI output, ensure boss_config.json screen_width/screen_height match framebuffer geometry (fbset -fb /dev/fb0 -i).

## Troubleshooting

### Service won’t start
```bash
sudo systemctl status boss
sudo journalctl -u boss -n 50
```
Common causes: invalid config, missing groups, bad Python env, busy GPIO.

### Permission issues
```bash
groups
sudo usermod -a -G gpio,video,audio $USER
# log out/in or reboot
```

### GPIO/Hardware not working
```bash
ls -la /dev/gpiomem   # should be readable by gpio group
ls -la /dev/fb0       # should be readable by video group
sudo apt install -y python3-lgpio
```

### Display issues
```bash
fbset -fb /dev/fb0 -i
cat boss/config/boss_config.json | grep -E "screen_(width|height)"
```
Ensure config resolution matches framebuffer.

### Remote manager SSH setup
Use key auth; see docs/ssh_authentication_setup.md. Test:
```bash
ssh rpi@your-pi-hostname
```

## VSCode helpers

### PowerShell aliases (optional)
```powershell
function boss-start { python scripts/boss_remote_manager.py start }
function boss-stop { python scripts/boss_remote_manager.py stop }
function boss-restart { python scripts/boss_remote_manager.py restart }
function boss-status { python scripts/boss_remote_manager.py status }
function boss-logs { python scripts/boss_remote_manager.py logs }
function boss-console { python scripts/boss_remote_manager.py }
```

### tasks.json snippets
```json
{
    "version": "2.0.0",
    "tasks": [
        { "label": "BOSS: Restart Service", "type": "shell", "command": "python", "args": ["scripts/boss_remote_manager.py", "restart"], "group": "build" },
        { "label": "BOSS: Show Logs", "type": "shell", "command": "python", "args": ["scripts/boss_remote_manager.py", "logs"], "group": "test" }
    ]
}
```

## Best practices
- Use the service for hardware testing; avoid ad-hoc runs
- Watch logs while iterating
- Test components individually first
- Keep changes small; commit often
- Validate config and pin assignments

That’s it. You’re ready to develop on Windows and run on the Pi.
