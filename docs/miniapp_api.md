# B.O.S.S. Mini-App API Documentation

## Overview
This document describes the official API provided by the B.O.S.S. (Board Of Switches and Screen) system for use by all mini-apps. All mini-apps must interact with hardware and display exclusively through this API. Direct hardware access is strictly prohibited to ensure portability, testability, and system safety.

---

## API Object
Each mini-app receives an `api` object as an argument to its entrypoint (typically `run(stop_event, api)` or `main(stop_event, api)`). This object exposes all allowed interactions with the B.O.S.S. hardware and system services.

### API Design Principles
- **Abstraction:** All hardware and display access is abstracted.
- **Mockability:** The API is fully mockable for testing and development.
- **Thread-Safe:** All methods are thread-safe.
- **Extensible:** New features are added via the API, not by direct hardware access.

---

## API Reference

### 1. Display Methods
#### `api.screen.display_text(text: str, *, x: int = None, y: int = None, color: str = "white", bgcolor: str = None, font_size: int = 32, align: str = "center", effects: dict = None, duration: float = None) -> None`
- **Description:** Display text on the 7-inch screen with flexible formatting.
- **Parameters:**
  - `text`: The string to display (supports multi-line, Unicode, emoji).
  - `x`, `y`: Optional coordinates for text position. If omitted, text is centered.
  - `color`: Font color (name or hex).
  - `bgcolor`: Background color (optional).
  - `font_size`: Font size in points.
  - `align`: 'left', 'center', or 'right'.
  - `effects`: Dict for bold, italic, underline, shadow, outline, etc.
  - `duration`: If set, text is cleared after this many seconds.

#### `api.screen.display_image(path: str, *, x: int = None, y: int = None, scale: str = "fit", shape: str = "rect", bgcolor: str = None, alpha: float = 1.0, rounded: bool = False) -> None`
- **Description:** Display an image with scaling and placement options.
- **Parameters:**
  - `path`: Path to image file (relative to app assets or absolute).
  - `x`, `y`: Optional coordinates for image position.
  - `scale`: 'fit', 'fill', 'stretch', 'center'.
  - `shape`: 'rect', 'circle', 'ellipse'.
  - `bgcolor`: Background color (optional).
  - `alpha`: Opacity (0.0–1.0).
  - `rounded`: If true, draws image with rounded corners.

#### `api.screen.clear() -> None`
- **Description:** Clears the screen.

---

### 2. LED Methods
#### `api.leds["red"|"yellow"|"green"|"blue"].on() -> None`
#### `api.leds["red"|"yellow"|"green"|"blue"].off() -> None`
#### `api.leds["red"|"yellow"|"green"|"blue"].blink(on_time: float = 0.5, off_time: float = 0.5, n: int = None) -> None`
- **Description:** Control the state of the color LEDs.

---

### 3. Button Methods
#### `api.buttons["red"|"yellow"|"green"|"blue"].is_pressed() -> bool`
- **Description:** Returns True if the button is currently pressed.
#### `api.buttons["red"|"yellow"|"green"|"blue"].wait_for_press(timeout: float = None) -> bool`
- **Description:** Blocks until the button is pressed or timeout expires.

---

### 4. Speaker Methods (Optional)
#### `api.speaker.play_sound(path: str, volume: float = 1.0) -> None`
- **Description:** Play a sound file (WAV/MP3/OGG) at the given volume.
#### `api.speaker.stop() -> None`
- **Description:** Stop any currently playing sound.

---

### 5. Utility Methods
#### `api.get_switch_value() -> int`
- **Description:** Returns the current value of the 8 toggle switches (0–255).
#### `api.get_config() -> dict`
- **Description:** Returns the current app configuration (read-only).
#### `api.log(message: str, level: str = "info") -> None`
- **Description:** Log a message to the central system log.

---

## Example Mini-App Usage
```python
def run(stop_event, api):
    api.screen.display_text("Hello, BOSS!", color="green", font_size=48)
    api.leds["red"].blink(n=3)
    while not stop_event.is_set():
        if api.buttons["blue"].is_pressed():
            api.screen.display_text("Blue pressed!", color="blue")
            api.speaker.play_sound("assets/beep.wav")
            break
        time.sleep(0.1)
```

---

## Best Practices
- Always check `stop_event.is_set()` in your app loop for clean shutdown.
- Do not access hardware directly; use only the API.
- Use `api.log()` for all app logging.
- Use try/except to handle errors gracefully.
- Place all assets in your app's `assets/` folder.

---

## Versioning
- The API is versioned. Backward-incompatible changes will increment the major version.
- Apps should check for required API features and fail gracefully if unavailable.

---

## Contact
For questions or feature requests, see the main project README or contact the B.O.S.S. maintainers.
