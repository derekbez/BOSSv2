# B.O.S.S. (Board Of Switches and Screen)

B.O.S.S. is a modular, event-driven Python application for Raspberry Pi. It provides a physical interface to select and run mini-apps using 8 toggle switches, a 7-segment display, buttons, LEDs, and a 7-inch screen.

This project is designed for extensibility, robust hardware abstraction, and seamless development with or without real hardware.

## Key Features
- **Physical Interface:** Control the system with toggle switches, buttons, and a 7-segment display.
- **Mini-Apps:** A dynamic library of small applications that can be run on demand.
- **Hardware Abstraction:** Develop and test on any machine, with or without the physical hardware.
- **Event-Driven:** A clean, event-based architecture for modularity and responsiveness.
- **Remote Management:** Control and monitor the B.O.S.S. system remotely.

## Getting Started

### For Production Hardware (Raspberry Pi)
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements/base.txt
    sudo apt-get install -y libasound2-dev # If using audio
    ```
2.  **Setup Systemd Service:** For robust, headless operation, run the setup script and start the service.
    ```bash
    cd /path/to/BOSSv2
    ./scripts/setup_systemd_service.sh
    sudo systemctl start boss
    ```
3.  **Monitor Logs:**
    ```bash
    sudo journalctl -u boss -f
    ```

### For Local Development (Windows/macOS/Linux)
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements/dev.txt
    ```
2.  **Run the Application:**
    ```bash
    python -m boss.main
    ```
3.  **Access the Web UI:** Open your browser to `http://localhost:8080` to interact with the virtual hardware.

## Documentation
- **[Copilot Instructions](./.github/copilot-instructions.md):** The primary source of truth for architecture, coding guidelines, and best practices.
- **[Remote Development](./docs/remote_development.md):** A detailed guide for setting up and managing the system on a Raspberry Pi from a development machine.
- **[Mini-Apps](./docs/mini-apps.md):** Information on how to create and configure new mini-apps.

## Directory Structure
- `.github/`: Contains Copilot instructions and CI workflows.
- `boss/`: The main Python package.
  - `main.py`: Application entry point.
  - `core/`: Core services, event bus, and application logic (after refactoring).
  - `hardware/`: Hardware abstraction layer (real, web, and mock).
  - `apps/`: The collection of mini-apps.
  - `config/`: System and app mapping configuration files.
- `docs/`: Project documentation.
- `scripts/`: Helper scripts for development and deployment.
- `tests/`: Unit and integration tests.
