# B.O.S.S. Mini-App Development: Event-Driven API

## Overview
All mini-apps in the B.O.S.S. architecture use a clean, event-driven API that provides access to hardware, screen, and system events. Mini-apps are located in `boss/apps/` and are co-located with the main system code for modularity. This enables apps to react to hardware changes without polling or direct hardware access.

## App Structure & Location
Each mini-app should be located in `boss/apps/` and have:
- `main.py` - Main entry point with `run(stop_event, api)` function
- `manifest.json` - App metadata and configuration (supports both standard and legacy formats)
- Optional `assets/` directory for images, sounds, data files, etc.

### Example Directory Structure
```
boss/apps/
  list_all_apps/           # System app for browsing available apps
    main.py
    manifest.json
    assets/
  hello_world/            # Example basic app
    main.py
    manifest.json
  current_weather/        # Example network-enabled app
    main.py
    manifest.json
    assets/
      weather_icons/
```

## Manifest Examples

### Standard Format (Recommended)
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

### Legacy Format (Auto-converted)
The system also supports legacy manifest formats for compatibility:
```json
{
  "id": "list_all_apps",
  "title": "Mini-App Directory Viewer", 
  "description": "Displays a paginated list of all available mini-apps",
  "entry_point": "main.py",
  "config": {
    "entries_per_page": 15
  },
  "instructions": "Uses yellow/blue buttons for navigation"
}
```
*Note: Legacy manifests are automatically converted to the standard format at runtime.*

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

# Get asset file path (automatically resolves from boss/apps/your_app/assets/)
sound_file = api.get_asset_path("sounds/beep.wav")
image_file = api.get_asset_path("images/logo.png")
data_file = api.get_asset_path("data.json")
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

## Configuration & App Mappings

Apps are mapped to switch values in `boss/config/app_mappings.json`:
```json
{
  "app_mappings": {
    "0": "list_all_apps",
    "1": "hello_world", 
    "8": "joke_of_the_moment",
    "10": "current_weather",
    "255": "admin_shutdown"
  },
  "parameters": {}
}
```

When a user sets the switches to a value (0-255) and presses the Go button, BOSS loads and runs the corresponding app. If no mapping exists for a switch value, the user will see a "No app mapped" message.

## Migration from Old Architecture
1. Move apps from top-level `apps/` to `boss/apps/` 
2. Update `manifest.json` with new format (or keep legacy format - auto-conversion supported)
3. Change main function signature to `run(stop_event, api)`
4. Replace hardware polling with event subscriptions
5. Use `api.screen.*` instead of direct screen access
6. Use `api.hardware.*` for LED/display control
7. Use `api.log_*` for logging
8. Update asset loading to use `api.get_asset_path()`

## Best Practices
- **Location:** Always place apps in `boss/apps/` for proper module resolution and co-location
- **Events:** Always subscribe to events rather than polling hardware
- **Cleanup:** Clean up resources in the `finally` block
- **Main Loop:** Use `stop_event.wait()` for the main loop instead of while loops
- **Logging:** Log important events for debugging using `api.log_*` methods
- **Hardware:** Keep the main loop simple - let events drive behavior
- **Testing:** Test apps using the mock hardware mode (`--hardware mock`)
- **Assets:** Use `api.get_asset_path()` to load files from your app's assets directory
- **Manifest:** Use the standard manifest format for new apps, legacy format is auto-converted
- **Dependencies:** Declare network/audio requirements in manifest for proper system validation

## Development Workflow
1. Create new app directory in `boss/apps/your_app_name/`
2. Add `main.py` with `run(stop_event, api)` function
3. Add `manifest.json` with app metadata
4. Create `assets/` directory for any data files
5. Add entry to `boss/config/app_mappings.json` to map to a switch value
6. Test with `python -m boss.main --hardware mock`
7. Use the WebUI development interface for visual debugging

## More Examples
- See the `boss/apps/` directory for complete working examples
- Use `boss/apps/hello_world/` as a simple starting template
- See `boss/apps/list_all_apps/` for a more complex example with assets and event handling
