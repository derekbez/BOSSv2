# Hardware & Parity

## Hardware Abstraction
Components are accessed via managers and interfaces, never directly by apps:
- Buttons, LEDs, Display, Switches, Screen, (optional Speaker)
- Backends: `gpio`, `webui`, `mock` chosen by config/env/flag.

Factory (`boss.hardware.create_hardware_factory`) returns backend-specific instances; parity guarantees behavior matches across implementations.

## Parity Contract
If an action works in WebUI it must behave identically on real GPIO and mocks.

### LED/Button Activation Pattern
- LED ON means corresponding button press is valid.
- LED OFF filters press (ignored, not published to app handlers).
- Always clear all LEDs on app exit.

Example:
```python
# Enable only red & blue buttons
api.hardware.set_led('red', True)
api.hardware.set_led('blue', True)
for c in ['yellow', 'green']:
    api.hardware.set_led(c, False)
```
Shutdown cleanup:
```python
for c in ['red', 'yellow', 'green', 'blue']:
    api.hardware.set_led(c, False)
```

## Screen Backend
- Canonical backend: `textual` in terminal. (Legacy Pillow removed.)
- Dimensions (`screen_width`, `screen_height`) are logical layout counts (e.g. columns/rows) guiding formatting.

## Switches & Snapshot Behavior
- Switch value (0–255) continuously monitored.
- Go button snapshots current value for app selection consistency.

## Extending Hardware
1. Define new backend module(s) under `boss/hardware/<backend_name>/`.
2. Implement required interface methods (mirror existing backends).
3. Register in factory selection logic.
4. Document in this file and add tests to ensure parity.

## Anti-Patterns
- Reading GPIO directly inside apps.
- Divergent behavior (e.g., LED gating only enforced in one backend).
- Silent failures of button presses (log at INFO when ignored).

## Quick Checklist
- LED gating applied before accepting button press.
- Switch change events published canonically: `input.switch.changed`.
- Display updates use canonical event (`output.display.updated`).

Next: see `app_authoring.md`.
