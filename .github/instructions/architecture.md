# Architecture Overview

Purpose: Provide Copilot and developers a precise mental model of the flattened B.O.S.S. system. Read this first.

## Current High-Level Structure
```
boss/
  core/            # Core orchestration & domain logic (events, managers, models, interfaces)
  hardware/        # Hardware factory + gpio/webui/mock implementations
  config/          # Config loading/validation + secrets interface
  logging/         # Central logging setup
  ui/              # Web UI (FastAPI + WebSocket) & text helpers
  apps/            # Mini-apps (each isolated directory)
  main.py          # Entry point (composition root)
```

## Architectural Principles
- Flat Facade Surface: All consumers import via `boss.core`, `boss.hardware`, `boss.config`, `boss.logging`, `boss.ui`.
- Dependency Direction: Apps depend on provided APIs (`AppAPI`), never directly on hardware implementations.
- Event-Driven: Input (switch/button) and output (display/screen/LED) actions propagate through the `EventBus`.
- Hardware Parity: WebUI, mock, and GPIO behave consistently.
- Configuration Centralization: A single JSON file (`boss/config/boss_config.json`) defines hardware + system settings.
- Deterministic Startup: `main.py` composes services; no hidden side-effects in module import.

## Core Runtime Flow
1.  `main.py` acts as the composition root.
2.  Load & validate configuration (`boss.config`).
3.  Initialize logging (`boss.logging`).
4.  Create a hardware factory based on config (`boss.hardware`). This factory provides access to specific hardware implementations (GPIO, WebUI, or mock).
5.  Instantiate the central `EventBus` (`boss.core`).
6.  Instantiate core services, injecting dependencies explicitly:
    -   `HardwareManager`: Manages hardware components provided by the factory.
    -   `AppManager`: Discovers and manages the lifecycle of mini-apps.
    -   `AppRunner`: Executes mini-apps in separate threads.
    -   `SystemManager`: Orchestrates the overall system state and startup/shutdown sequences.
7.  Register event handlers (`SystemEventHandler`, `HardwareEventHandler`) to connect system logic and hardware actions.
8.  The `SystemManager` starts all services. The system then runs, processing events and app logic until a shutdown signal is received.

## Event Model (Simplified)
Categories:
- Input: `input.switch.changed`, `input.button.pressed`, `input.button.released`
- Output: `output.display.updated`, `output.screen.updated`, `output.led.state_changed`
- System/App Lifecycle: `system.app.started`, `system.app.finished`, `system.shutdown.initiated`

Naming Rules:
- Use dot-separated lowercase tokens.
- Past tense for completed state transitions (`state_changed`, `updated`).
- Avoid legacy aliases (`switch_change`, `display_update`). Always publish canonical forms.

## App Boundary
Mini-apps receive an `AppAPI` instance. They must NOT:
- Import from `boss.hardware.gpio.*` or mocks directly.
- Persist threads beyond allowed timeout.
- Mutate global config files.

They MUST:
- Use LED/Button parity pattern to gate button input.
- Subscribe/unsubscribe to events responsibly.
- Handle `stop_event` for clean shutdown.

## Extension Points
- New hardware: implement interface under `boss/hardware/<backend>` and expose via factory.
- New app: create `apps/<name>/main.py` + `manifest.json`.
- New event type: define and document in `event_bus_and_logging.md`; ensure consumers exist or are optional.

## Anti-Patterns
- Direct GPIO pin access in apps.
- Polling loops bypassing event system.
- Blocking the main thread with long computations (offload to app thread or async where applicable).

## Migration Notes (Legacy to Current)
Removed layers (`application/`, `domain/`, `infrastructure/`, `presentation/`) merged into `core/`, `hardware/`, `config/`, `logging/`, `ui/` to reduce indirection.

## Quick Checklist Before Committing
- No import of removed legacy paths.
- Events published use canonical names.
- App LED state matches expected button availability.
- Tests remain green (`pytest`).

Refer next to: `development_environment.md` then `app_authoring.md`.
