# Hardware Parity Principle

## Overview
The B.O.S.S. system implements a **Hardware Parity Principle** ensuring seamless development-to-production transitions. The WebUI is not just a debugging tool—it's a complete hardware emulation layer that behaves identically to real GPIO hardware.

## Core Principle
> **Any behavior implemented for real GPIO hardware must work identically in the WebUI, and any feature developed/tested in the WebUI must work identically on real hardware.**

## Why This Matters
- **Confidence**: What you test in development will work in production
- **Efficiency**: No need to constantly deploy to Pi for testing
- **Debugging**: Complex interactions can be debugged in the WebUI first
- **Accessibility**: Developers can work on any platform, not just Pi

## Hardware Abstraction Layers

### 1. Real Hardware (GPIO)
- Physical buttons connected to GPIO pins
- Physical LEDs controlled via GPIO pins
- TM1637 display showing actual numbers
- Physical switches setting real states

### 2. WebUI Hardware (Development)
- Virtual buttons in web interface
- Virtual LED indicators with on/off states  
- Virtual 7-segment display showing numbers
- Virtual switches with binary/decimal controls

### 3. Mock Hardware (Testing)

### Screen Backends Note
The default screen backend is now the textual (Rich-based) backend for both development and production. The legacy Pillow framebuffer backend remains only for explicit legacy scenarios and is deprecated. Mini-apps should treat screen output as text-only; image APIs will no-op under textual.
- In-memory state tracking
- Console logging of hardware events
- No visual interface, pure programmatic

## Implementation Examples

### LED/Button Coordination
**Real Hardware:**
```python
# App sets LED on
api.hardware.set_led('red', True)  # Physical LED lights up

# User presses physical button
# → GPIO interrupt → hardware service → event bus → app receives event
```

**WebUI Hardware:**
```python
# App sets LED on  
api.hardware.set_led('red', True)  # Virtual LED shows "ON" in browser

# User clicks virtual button
# → WebSocket → API → hardware service → event bus → app receives event
```

**Identical Result:** App receives the same button event structure in both cases.

### State Filtering
**Real Hardware:**
- RED LED is OFF
- User presses physical RED button  
- Hardware service checks LED state → press ignored
- App receives no event

**WebUI Hardware:**
- RED LED indicator shows "OFF"
- User clicks virtual RED button
- API checks LED state → press ignored  
- App receives no event

**Identical Behavior:** Both environments filter button presses based on LED state.

## Development Workflow

### 1. Develop in WebUI
```bash
# Start system with WebUI
python -m boss.main

# Open browser → http://localhost:8000
# Develop app using virtual controls
# Test LED/button interactions
# Verify screen display and events
```

### 2. Deploy to Hardware
```bash
# Same code, same configuration
# Hardware automatically detected
# Real GPIO used instead of WebUI
# Identical behavior guaranteed
```

## Configuration Consistency

Both environments use the same configuration:

```json
// boss/config/boss_config.json
{
  "hardware": {
    "button_pins": {"red": 5, "yellow": 6, "green": 13, "blue": 19},
    "led_pins": {"red": 21, "yellow": 20, "green": 26, "blue": 12}
  }
}
```

- **Real Hardware**: Uses actual GPIO pin numbers
- **WebUI**: Ignores pin numbers, provides virtual interface
- **Same API**: `api.hardware.set_led('red', True)` works in both

## Event Structure Consistency

Button events have identical structure across all hardware layers:

```json
{
  "event": "button_pressed",
  "payload": {
    "button_id": "red",
    "timestamp": "2025-01-23T10:30:00Z"
  }
}
```

This consistency ensures mini-apps work identically regardless of hardware layer.

## Testing Strategy

### Development Testing (WebUI)
- Full functionality testing in browser
- LED/button interaction validation
- Screen content verification
- Event flow debugging

### Integration Testing (Pi)
- Periodic deployment to real hardware
- Validation of GPIO pin assignments
- Physical interaction testing
- Performance verification

### Unit Testing (Mocks)
- Fast automated testing
- Logic verification without hardware
- CI/CD pipeline integration

## Best Practices

### For Developers
1. **Always test in WebUI first** before deploying to Pi
2. **Use same configuration files** in both environments  
3. **Follow LED/button patterns** established in documentation
4. **Verify events** using WebUI event log before production

### For Mini-App Authors
1. **Use the App API exclusively** - never access hardware directly
2. **Test LED coordination** in WebUI to ensure proper UX
3. **Validate button event handling** using virtual controls
4. **Check screen display** in WebUI before Pi deployment

## Troubleshooting Hardware Differences

If behavior differs between WebUI and real hardware:

1. **Check configuration** - ensure pin assignments are correct
2. **Verify event structure** - compare WebUI event log with Pi logs
3. **Test LED states** - confirm LED on/off matches expectations
4. **Review button subscriptions** - ensure app listens for correct events

## Future Enhancements

The Hardware Parity Principle enables:
- **New hardware support** - add virtual equivalents for new devices
- **Advanced debugging** - WebUI can show internal state not visible on Pi
- **Automated testing** - WebUI can be scripted for comprehensive testing
- **Remote development** - work on BOSS apps from anywhere

---

This principle ensures the BOSS system remains maintainable, testable, and accessible while guaranteeing production reliability.
