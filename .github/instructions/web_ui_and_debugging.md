# Web UI & Debugging

## Purpose
The Web UI provides an emulated view of hardware state (LEDs, display, screen buffer, switches) and interaction endpoints for development.

## Starting WebUI
- Command-line: `python -m boss.main --hardware webui`
- Environment: `BOSS_DEV_MODE=1` (forces WebUI + DEBUG logging)
- Port from config (`webui_port`, default 8070). Chooses alternative if occupied.

## Components
- FastAPI app mounted at `/` (static assets: HTML/JS/CSS).
- WebSocket endpoint: `/ws` for real-time event broadcasts.
- REST endpoints (examples):
  - `POST /api/button/{color}/press`
  - `POST /api/switch/set {"value": <0-255>}`
  - `POST /api/display/set {"text": "1234"}`
  - `POST /api/screen/set {"text": "Hello"}`
  - `GET /api/state` (snapshot of current hardware state)
  - `GET /api/system/info`

## Event Broadcasting
Server subscribes to core output + input events:
- `output.led.state_changed`
- `output.display.updated`
- `output.screen.updated`
- `input.switch.changed`

Messages sent via WebSocket as JSON:
```json
{
  "event": "led_changed",
  "payload": {"color": "red", "is_on": true},
  "timestamp": 1731950000.123
}
```

## Debug Workflow
1. Start WebUI mode.
2. Open browser at `http://localhost:8070`.
3. Flip virtual switches / press buttons.
4. Observe log output for event publishing and handler activity.

## Common Checks
| Issue | Check |
|-------|-------|
| No updates in UI | Confirm events being published (logging) |
| Button ignored | LED gating: LED must be ON |
| Wrong port | Look for alternative port log message |
| Screen not updating | Ensure `output.screen.updated` events emitted |

## Performance Tips
- Avoid flooding WebSocket with redundant display updates.
- Batch screen text changes when generating large content.

## Anti-Patterns
- Publishing both legacy and canonical event names.
- Treating WebUI-only features as production-specific logic.

## Checklist Before Using For App Dev
- WebSocket connects successfully.
- `/api/state` reflects expected LED gating.
- Display updates appear or fallback placeholder "----".

Next: `testing_strategy.md`.
