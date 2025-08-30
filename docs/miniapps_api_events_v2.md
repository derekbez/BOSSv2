# B.O.S.S. Mini‑App API & Event Guide (v2)

Date: 2025-08-30  
Status: Authoritative (supersedes legacy `miniapp_api.md` + `event_schema.md`)

---
## 1. Purpose
Defines the supported surface area mini‑apps may rely on in the simplified architecture. Anything not described here is internal and may change without notice.

---
## 2. Architecture Summary
Mini‑apps run in their own thread and interact ONLY via:
1. The provided API object (screen, hardware, event bus helpers)
2. Publishing/subscribing to events on the central event bus

Direct GPIO / OS calls (beyond reading bundled assets) are prohibited.

---
## 3. API Object Facets
Implementation reference: `boss/application/api/app_api.py` (contains some TODO stubs; this doc is the contract).

| Facet | Purpose | Methods |
|-------|---------|---------|
| `api.screen` | Request screen changes | `display_text(text, font_size=24, color='white', background='black', align='center')`, `display_image(path, scale=1.0, position=(0,0))`, `clear_screen(color='black')`, `get_screen_size()` |
| `api.hardware` | LEDs (and placeholder sound) | `set_led(color, is_on, brightness=1.0)`, `play_sound(path, volume=1.0)` (future) |
| `api.event_bus` | Event integration | `subscribe(event_type, handler, filter_dict=None)`, `unsubscribe(id)`, `publish(event_type, payload)` |
| Path helpers | Asset resolution | `get_asset_path(filename)` |
| Logging | Central logging | `log_info(msg)`, `log_error(msg)` |

### 3.1 LED/Button Parity (MANDATORY UX RULE)
If a button is a valid action, its LED must be ON. A press while OFF is ignored (identical behavior on physical + WebUI). Turn all LEDs off in cleanup.

### 3.2 Long Loops & Shutdown
Check `stop_event.is_set()` frequently (≤100ms typical) so forced termination is graceful.

### 3.3 Asset Access
Use `api.get_asset_path()` instead of constructing file paths manually.

### 3.4 Logging
Always use provided logging helpers; they tag messages with app context.

---
## 4. Event Bus
File: `boss/application/events/event_bus.py`.

Characteristics:
* Bounded queue, worker thread processes events asynchronously.
* Per-event-type subscription lists with optional dict filter (all keys must match payload).
* Handler exceptions are logged; platform may remove bad handlers in future enhancement.

### 4.1 Subscribe / Unsubscribe
```python
sub_id = api.event_bus.subscribe("button_pressed", handler)  # with optional filter_dict
... # later
api.event_bus.unsubscribe(sub_id)
```
Store subscription IDs and always unsubscribe (or rely on `api.cleanup()` once implemented fully).

### 4.2 Canonical Event Types (Current Implementation)

| Event | Direction | Payload Keys | Notes |
|-------|-----------|--------------|-------|
| `button_pressed` | System -> Apps | `button`, `timestamp` | button ∈ {red,yellow,green,blue} |
| `button_released` | System -> Apps | `button`, `timestamp` |  |
| `go_button_pressed` | System internal | `timestamp` | Causes `app_launch_requested` |
| `switch_changed` | System -> Apps | `old_value`, `new_value`, `timestamp` | 0–255 |
| `app_launch_requested` | System | (optional) `switch_value`, `timestamp` | Launch logic can infer switch value |
| `app_started` | System -> Apps | `app_name`, `switch_value`, `timestamp` |  |
| `app_stopped` | System -> Apps | `app_name`, `switch_value`, `reason`, `timestamp` | reason ∈ {normal, timeout, error, user_stop} |
| `app_error` | System -> Apps | `app_name`, `timestamp` | `error` detail may be added later |
| `system_started` | System -> Apps | `hardware_type`, `timestamp` |  |
| `system_shutdown` | System -> Apps | `reason`, `timestamp` | reasons include reboot,poweroff,exit_to_os,user,signal,error |
| `led_update` | App -> System (HW) | `color`, `is_on`, `brightness` | color ∈ {red,yellow,green,blue}, brightness 0–1 |
| `screen_update` (text) | App -> System (UI) | `content_type='text'`, `content`, `font_size`, `color`, `background`, `align` | Minimal styling |
| `screen_update` (image) | App -> System (UI) | `content_type='image'`, `content` (path), `scale`, `position` | position tuple (x,y) |
| `screen_update` (clear) | App -> System (UI) | `content_type='clear'`, `content` (background_color) | Clears screen |

Legacy differences: `led`→`color`, `state`→`is_on`, `data`→`content`.

### 4.3 Custom Events
Apps may publish custom namespaced events (e.g. `quiz_answer_selected`). Avoid collisions with core list above. Document any custom events in the app's README.

### 4.4 Best Practices
1. Keep handlers lightweight; offload heavy work to your main loop.
2. Guard against missing payload keys.
3. Unsubscribe in a `finally:` block.
4. Debounce rapid hardware-driven actions inside the handler if needed.

---
## 5. Mini‑App Template Pattern
```python
def run(stop_event, api):
    api.log_info("Starting sample app")
    # LED/Button availability
    for c in ("red","yellow","green","blue"): api.hardware.set_led(c, False)
    api.hardware.set_led("red", True)

    api.screen.display_text("Hello BOSS", color="green", font_size=32)

    def on_press(event_type, payload):
        if payload.get("button") == "red":
            api.screen.display_text("Red pressed", color="red")
            api.hardware.set_led("red", False)
    sub_id = api.event_bus.subscribe("button_pressed", on_press)

    try:
        while not stop_event.is_set():
            time.sleep(0.05)
    finally:
        api.event_bus.unsubscribe(sub_id)
        for c in ("red","yellow","green","blue"): api.hardware.set_led(c, False)
        api.screen.clear_screen()
        api.log_info("Sample app finished")
```

---
## 6. Migration (Legacy → v2)
| Legacy Concept | v2 Adjustment |
|----------------|---------------|
| `led_update` payload (`led`,`state`) | Use (`color`,`is_on`) |
| `screen_update` key `data` | Use `content` |
| Synchronous event delivery | Now queued async worker |
| App control of 7‑seg display | Removed (system only) |
| Rich styling/effects dict | Not yet implemented; keep to basics |

---
## 7. Error Handling Guidance
| Issue | App Strategy |
|-------|--------------|
| Screen update ignored / fails | Re-send if critical; keep running |
| Event queue full warning | Reduce publishing rate / debounce |
| Handler payload mismatch | Log + return (do not raise) |

---
## 8. Future Roadmap (Non‑Breaking)
* Timed text auto-clear
* Basic layout widgets (panels, marquees)
* Audio events (`sound_play`, `sound_stop`)
* Per-app config hot reload event

---
## 9. New App Compliance Checklist
1. Uses only documented API facets
2. Implements LED/Button parity rule
3. Cleans up LEDs, subscriptions, screen
4. Checks `stop_event` regularly
5. Central logging only
6. Assets in `assets/`

---
## 10. Feedback
Open a PR referencing this file with: rationale, proposed event(s), payload schema, backward compatibility note.

End of document.
