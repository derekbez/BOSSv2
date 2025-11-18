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

## Manifest Guidelines
Example minimal manifest:
```json
{
  "name": "hello_world",
  "description": "Simple demo app",
  "version": "1.0.0"
}
```
Add fields only as needed; keep stable for automated listing.

## Using AppAPI
- `api.hardware.*` for LEDs, buttons (read-only events), display, screen.
- `api.event_bus.publish(type, payload, source)` to emit app-specific events (avoid generic names).
- Avoid sleeping loops > 0.5s without checking `stop_event`.

## Threading & Timeouts
- Each app runs in its own thread; forced termination if exceeding configured timeout (`app_timeout_seconds`).
- Use `stop_event.wait(interval)` instead of busy-looping.

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
- [ ] Handles shutdown gracefully.

Next: `event_bus_and_logging.md`.
