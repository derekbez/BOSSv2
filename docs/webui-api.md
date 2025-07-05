# BOSS Web UI Debug API Documentation

This document describes the HTTP API endpoints provided by the BOSS Web UI debug dashboard for development and testing.

## Endpoints

### Simulate Button Press
- **POST** `/api/button/{button_id}/press`
- Simulate a button press (red, yellow, green, blue, main).
- Example: `/api/button/red/press`

### Set Switch Value
- **POST** `/api/switch/set`
- Set the switch value (0-255).
- Body: `{ "value": 123 }`

### Set LED State
- **POST** `/api/led/{color}/set`
- Set the state of a color LED (on/off).
- Body: `{ "state": true }` (on) or `{ "state": false }` (off)
- Example: `/api/led/red/set`

### Set 7-Segment Display Text
- **POST** `/api/display/set`
- Set the text on the 7-segment display.
- Body: `{ "text": "BOSS" }`

### Set Screen Text
- **POST** `/api/screen/set`
- Set the text on the main screen.
- Body: `{ "text": "Hello" }`

### List Available Mini-Apps
- **GET** `/api/apps`
- Returns a list of available mini-apps (requires AppAPI with `list_apps` method).

### Launch Mini-App
- **POST** `/api/app/{app_name}/start`
- Launch a mini-app by name (requires AppAPI with `launch_app` method).

### Stop Mini-App
- **POST** `/api/app/{app_name}/stop`
- Stop a mini-app by name (requires AppAPI with `stop_app` method).

### System Info
- **GET** `/api/system/info`
- Returns system/platform info and which hardware is mocked.

---

**Note:** All endpoints return JSON responses. Some endpoints require the AppAPI to be present in the hardware dictionary with the appropriate methods implemented.
