# B.O.S.S. Mini-App Development: Event-Driven API

## Overview
All mini-apps in the new B.O.S.S. architecture use a clean, event-driven API that provides access to hardware, screen, and system events. This enables apps to react to hardware changes without polling or direct hardware access.

## App Structure
Each mini-app should have:
- `manifest.json` - App metadata and configuration
- `main.py` - Main entry point with `run(stop_event, api)` function
- Optional `assets/` directory for images, sounds, etc.

## Manifest Example
```json
{
  "name": "Hello World",
  "description": "Simple hello world app demonstrating event-driven API",
  "version": "1.0.0",
  "author": "BOSS Team",
  "entry_point": "main.py",
  "timeout_seconds": 60,
  "requires_network": false,
  "requires_audio": false,
  "tags": ["example", "basic"]
}
```

## Main App Function
```python
def run(stop_event, api):
    """
    Main app function called by BOSS.
    
    Args:
        stop_event: threading.Event - signals when app should stop
        api: BOSS API object with access to hardware and events
    """
    # Your app code here
    pass
```

## API Reference

### Event Bus (`api.event_bus`)
```python
# Subscribe to events
subscription_id = api.event_bus.subscribe("button_pressed", on_button_press)

# Subscribe with filter
subscription_id = api.event_bus.subscribe("button_pressed", on_red_button, 
                                         filter_dict={"button": "red"})

# Unsubscribe
api.event_bus.unsubscribe(subscription_id)

# Publish events
api.event_bus.publish("custom_event", {"data": "value"})
```

### Screen Control (`api.screen`)
```python
# Display text
api.screen.display_text("Hello World!", font_size=32, color="white", align="center")

# Display image
api.screen.display_image("assets/image.png", scale=0.5, position=(100, 50))

# Clear screen
api.screen.clear_screen("black")

# Get screen size
width, height = api.screen.get_screen_size()
```

### Hardware Control (`api.hardware`)
```python
# Control LEDs
api.hardware.set_led("red", True, brightness=0.8)  # Turn on red LED
api.hardware.set_led("green", False)  # Turn off green LED

# Control 7-segment display
api.hardware.set_display(123)  # Show number
api.hardware.set_display(None)  # Clear display

# Play sounds (if audio enabled)
api.hardware.play_sound("assets/beep.wav", volume=0.5)
```

### Logging (`api.log_*`)
```python
api.log_info("App started successfully")
api.log_error("Something went wrong")
```

### Utilities
```python
# Get app directory path
app_path = api.get_app_path()

# Get asset file path
sound_file = api.get_asset_path("sounds/beep.wav")
```

## Available Events

### Hardware Events
- `"button_pressed"` - `{"button": "red|yellow|green|blue"}`
- `"button_released"` - `{"button": "red|yellow|green|blue"}`
- `"go_button_pressed"` - `{}`
- `"switch_changed"` - `{"old_value": int, "new_value": int}`

### System Events
- `"app_started"` - `{"app_name": str, "switch_value": int}`
- `"app_stopped"` - `{"app_name": str, "switch_value": int, "reason": str}`
- `"system_started"` - `{"hardware_type": str}`
- `"system_shutdown"` - `{"reason": str}`

## Example: Complete Mini-App
```python
def run(stop_event, api):
    """
    Example app that responds to button presses and shows switch values.
    """
    api.log_info("Example app starting")
    
    # Initial display
    api.screen.display_text("Press buttons!\nSwitch value on display", 
                           font_size=24, align="center")
    
    # Track button presses
    button_count = 0
    
    def on_button_press(event_type, payload):
        nonlocal button_count
        button = payload["button"]
        button_count += 1
        
        # Light up the pressed button's LED
        api.hardware.set_led(button, True)
        
        # Update screen
        api.screen.display_text(f"Button: {button}\nCount: {button_count}", 
                               font_size=32, align="center")
        api.log_info(f"{button} button pressed (total: {button_count})")
    
    def on_button_release(event_type, payload):
        button = payload["button"]
        # Turn off the LED
        api.hardware.set_led(button, False)
    
    def on_switch_change(event_type, payload):
        # Show switch value on 7-segment display
        new_value = payload["new_value"]
        api.hardware.set_display(new_value)
        api.log_info(f"Switch changed to: {new_value}")
    
    # Subscribe to events
    api.event_bus.subscribe("button_pressed", on_button_press)
    api.event_bus.subscribe("button_released", on_button_release)
    api.event_bus.subscribe("switch_changed", on_switch_change)
    
    # Main loop - wait for stop signal
    try:
        api.log_info("App running - waiting for events")
        stop_event.wait()  # Block until stop is signaled
    except Exception as e:
        api.log_error(f"App error: {e}")
    finally:
        # Cleanup
        for color in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(color, False)
        api.screen.clear_screen()
        api.log_info("App stopping")
```

## Migration from Old Architecture
1. Update `manifest.json` with new format
2. Change main function signature to `run(stop_event, api)`
3. Replace hardware polling with event subscriptions
4. Use `api.screen.*` instead of direct screen access
5. Use `api.hardware.*` for LED/display control
6. Use `api.log_*` for logging

## Best Practices
- Always subscribe to events rather than polling
- Clean up resources in the `finally` block
- Use `stop_event.wait()` for the main loop
- Log important events for debugging
- Keep the main loop simple - let events drive behavior
- Test apps using the mock hardware mode
- Replace polling or direct hardware access with event subscriptions.
- See the example above and the migration guide for details.

## More Examples
- See the `templates/` directory for more event-driven mini-app templates.
