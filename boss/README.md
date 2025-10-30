# B.O.S.S. Application Package

This directory contains the `boss` Python package, which is the core of the B.O.S.S. system.

## Overview
This package includes all the source code for the application, organized according to Clean Architecture principles.

- **`main.py`**: The main entry point for the application.
- **`core/`**: Contains the core business logic, services, and domain models (Note: this is the target structure after the planned refactoring).
- **`hardware/`**: The hardware abstraction layer, with implementations for real GPIO, a web UI, and mocks.
- **`apps/`**: The directory where all mini-apps are located.
- **`config/`**: Houses the JSON configuration files for the system and app mappings.

For full project documentation, please see the `README.md` in the project root or the documents in the `docs/` directory.

