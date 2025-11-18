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
1. Load & validate config.
2. Initialize logging.
3. Create hardware factory (gpio/webui/mock selection).
4. Create `EventBus`.
5. Instantiate managers: `HardwareManager`, `AppManager`, `AppRunner`, `SystemManager`.
6. Register event handlers (system + hardware output).
7. System waits on shutdown signal while apps run in threads.

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
