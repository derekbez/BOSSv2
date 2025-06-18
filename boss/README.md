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
4. Run `python -m boss.main` to start the system.

See `docs/` for more details.
