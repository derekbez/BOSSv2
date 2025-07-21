# B.O.S.S. Event Schema - New Architecture

## Overview
The new B.O.S.S. architecture uses a simplified event bus for system communication. All hardware events, system events, and app events flow through a single, robust event bus.

## Event Bus Implementation
- **Location**: `boss/application/events/event_bus.py`
- **Pattern**: Simple publish/subscribe with synchronous delivery
- **Thread Safety**: All methods are thread-safe
- **Error Handling**: Robust error handling with logging

## Core Events

### Hardware Events

#### Button Events
```python
# Published when a colored button is pressed
event_type: "button_pressed"
payload: {
    "button": "red" | "yellow" | "green" | "blue",
    "timestamp": float
}

# Published when a colored button is released
event_type: "button_released" 
payload: {
    "button": "red" | "yellow" | "green" | "blue",
    "timestamp": float
}

# Published when the main Go button is pressed
event_type: "go_button_pressed"
payload: {
    "timestamp": float
}
```

#### Switch Events
```python
# Published when switch value changes
event_type: "switch_changed"
payload: {
    "old_value": int,  # Previous switch value (0-255)
    "new_value": int,  # New switch value (0-255)
    "timestamp": float
}
```

### Hardware Output Events

#### LED Control
```python
# Request LED state change
event_type: "led_update"
payload: {
    "led": "red" | "yellow" | "green" | "blue",
    "state": bool,  # True = on, False = off
    "brightness": float  # 0.0 to 1.0 (optional)
}
```

#### Display Control
```python
# Update 7-segment display
event_type: "display_update"
payload: {
    "value": int | None,  # Number to display (0-255) or None to clear
    "brightness": float   # 0.0 to 1.0 (optional)
}
```

#### Screen Control
```python
# Update main screen content
event_type: "screen_update"
payload: {
    "content_type": "text" | "image" | "clear",
    "data": str,           # Text content or image path
    "x": int,             # X position (optional)
    "y": int,             # Y position (optional)
    "font_size": int,     # Font size for text (optional)
    "color": str,         # Text/background color (optional)
    "align": str          # Text alignment (optional)
}
```

### System Events

#### Application Lifecycle
```python
# App launch requested (usually from Go button)
event_type: "app_launch_requested"
payload: {
    "switch_value": int,   # Current switch value
    "timestamp": float
}

# App started successfully
event_type: "app_started"
payload: {
    "app_name": str,
    "switch_value": int,
    "timestamp": float
}

# App stopped (normal or forced)
event_type: "app_stopped" 
payload: {
    "app_name": str,
    "switch_value": int,
    "reason": "normal" | "timeout" | "error" | "user_stop",
    "duration": float,     # How long app ran (seconds)
    "timestamp": float
}

# App encountered an error
event_type: "app_error"
payload: {
    "app_name": str,
    "switch_value": int,
    "error": str,          # Error message
    "timestamp": float
}
```

#### System Lifecycle
```python
# System started successfully
event_type: "system_started"
payload: {
    "hardware_type": "gpio" | "webui" | "mock",
    "timestamp": float
}

# System shutdown initiated
event_type: "system_shutdown"
payload: {
    "reason": "user" | "signal" | "error",
    "timestamp": float
}
```

## Event Bus API

### Publishing Events
```python
# Publish an event
event_bus.publish(event_type: str, payload: dict)

# Example
event_bus.publish("button_pressed", {
    "button": "red",
    "timestamp": time.time()
})
```

### Subscribing to Events
```python
# Subscribe to all events of a type
subscription_id = event_bus.subscribe(event_type: str, handler: callable)

# Subscribe with payload filtering
subscription_id = event_bus.subscribe(
    event_type: str, 
    handler: callable,
    filter_dict: dict  # Only events matching this dict will be delivered
)

# Example
def on_button_press(event_type, payload):
    button = payload["button"]
    print(f"{button} button pressed")

# Subscribe to all button presses
sub_id = event_bus.subscribe("button_pressed", on_button_press)

# Subscribe only to red button presses
red_sub_id = event_bus.subscribe(
    "button_pressed", 
    on_button_press,
    filter_dict={"button": "red"}
)
```

### Unsubscribing
```python
# Unsubscribe from events
event_bus.unsubscribe(subscription_id)
```

## Event Flow Architecture

```
Hardware Layer (GPIO/WebUI/Mock)
    │
    │ (publishes hardware events)
    ▼
Event Bus (application/events/event_bus.py)
    │
    ├─► System Service (handles system events)
    ├─► Hardware Service (handles output events) 
    ├─► App Manager (handles app lifecycle events)
    └─► Mini-Apps (via App API)
```

## Implementation Notes

### Thread Safety
- All event bus operations are thread-safe
- Events are delivered synchronously in the calling thread
- Hardware monitoring runs in background threads

### Error Handling
- Event handler exceptions are caught and logged
- Failed event delivery doesn't stop other handlers
- Event bus continues operating even with handler errors

### Performance
- Events are delivered immediately (no queuing)
- Simple dict-based filtering for efficiency
- Minimal overhead for publish/subscribe operations

### Testing
- Mock hardware publishes same events as real hardware
- Event bus can be easily mocked for unit tests
- All events are logged for debugging and testing

## Migration from Old Event Bus

The new event bus is much simpler than the previous over-engineered version:

### Removed Complexity
- ❌ CQRS command/query separation
- ❌ Complex mediator patterns  
- ❌ Async event handling
- ❌ Event sourcing and replay
- ❌ Complex event hierarchies

### Kept Simplicity
- ✅ Simple publish/subscribe
- ✅ Type-safe event definitions
- ✅ Robust error handling
- ✅ Event filtering
- ✅ Comprehensive logging

This simplified approach provides all the functionality needed for B.O.S.S. while being much easier to understand, test, and maintain.
