# B.O.S.S. Mini-App Development: Event-Driven Templates

## Overview
All new mini-apps should use the event-driven API provided by B.O.S.S. via the `api.event_bus` object. This enables apps to react to hardware and system events (e.g., button presses, switch changes) without polling or direct hardware access.

## Example: Hello World Mini-App (Button-Driven)
```python
# hello_world.py

def run(stop_event, api):
    """
    Example mini-app that displays 'Hello World' when the red button is pressed.
    Args:
        stop_event: threading.Event to signal app termination
        api: object with .screen and .event_bus
    """
    def on_red_button(event_type, payload):
        api.screen.display_text("Hello World!", align='center')

    # Subscribe to red button press events
    api.event_bus.subscribe("button_press", on_red_button, filter={"button": "red"})

    # Wait for app termination
    stop_event.wait()
```

## Template Guidelines
- **Subscribe to events:** Use `api.event_bus.subscribe(event_type, handler, filter=...)` for all hardware/system events.
- **No polling:** Do not use polling loops for hardware state.
- **No direct GPIO:** Do not access GPIO or hardware directly; use the event bus.
- **Unregister handlers:** If your app needs to clean up, store the subscription and unregister on exit (future API).
- **Document event usage:** Add comments explaining which events your app subscribes to and why.

## Migrating Existing Apps
- Replace polling or direct hardware access with event subscriptions.
- See the example above and the migration guide for details.

## More Examples
- See the `templates/` directory for more event-driven mini-app templates.
