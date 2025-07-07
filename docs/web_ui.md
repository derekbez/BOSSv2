# B.O.S.S. Web UI Hardware Emulator

The Web UI Hardware Emulator is a comprehensive tool for developing and debugging B.O.S.S. applications without requiring physical Raspberry Pi hardware. It provides a web-based interface that emulates all the physical inputs and outputs of the device with full feature parity.

## Features

- **Full Hardware Emulation**: Simulates all major hardware components:
  - **Buttons**: Clickable buttons for Red, Yellow, Green, Blue, and the main "GO" button with visual feedback and keyboard shortcuts.
  - **Switch Controls**: 
    - Decimal input field (0-255) with validation
    - 8 individual bit toggle switches for direct binary control
    - Real-time binary display showing current value
    - Keyboard shortcuts for quick testing (arrow keys, R for reset, M for max)
  - **LEDs**: Realistic LED indicators with proper colors, glowing effects, and real-time state updates.
  - **7-Segment Display**: Retro-styled green-on-black display showing 4-character output with proper padding.
  - **Main Screen**: Canvas-based screen emulator (800x480) that mirrors the main HDMI display output.
- **Real-Time Updates**: Uses WebSockets to instantly reflect state changes initiated by the running application on the web UI.
- **Interactive Inputs**: Allows developers to trigger button presses and change switch values, which are fed directly into the application's event bus.
- **Developer Tools**: 
  - Real-time event monitor with filtering capabilities
  - Connection status indicator
  - System information display
- **Modern UI**: Dark theme with professional styling, responsive design, and smooth animations.
- **Automatic Start**: The web server launches automatically when `main.py` is run in mock mode (non-Raspberry Pi environment).

## Architecture

The emulator consists of a FastAPI backend server with WebSocket support and a modern frontend web interface.

### Backend (`boss/webui/server.py` and `boss/webui/main.py`)

- **Framework**: Built with **FastAPI**, a modern, high-performance Python web framework.
- **Web Server**: A `uvicorn` server runs in a separate, daemon thread alongside the main B.O.S.S. application.
- **WebSocket Manager**: Handles multiple client connections and real-time event broadcasting.
- **API Endpoints**:
  - `POST /api/button/{button_id}/press`: Simulates a button press. The `button_id` corresponds to "red", "yellow", "green", "blue", or "main".
  - `POST /api/switch/set`: Sets the value of the 8-bit switch bank (0-255).
  - `POST /api/led/{color}/set`: Manual LED control for testing.
  - `POST /api/display/set`: Set 7-segment display content.
  - `POST /api/screen/set`: Set screen content.
  - `POST /api/screen/clear`: Clear the screen.
  - `GET /api/system/info`: Get system and hardware status information.
- **WebSocket Communication**:
  - WebSocket endpoint at `/ws` allows persistent bidirectional communication.
  - The WebSocket manager subscribes to relevant events on the main application's EventBus.
  - When hardware events occur (LED changes, display updates, screen updates), the server broadcasts JSON messages to all connected clients.
  - Initial hardware state is sent when clients connect.
  - Automatic reconnection handling with status indicators.

### Frontend (`boss/webui/static/index.html`, `app.js`, `style.css`)

- **Structure**: Modern HTML5 page with CSS Grid layout and comprehensive JavaScript application logic.
- **Technology**: Vanilla JavaScript (ES6+), CSS3 with custom properties, responsive design.
- **Client-Side Logic (`app.js`)**:
  - Establishes WebSocket connection with automatic reconnection.
  - Real-time event handling and hardware state synchronization.
  - Interactive controls for all hardware components.
  - Event logging and filtering system.
  - Keyboard shortcuts for rapid testing.
  - Visual feedback and animations for user interactions.

## How It Works

1.  When `main.py` detects it is running in mock mode, it calls `start_web_ui()` with the hardware dictionary and event bus.
2.  The web UI server is created with FastAPI and the WebSocket manager is initialized with hardware references.
3.  The WebSocket manager subscribes to relevant events (`output.led.state_changed`, `output.display.updated`, `output.screen.updated`, `input.switch.changed`).
4.  The server starts in a daemon thread at `http://localhost:8070`.
5.  When you open the URL in a web browser, the JavaScript establishes a WebSocket connection.
6.  The server sends the initial hardware state to synchronize the UI.
7.  When the running B.O.S.S. application calls hardware methods (e.g., `led_red.on()`), the mock hardware publishes events to the EventBus.
8.  The WebSocket manager receives these events and broadcasts updates to all connected browsers.
9.  The JavaScript receives the messages and updates the UI in real-time (e.g., turns the red LED indicator on with glowing effect).
10. When you interact with the UI (click buttons, change switches), the JavaScript sends API requests to the server.
11. The server calls the corresponding methods on the mock hardware objects (e.g., `mock_button.press()`).
12. The mock hardware publishes `input.button.pressed` or `input.switch.changed` events to the EventBus.
13. The running application receives these events and reacts accordingly, completing the bidirectional loop.

## User Interface Components

### Input Controls

**Color Buttons**
- Four clickable buttons (Red, Yellow, Green, Blue) with visual feedback
- Large central "GO" button for main actions
- Keyboard shortcuts: 1-4 for color buttons, Spacebar for GO button
- Press animations and visual state feedback

**Switch Controls**
- Decimal input field with validation (0-255)
- 8 individual bit toggle switches for direct binary manipulation
- Real-time binary display showing current value in 8-bit format
- Keyboard shortcuts:
  - Arrow Up/Down: Increment/decrement value
  - R: Reset to 0
  - M: Set to maximum (255)

### Output Indicators

**LED Display**
- Four LED indicators with realistic styling
- Color-coded when ON: Red (#ff4444), Yellow (#ffff00), Green (#44ff44), Blue (#4444ff)
- Gray (#333333) when OFF
- Glowing effects and smooth transitions
- ON/OFF text status labels

**7-Segment Display**
- Retro digital display styling with green text on black background
- Monospace font (Courier New) for authentic appearance
- 4-character width with proper padding
- Glowing text effect for realism

**Main Screen Emulator**
- Canvas-based display (800x480 pixels)
- Maintains 5:3 aspect ratio of physical 7-inch screen
- Text overlay for displaying application output
- Black background with proper scaling
- Handles both text and graphics output

### Developer Tools

**Event Monitor**
- Real-time event log with timestamp and payload information
- Color-coded event categories:
  - Blue: Input events (button presses, switch changes)
  - Orange: Output events (LED, display, screen updates)
  - Purple: System events (app lifecycle, errors)
- Event filtering by category
- JSON payload expansion for debugging
- Clear log functionality
- Configurable log retention (last 100 events)

**Status Indicators**
- Connection status (Connected/Disconnected) with auto-reconnection
- System status display
- Hardware availability information

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| 1 | Press Red button |
| 2 | Press Yellow button |
| 3 | Press Green button |
| 4 | Press Blue button |
| Spacebar | Press GO button |
| ↑ | Increment switch value |
| ↓ | Decrement switch value |
| R | Reset switch to 0 |
| M | Set switch to maximum (255) |

## API Reference

### Button Control
```http
POST /api/button/{button_id}/press
```
- **Parameters**: `button_id` ∈ {red, yellow, green, blue, main}
- **Response**: `{"status": "success", "button": "red", "action": "pressed"}`

### Switch Control
```http
POST /api/switch/set
Content-Type: application/json

{"value": 42}
```
- **Parameters**: `value` (integer, 0-255)
- **Response**: `{"status": "success", "value": 42}`

### LED Control (Manual Testing)
```http
POST /api/led/{color}/set
Content-Type: application/json

{"state": true}
```
- **Parameters**: `color` ∈ {red, yellow, green, blue}, `state` (boolean)
- **Response**: `{"status": "success", "color": "red", "state": true}`

### Display Control
```http
POST /api/display/set
Content-Type: application/json

{"text": "BOSS"}
```
- **Parameters**: `text` (string, up to 4 characters)
- **Response**: `{"status": "success", "text": "BOSS"}`

### Screen Control
```http
POST /api/screen/set
Content-Type: application/json

{"text": "Hello World"}
```
- **Parameters**: `text` (string)
- **Response**: `{"status": "success", "text": "Hello World"}`

```http
POST /api/screen/clear
```
- **Response**: `{"status": "success", "action": "cleared"}`

### System Information
```http
GET /api/system/info
```
- **Response**: Hardware status and connection information

## WebSocket Events

The WebSocket connection at `/ws` receives real-time events in the following format:

```json
{
  "event": "event_type",
  "payload": { /* event-specific data */ },
  "timestamp": 1234567890.123
}
```

### Event Types

**Initial State**
```json
{
  "event": "initial_state",
  "payload": {
    "led_red": false,
    "led_yellow": true,
    "led_green": false,
    "led_blue": false,
    "display": "----",
    "switch_value": 42,
    "screen_content": "Ready"
  }
}
```

**LED State Change**
```json
{
  "event": "led_changed",
  "payload": {
    "led_id": "red",
    "state": "on",
    "timestamp": 1234567890.123,
    "source": "hardware.led.red"
  }
}
```

**Display Update**
```json
{
  "event": "display_changed",
  "payload": {
    "value": "0042",
    "timestamp": 1234567890.123,
    "source": "hardware.display.mock"
  }
}
```

**Screen Update**
```json
{
  "event": "screen_changed",
  "payload": {
    "action": "display_text",
    "details": {
      "text": "Hello World",
      "color": [255, 255, 255],
      "size": 32,
      "align": "center"
    },
    "timestamp": 1234567890.123,
    "source": "hardware.screen.mock"
  }
}
```

**Switch Change**
```json
{
  "event": "switch_changed",
  "payload": {
    "value": 42,
    "previous_value": 0,
    "timestamp": 1234567890.123,
    "source": "webui.switch"
  }
}
```

## Responsive Design

The Web UI is designed to work across different devices:

- **Desktop**: Full feature set with optimal layout
- **Tablet**: Responsive grid layout with touch-friendly controls
- **Mobile**: Simplified layout with essential controls visible

## Troubleshooting

### Connection Issues
- **Symptom**: "Disconnected" status or no real-time updates
- **Solution**: Check that BOSS is running in mock mode and refresh the browser

### Missing Updates
- **Symptom**: UI doesn't reflect hardware changes
- **Solution**: Verify WebSocket connection and check browser console for errors

### API Errors
- **Symptom**: Button clicks or switch changes don't work
- **Solution**: Check browser network tab for failed requests and verify server is running

### Performance Issues
- **Symptom**: Slow or unresponsive UI
- **Solution**: Clear event log, reduce browser tabs, or restart the application

## Development Notes

The Web UI is designed for development and testing purposes. Key characteristics:

- **Security**: Binds to localhost only for development safety
- **Performance**: Optimized for responsiveness with minimal CPU overhead
- **Reliability**: Automatic reconnection and error handling
- **Compatibility**: Works with modern browsers (Chrome, Firefox, Safari, Edge)
- **Accessibility**: Keyboard navigation and focus indicators

For production deployment or remote access, additional security measures and configuration would be required.