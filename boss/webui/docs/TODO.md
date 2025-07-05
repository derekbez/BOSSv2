# B.O.S.S. Project TODO List

This file tracks the remaining tasks for development, focusing on enhancing the Web UI Emulator.

## High Priority: Core Functionality

- [ ] **Implement Button Press/Release Simulation**
    - [ ] **Backend**: Create a new API endpoint `/api/button/{button_id}/release`.
    - [ ] **Backend**: Ensure the `MockButton.release()` method is called by the new endpoint.
    - [ ] **Frontend**: In `app.js`, change the button event listener from `click` to `mousedown` and `mouseup`.
    - [ ] **Frontend**: `mousedown` should call the `/press` endpoint.
    - [ ] **Frontend**: `mouseup` should call the `/release` endpoint.
    - [ ] **Docs**: Update `web_ui.md` to reflect the new press/release API endpoints.

- [ ] **Refine Initial State Synchronization**
    - [ ] **Backend**: In `WebUIServer.get_current_hardware_state`, ensure the `screen` state includes the full text content, not just `last_output` or `last_status`.
    - [ ] **Backend**: Consider adding more state details, like the last time a button was pressed or the current running app's name if available via the EventBus.
    - [ ] **Frontend**: Test reconnecting to the WebSocket to ensure the UI correctly re-populates with the full current state every time.

## Medium Priority: Feature Enhancements

- [ ] **Implement Screen Image Emulation (for `PillowScreen`)**
    - [ ] **Backend**: In `WebUIServer`, create a new API endpoint, e.g., `GET /api/screen/image.png`.
    - [ ] **Backend**: This endpoint should access the `mock_hardware['screen']` object, call a method like `get_image_bytes()` (which needs to be created on `PillowScreen`/`MockScreen`), and return an `ImageResponse`.
    - [ ] **Backend (`PillowScreen`)**: Create a `get_image_bytes()` method that saves the current `self.image` buffer to an in-memory `io.BytesIO` object and returns its content.
    - [ ] **Frontend**: Replace the `<pre>` tag for the main screen in `index.html` with an `<img>` tag.
    - [ ] **Frontend**: In `app.js`, when an `output.screen.updated` event is received, update the `src` of the image tag to `/api/screen/image.png?t=${new Date().getTime()}` to force a reload.
    - [ ] **Alternative (WebSocket Streaming)**: Investigate sending the image as a Base64-encoded string over the WebSocket for lower latency updates. This is more complex but provides a better user experience.

- [ ] **Improve Main Screen Text Emulation**
    - [ ] **CSS**: Find and add a monospaced, "pixel-style" web font to better mimic a terminal or raw display.
    - [ ] **CSS**: Adjust the styling of `.main-screen-output` to more closely match the real screen's aspect ratio and color scheme (e.g., black background, green/white text).

- [ ] **Add a Live Event Log to UI**
    - [ ] **HTML**: Add a new panel or component in `index.html` for an "Event Bus Log".
    - [ ] **Backend**: In `WebUIServer.handle_event`, broadcast *all* events to a separate WebSocket message type, e.g., `log_event`.
    - [ ] **Frontend**: In `app.js`, listen for `log_event` and append the event type and payload to the event log panel. This is invaluable for debugging event flow.

## Low Priority: Polish and Refinement

- [ ] **Make Web UI Configurable**
    - [ ] **Core**: Read `host` and `port` for the `WebUIServer` from the main `config.json` file.
    - [ ] **Core**: Provide sensible defaults in `main.py` if the config values are missing.

- [ ] **Improve WebSocket Stability and Error Handling**
    - [ ] **Frontend**: In `app.js`, implement a reconnection strategy for the WebSocket if the connection is lost (e.g., using a simple `setTimeout` with exponential backoff).
    - [ ] **Backend**: Add more robust logging within the `ConnectionManager` and WebSocket endpoint to track connections and disconnections.

- [ ] **Documentation and Cleanup**
    - [ ] **Docs**: Update `docs/web_ui.md` as new features (like image streaming) are added.
    - [ ] **Code**: Refactor `app.js` to better separate UI update logic from WebSocket handling logic.