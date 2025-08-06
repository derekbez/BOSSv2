# Remote Development & Debugging Guide for B.O.S.S.
### **On Windows (VSCode Terminal):**
```bash
# Copy the scr### **Windows Setup**
1. Copy `scripts/boss_remote_manager.py` to your Windows development machine
2. **Setup SSH Authentication** (see `docs/ssh_a#### 5. Remote Manager Connection Issues
```bash
# Test SSH connection manually
ssh rpi@your-pi-hostname

# Setup SSH keys if connection fails
python scripts/boss_remote_manager.py ssh-setup

# Update RPI_HOST in boss_remote_manager.py
# Ensure SSH key authentication is configured (see docs/ssh_authentication_setup.md)
```ion_setup.md` for complete guide):
   ```bash
   # Generate SSH key
   ssh-keygen -t rsa -b 4096
   
   # Copy to Pi
   ssh-copy-id rpi@192.168.1.100
   ```
3. Update the `RPI_HOST` variable to match your Pi's SSH connection string:
   ```python
   RPI_HOST = "rpi@192.168.1.100"  # Your Pi's IP or hostname
   ```
4. Test connection: `ssh rpi@192.168.1.100` (should connect without password)your local machine
# Update RPI_HOST in the script to match your Pi's SSH connection string
# Setup SSH key authentication (see docs/ssh_authentication_setup.md)

# Run interactively
python scripts/boss_remote_manager.py

# Or use quick commands
python scripts/boss_remote_manager.py start
python scripts/boss_remote_manager.py status
python scripts/boss_remote_manager.py logs
```e covers how to develop, test, and debug the B.O.S.S. application remotely over SSH from Windows/VSCode while running on real Raspberry Pi hardware.

## Overview

The B.O.S.S. remote development setup provides:
- **Systemd Service**: Runs BOSS as a robust system service with auto-restart and proper permissions
- **Remote Management**: Windows script to control the service from VSCode terminal
- **Live Monitoring**: Real-time logs and status monitoring over SSH
- **Hardware Access**: Proper group permissions for GPIO, framebuffer, and audio devices
- **Development Workflow**: Deploy, test, and debug cycle optimized for remote work

## Quick Start

### 1. Initial Setup (on Raspberry Pi)
```bash
# Clone and setup the project
cd ~
git clone https://github.com/derekbez/BOSSv2.git boss
cd boss

# Create virtual environment
python3 -m venv boss-venv
source boss-venv/bin/activate
pip install -r requirements.txt

# Install lgpio for optimal GPIO performance
pip install lgpio

# Setup systemd service (adds user to gpio/video/audio groups)
chmod +x scripts/setup_systemd_service.sh
./scripts/setup_systemd_service.sh

# Logout and login (or restart) to apply group changes
sudo reboot
```

### 2. Start the Service
```bash
# Start BOSS service
sudo systemctl start boss

# Check status
sudo systemctl status boss

# View live logs
sudo journalctl -u boss -f
```

### 3. Remote Management from Windows/VSCode
```bash
# Copy boss_remote_manager.py to your local Windows machine
# Update RPI_HOST in the script to match your Pi's SSH details

# Run the remote manager
python scripts/boss_remote_manager.py

# Or use quick commands
python scripts/boss_remote_manager.py status
python scripts/boss_remote_manager.py restart
python scripts/boss_remote_manager.py logs
```

## Systemd Service Details

### Service Configuration
- **User**: `rpi` (configurable in setup script)
- **Groups**: `gpio`, `video`, `audio` for hardware access
- **Working Directory**: `/home/rpi/boss`
- **Virtual Environment**: `boss-venv/bin/python`
- **Auto-restart**: Yes, with rate limiting
- **Boot Start**: Enabled by default
- **Resource Limits**: 512MB RAM, 80% CPU quota
- **Security**: Hardened with minimal privileges

### Service Commands
```bash
# Service management
sudo systemctl start boss        # Start service
sudo systemctl stop boss         # Stop service  
sudo systemctl restart boss      # Restart service
sudo systemctl status boss       # Check status
sudo systemctl enable boss       # Enable auto-start
sudo systemctl disable boss      # Disable auto-start

# Logs and monitoring
sudo journalctl -u boss -f       # Follow live logs
sudo journalctl -u boss -n 50    # Show last 50 log entries
sudo journalctl -u boss --since "1 hour ago"  # Logs from last hour
```

### Configuration Files
The service reads configuration from:
- **Main Config**: `/home/rpi/boss/boss/config/boss_config.json`
- **App Mappings**: `/home/rpi/boss/boss/config/app_mappings.json`
- **Environment**: Set via systemd service file

## Remote Management Script

### Windows Setup
1. Copy `scripts/boss_remote_manager.py` to your Windows development machine
2. Update the `RPI_HOST` variable to match your Pi's SSH connection string:
   ```python
   RPI_HOST = "rpi@192.168.1.100"  # Your Pi's IP or hostname
   ```
3. Ensure SSH key authentication is set up for passwordless access

### Interactive Menu
Run `python boss_remote_manager.py` for an interactive menu:

```
==================================================
   B.O.S.S. Remote Management Console
==================================================

Available Commands:
1. 📊 Show Status
2. ▶️  Start Service
3. ⏹️  Stop Service
4. 🔄 Restart Service
5. 📋 Show Logs
6. 📡 Follow Live Logs
7. 🚀 Deploy & Restart
8. 🔧 Hardware Test
9. 👥 Check Groups & Permissions
10. 🔌 SSH to Pi
11. 🔑 Setup SSH Authentication
0. ❌ Exit
```

### Command Line Usage
```bash
# Quick commands (no interactive menu)
python boss_remote_manager.py start      # Start service
python boss_remote_manager.py stop       # Stop service
python boss_remote_manager.py restart    # Restart service
python boss_remote_manager.py status     # Show detailed status
python boss_remote_manager.py logs       # Follow live logs
python boss_remote_manager.py test       # Run hardware test
python boss_remote_manager.py groups     # Check permissions
```

## Development Workflow

### 1. Code Development
1. **Local Development**: Write code in VSCode on Windows
2. **Commit Changes**: Push to git repository
3. **Deploy**: Use remote manager "Deploy & Restart" option
4. **Test**: Monitor logs and run hardware tests
5. **Debug**: Use live logs and status monitoring

### 2. Testing Cycle
```bash
# Make code changes locally, then:
git add .
git commit -m "Your changes"
git push

# Deploy to Pi
python boss_remote_manager.py restart

# Monitor results
python boss_remote_manager.py logs
```

### 3. Hardware Testing
```bash
# Test individual hardware components
python boss_remote_manager.py test

# Check permissions and groups
python boss_remote_manager.py groups

# Monitor live system behavior
python boss_remote_manager.py logs
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status boss

# Check detailed logs
sudo journalctl -u boss -n 50

# Common causes:
# - Config file missing or invalid
# - Permission issues (user not in gpio/video groups)
# - Python environment issues
# - GPIO devices in use by other processes
```

#### 2. Permission Denied Errors
```bash
# Check user groups
groups

# Should include: gpio video audio

# If missing, add groups:
sudo usermod -a -G gpio,video,audio $USER
# Then logout/login or reboot
```

#### 3. GPIO/Hardware Not Working
```bash
# Check GPIO access
ls -la /dev/gpiomem
# Should be readable by gpio group

# Check framebuffer access
ls -la /dev/fb0
# Should be readable by video group

# Install lgpio for better GPIO support
pip install lgpio
```

#### 4. Display/Screen Issues
```bash
# Check framebuffer geometry
fbset -fb /dev/fb0 -i

# Verify config matches framebuffer size
cat boss/config/boss_config.json | grep screen

# Common issue: config resolution != framebuffer resolution
```

#### 5. Remote Manager Connection Issues
```bash
# Test SSH connection
ssh rpi@your-pi-hostname

# Setup SSH keys for passwordless access
ssh-copy-id rpi@your-pi-hostname

# Update RPI_HOST in boss_remote_manager.py
```

### Debug Logging
To enable debug logging, edit the systemd service:
```bash
sudo systemctl edit boss
```

Add override:
```ini
[Service]
Environment=BOSS_LOG_LEVEL=DEBUG
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart boss
```

## Hardware Requirements

### Permissions Required
- **gpio group**: GPIO pin access (buttons, LEDs, switches, display)
- **video group**: Framebuffer access (/dev/fb0 for screen output)
- **audio group**: Audio device access (optional speaker)

### GPIO Libraries
- **gpiozero**: Main GPIO interface
- **lgpio**: Recommended backend (eliminates warnings)
- **python-tm1637**: TM1637 7-segment display support

### Hardware Validation
The remote manager includes hardware testing:
```bash
python boss_remote_manager.py test
```

This tests:
- TM1637 display functionality
- GPIO pin access
- Framebuffer access
- Permission validation

## Security Considerations

### Service Security
- Runs as non-root user (`rpi`)
- Minimal privileges with group-based hardware access
- Read-only filesystem except for logs and config
- Resource limits prevent runaway processes
- Private temp directory

### SSH Security
- Use SSH key authentication (no passwords)
- Consider SSH port forwarding for web interfaces
- Limit SSH access to development machines
- Regular security updates on Pi

## VSCode Integration

### Terminal Integration
Add these to VSCode terminal profile or PowerShell profile:
```powershell
# PowerShell aliases
function boss-start { python scripts/boss_remote_manager.py start }
function boss-stop { python scripts/boss_remote_manager.py stop }
function boss-restart { python scripts/boss_remote_manager.py restart }
function boss-status { python scripts/boss_remote_manager.py status }
function boss-logs { python scripts/boss_remote_manager.py logs }
function boss-console { python scripts/boss_remote_manager.py }
```

### Tasks Configuration
Add to `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "BOSS: Start Service",
            "type": "shell",
            "command": "python",
            "args": ["scripts/boss_remote_manager.py", "start"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "BOSS: Restart Service",
            "type": "shell",
            "command": "python",
            "args": ["scripts/boss_remote_manager.py", "restart"],
            "group": "build"
        },
        {
            "label": "BOSS: Show Logs",
            "type": "shell",
            "command": "python",
            "args": ["scripts/boss_remote_manager.py", "logs"],
            "group": "test"
        }
    ]
}
```

## Best Practices

### Development Workflow
1. **Always use the service** for hardware testing (not direct python execution)
2. **Monitor logs actively** during development and testing
3. **Test hardware components individually** before running full system
4. **Use git workflow** for all code changes (never edit directly on Pi)
5. **Check permissions** if hardware features stop working

### Code Changes
1. **Small incremental changes** with frequent testing
2. **Commit often** to git for easy rollbacks
3. **Test on hardware early** - don't rely only on WebUI simulation
4. **Document hardware-specific quirks** in code comments

### Debugging Strategy
1. **Service status first** - check if service is running
2. **Recent logs** - look for errors in last few minutes
3. **Hardware test** - validate hardware components work
4. **Permissions check** - ensure user has required group access
5. **Config validation** - verify JSON syntax and pin assignments

This remote development setup provides a professional, robust environment for developing and debugging B.O.S.S. applications while maintaining full hardware access and system reliability.
