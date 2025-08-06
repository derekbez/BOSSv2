# B.O.S.S. Remote Development Quick Reference

## Setup (One-time)
```bash
# On Raspberry Pi
cd ~/boss
./scripts/setup_systemd_service.sh
sudo reboot

# On Windows
# 1. Setup SSH authentication (see docs/ssh_authentication_setup.md)
ssh-keygen -t rsa -b 4096

# 2. Copy SSH key to Pi (Windows method)
type ~/.ssh/id_rsa.pub | ssh rpi@192.168.1.143 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
# Enter Pi password when prompted

# 3. Update RPI_HOST in scripts/boss_remote_manager.py
# 4. Test SSH connection: ssh rpi@192.168.1.143
```

## Daily Development Commands

### From Windows/VSCode Terminal
```bash
# Interactive console
python scripts/boss_remote_manager.py

# Quick commands
python scripts/boss_remote_manager.py start     # Start service
python scripts/boss_remote_manager.py stop      # Stop service  
python scripts/boss_remote_manager.py restart   # Restart service
python scripts/boss_remote_manager.py status    # Show status
python scripts/boss_remote_manager.py logs      # Follow live logs
python scripts/boss_remote_manager.py test      # Hardware test
python scripts/boss_remote_manager.py groups    # Check permissions
python scripts/boss_remote_manager.py ssh-setup # Setup SSH auth
```

### Direct SSH Commands
```bash
# Service control
sudo systemctl start boss
sudo systemctl stop boss
sudo systemctl restart boss
sudo systemctl status boss

# Monitoring
sudo journalctl -u boss -f              # Live logs
sudo journalctl -u boss -n 50           # Last 50 entries
sudo journalctl -u boss --since "1h ago" # Last hour
```

## Development Workflow
1. **Code**: Develop in VSCode on Windows
2. **Commit**: `git add . && git commit -m "changes" && git push`
3. **Deploy**: `python scripts/boss_remote_manager.py restart`
4. **Monitor**: `python scripts/boss_remote_manager.py logs`
5. **Test**: `python scripts/boss_remote_manager.py test`

## Troubleshooting
- **SSH issues**: Run `python scripts/boss_remote_manager.py ssh-setup`
- **Service issues**: Check `sudo systemctl status boss`
- **Permissions**: Run `python scripts/boss_remote_manager.py groups`
- **Hardware**: Run `python scripts/boss_remote_manager.py test`
- **Logs**: Use `python scripts/boss_remote_manager.py logs`

## File Locations
- **Service**: `/etc/systemd/system/boss.service`
- **Config**: `/home/rpi/boss/boss/config/boss_config.json`
- **Logs**: `sudo journalctl -u boss`
- **Code**: `/home/rpi/boss/`

## Key Features
- ✅ Auto-restart on failure
- ✅ Proper hardware permissions (gpio/video/audio)
- ✅ Resource limits and security hardening
- ✅ Live log monitoring from Windows
- ✅ Hardware testing and validation
- ✅ Git-based deployment workflow
