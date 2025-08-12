# B.O.S.S. (Board Of Switches and Screen)

This is the main application package for B.O.S.S., a modular, hardware-interfacing Python system for Raspberry Pi. See the `docs/` directory for full documentation and specifications.

## Directory Structure
- `main.py`: Application entry point
- `core/`: Core logic (app manager, event bus, config, logger, API, remote management)
- `hardware/`: Hardware abstraction layer
- `apps/`: Mini-apps (each as a subdirectory with manifest)
- `assets/`: Images, sounds, and other data files
- `config/`: Configuration files
- `tests/`: Unit and integration tests
- `scripts/`: Utility scripts
- `docs/`: Documentation


## Getting Started

### For Production Hardware (Recommended)
1. Install Python 3.11+ and create a virtual environment.
2. Install dependencies from `requirements/base.txt` plus `lgpio` for optimal GPIO performance.
3. Setup systemd service for robust operation:
   ```bash
   ./scripts/setup_systemd_service.sh
   sudo systemctl start boss
   ```
4. Use remote management for development:
   ```bash
   python scripts/boss_remote_manager.py
   ```

### For Local Development/Testing
1. Install Python 3.11+ and create a virtual environment.
2. Install dependencies from `requirements/base.txt` (and `requirements/dev.txt` for local dev).
3. Edit `config/boss_config.json` to configure hardware pins.
4. Edit `config/app_mappings.json` to map switch values to apps.
5. Run `python -m boss.main` from the project root to start the system.
6. Open the Web UI debug dashboard in your browser: http://localhost:8080/

**Note:**
- Always run the app from the project root (not from inside the boss/boss subfolder).
- The system will automatically detect hardware and use mocks for development if hardware is not present.
- For production hardware, use the systemd service for reliability and proper permissions.

See `docs/remote_development.md` for comprehensive remote development setup and troubleshooting.

See `docs/` for more details.
