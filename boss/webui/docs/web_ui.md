# B.O.S.S. Web UI Hardware Emulator

The Web UI Hardware Emulator is a tool for developing and debugging B.O.S.S. applications without requiring physical Raspberry Pi hardware. It provides a web-based interface that emulates all the physical inputs and outputs of the device.

## Features

- **Full Hardware Emulation**: Simulates all major hardware components:
  - **Buttons**: Clickable buttons for Red, Yellow, Green, Blue, and the main "GO" button.
  - **Switches**: An interactive slider and individual toggles to set the 8-bit switch value (0-255).
  - **LEDs**: Visual indicators for the four colored LEDs that change state in real-time.
  - **7-Segment Display**: A display that shows the 4-character output.
  - **Main Screen**: A text area that mirrors the output sent to the main HDMI display.
- **Real-Time Updates**: Uses WebSockets to instantly reflect state changes initiated by the running application on the web UI.
- **Interactive Inputs**: Allows the developer to trigger button presses and change switch values, which are fed directly into the application's event bus.
- **Automatic Start**: The web server launches automatically when `main.py` is run on a non-Raspberry Pi environment (i.e., in mock mode).

## Architecture

The emulator consists of a backend server and a frontend web page.

### Backend (`boss/web_ui/server.py`)

- **Framework**: Built with **FastAPI**, a modern, high-performance Python web framework.
- **Web Server**: A `uvicorn` server runs in a separate, non-blocking thread alongside the main B.O.S.S. application.
- **API Endpoints**:
  - `POST /api/button/{button_id}/press`: Simulates a button press. The `button_id` corresponds to the button's color or "main".
  - `POST /api/switch/set`: Sets the value of the 8-bit switch bank.
- **WebSocket Communication**:
  - A WebSocket endpoint at `/ws` allows the frontend to establish a persistent connection.
  - The `WebUIServer` subscribes to relevant topics on the main application's `EventBus`.
  - When an event occurs (e.g., an LED state changes, the screen is updated), the server broadcasts a JSON message to all connected web clients.
  - On initial connection, the server sends the complete current state of all emulated hardware.

### Frontend (`boss/web_ui/index.html`, `static/app.js`, `static/style.css`)

- **Structure**: A simple HTML page with CSS for styling and JavaScript for interactivity.
- **Client-Side Logic (`app.js`)**:
  - Establishes a WebSocket connection to the backend.
  - Listens for messages from the server and updates the corresponding HTML elements (LEDs, displays, etc.).
  - Adds event listeners to the input elements (buttons, sliders).
  - When a user interacts with an input, it sends an HTTP POST request to the appropriate API endpoint on the backend server.

## How It Works

1.  When `main.py` detects it is running in a mock environment (not on a Pi), it instantiates and starts the `WebUIServer`.
2.  The `WebUIServer` is given access to the application's `EventBus` and the dictionary of mock hardware objects.
3.  The server starts in a background thread, serving the `index.html` file at `http://localhost:8000`.
4.  You open the URL in a web browser. The JavaScript connects to the WebSocket.
5.  When the running B.O.S.S. application calls a function on a mock hardware object (e.g., `led_red.on()`), that object publishes an event to the `EventBus`.
6.  The `WebUIServer`, subscribed to that event, receives it and broadcasts the update over the WebSocket to your browser.
7.  The JavaScript in your browser receives the message and updates the UI (e.g., turns the red LED indicator on).
8.  When you click a button in the UI, the JavaScript sends a `POST` request to the server.
9.  The server's API endpoint calls the corresponding method on the mock hardware object (e.g., `mock_button.press()`).
10. The `mock_button.press()` method publishes a `input.button.pressed` event to the `EventBus`, which the running application can then react to, completing the loop.