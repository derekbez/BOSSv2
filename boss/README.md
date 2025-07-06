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
1. Install Python 3.11+ and create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Edit `config/BOSSsettings.json` to map switch values to apps.
4. Ensure the pigpio daemon is running for GPIO hardware:
   sudo systemctl start pigpiod
5. Run `python -m boss.main` from the project root to start the system.

6. Open the Web UI debug dashboard in your browser:
   http://localhost:8070/

**Note:**
- Always run the app from the project root (not from inside the boss/boss subfolder).
- The system will automatically detect hardware and use keyboard/mocks for development if hardware is not present.

See `docs/` for more details.
