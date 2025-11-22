# App Authoring

## Minimum Structure
```
apps/<app_name>/
  main.py        # Defines run(stop_event, api)
  manifest.json  # Metadata (name, description, version, optional params)
  assets/        # Optional resources
```

## Entry Point Contract
```python
def run(stop_event, api):
    # stop_event: threading.Event signaled when app must terminate
    # api: AppAPI instance (hardware, event_bus, utilities)
    pass
```
Return nothing; respect shutdown semantics.

## Typical Pattern
```python
def run(stop_event, api):
    api.hardware.set_led('red', True)
    sub_id = api.event_bus.subscribe('input.button.pressed', lambda t,p: handle_button(t,p, api))
    try:
        while not stop_event.is_set():
            # periodic work or wait for events
            stop_event.wait(0.25)
    finally:
        api.event_bus.unsubscribe(sub_id)
        for c in ['red','yellow','green','blue']:
            api.hardware.set_led(c, False)
```

## Manifest Guidelines (Updated)
Example minimal manifest (with mandatory tags):
```json
{
  "name": "hello_world",
  "description": "Simple demo app",
  "version": "1.0.0",
  "tags": ["utility"],
  "timeout_seconds": 120,
  "timeout_behavior": "return"
}
```
Mandatory: `tags` must include at least one from the blueprint taxonomy: `admin`, `content`, `network`, `sensor`, `novelty`, `system`, `utility`.
Global timeout default (system-level) is high for safety; apps SHOULD override with a reasonable value (<300s typical) reflecting expected execution length. Use `timeout_behavior` to define post-timeout action (`return`, `rerun`, or `none`).

See `mini_app_blueprint.md` for full schema and classification details.

## Using AppAPI
- `api.hardware.*` for LEDs only (buttons are event-driven; do not poll).
- `api.screen.display_text()/clear_screen()/display_image()` for UI feedback.
- `api.event_bus.publish(type, payload, source)` to emit app-specific events (avoid generic names; follow blueprint event naming rules).
- Avoid sleeping loops > 0.5s without checking `stop_event`; prefer `stop_event.wait()`.

## Threading & Timeouts
- Each app runs in its own thread; system enforces timeout. Global default is applied if `timeout_seconds` omitted.
- Use `stop_event.wait(interval)` instead of busy-looping.
- Select `timeout_behavior` based on purpose: `return` (most apps), `rerun` (periodic fetchers), `none` (admin/system utilities only).

## Clean Shutdown Requirements
- Turn OFF any LEDs you turned ON.
- Unsubscribe all event handlers.
- Avoid orphan threads or background processes.

## Logging
Use structured logging via standard `logging.getLogger(__name__)`. Avoid excessive DEBUG noise after stabilization.

## Randomness / External APIs
- Wrap external API calls with try/except and publish failure events if relevant.
- Respect timeouts; avoid blocking startup.

## Anti-Patterns
- Direct filesystem writes outside app assets scope.
- Using global state to pass data between apps.
- Hard-coded sleeps ignoring `stop_event`.

## Testing Apps
- Prefer mock hardware backend or webui backend.
- Provide minimal deterministic logic (easy to assert).

## Checklist Before Adding App
- [ ] `run` signature correct.
- [ ] Uses LED gating pattern where buttons are used.
- [ ] No direct hardware implementation imports.
- [ ] Manifest valid JSON (no comments).
- [ ] Manifest includes mandatory `tags` field with canonical taxonomy values.
- [ ] Manifest `name` matches directory name exactly.
- [ ] Includes required fields: `name`, `description`, `version`, `author`.
- [ ] Handles shutdown gracefully.
- [ ] Run validator: `python scripts/validate_manifests.py` (should show 0 errors).

## Manifest Validation
Before committing manifest changes, run the automated validator:
```bash
python scripts/validate_manifests.py
```
The validator enforces:
- JSON validity
- Required fields presence
- Canonical tag usage
- Name/directory match
- Valid `timeout_behavior` values
- Detection of deprecated fields

Exit code 0 = clean; 1 = critical errors found.

Next: `mini_app_blueprint.md` for full standards, then `event_bus_and_logging.md`.
