class WebSocketManager:
    def __init__(self):
        self.clients = set()
        self.hardware = {}  # Filled in by main.py with mock objects

    async def connect(self, ws):
        await ws.accept()
        self.clients.add(ws)
        await ws.send_json(self.get_full_state())

    async def broadcast(self, payload):
        for ws in self.clients:
            await ws.send_json(payload)

    def get_full_state(self):
        # Snapshot all current hardware states for new clients
        state = {}
        for k, v in self.hardware.items():
            if k == "display":
                # Always use last_value for display, trim whitespace for UI
                if hasattr(v, "last_value"):
                    val = v.last_value
                    if isinstance(val, str):
                        state["display"] = val.strip()
                    else:
                        state["display"] = val
                elif hasattr(v, "is_on"):
                    state["display"] = v.is_on()
                else:
                    state["display"] = None
            elif hasattr(v, 'is_on'):
                state[k] = v.is_on()
            elif hasattr(v, 'value'):
                state[k] = v.value
            elif hasattr(v, 'text'):
                state[k] = v.text
            elif hasattr(v, 'get_state'):
                state[k] = v.get_state()
            else:
                state[k] = str(v)
        return state

    async def push_event(self, event):
        # Always push the event itself
        await self.broadcast({"event": event})
        # Always push the latest hardware state after any event
        state = self.get_full_state()
        print("[WS] hardware_state:", state)  # DEBUG: print hardware state being sent
        await self.broadcast({"event": "hardware_state", "state": state})
