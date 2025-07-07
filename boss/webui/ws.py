class WebSocketManager:
    def __init__(self):
        self.clients = set()
        self.hardware = {}  # Filled in by main.py with mock objects

    async def connect(self, ws):
        await ws.accept()
        self.clients.add(ws)
        await ws.send_json(self.get_full_state())

    async def broadcast(self, payload):
        print(f"[WS DEBUG] Broadcasting to {len(self.clients)} clients: {payload}")
        disconnected_clients = set()
        for ws in self.clients:
            try:
                await ws.send_json(payload)
                print(f"[WS DEBUG] Sent message to client successfully")
            except Exception as e:
                print(f"[WS DEBUG] Failed to send to client: {e}")
                disconnected_clients.add(ws)
        
        # Remove disconnected clients
        for ws in disconnected_clients:
            self.clients.discard(ws)

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
                        state["display"] = str(val) if val is not None else None
                elif hasattr(v, "is_on"):
                    state["display"] = v.is_on()
                else:
                    state["display"] = None
            elif k.startswith("led_") or k in ["led_red", "led_yellow", "led_green", "led_blue"]:
                # Handle LEDs consistently
                if hasattr(v, 'is_on'):
                    led_state = v.is_on()
                    state[k] = led_state
                    print(f"[WS DEBUG] LED {k}: is_on() = {led_state}, type = {type(led_state)}")
                elif hasattr(v, 'value'):
                    state[k] = bool(v.value)
                    print(f"[WS DEBUG] LED {k}: value = {v.value}, bool = {bool(v.value)}")
                else:
                    state[k] = False
                    print(f"[WS DEBUG] LED {k}: defaulted to False")
            elif k.startswith("btn_") or k == "main_btn":
                # Skip button objects - we don't need their state in the UI
                continue
            elif k in ["switch_reader", "switch"]:
                # Get switch value
                if hasattr(v, 'read_value'):
                    try:
                        state[k] = v.read_value()
                    except:
                        state[k] = 0
                elif hasattr(v, 'value'):
                    state[k] = v.value
                else:
                    state[k] = 0
            elif k in ["screen"]:
                # Get screen state if needed
                if hasattr(v, 'get_state'):
                    state[k] = v.get_state()
                elif hasattr(v, 'text'):
                    state[k] = v.text
                else:
                    continue  # Skip screen object
            elif k in ["api", "event_bus"]:
                # Skip these objects - not needed in UI state
                continue
            elif hasattr(v, 'is_on'):
                state[k] = v.is_on()
            elif hasattr(v, 'value'):
                state[k] = v.value
            elif hasattr(v, 'text'):
                state[k] = v.text
            elif hasattr(v, 'get_state'):
                state[k] = v.get_state()
            else:
                # Don't send object strings - skip unknown objects
                continue
        print(f"[WS DEBUG] Final state: {state}")
        return state

    async def push_event(self, event):
        print(f"[WS DEBUG] push_event called with: {event}")
        # Handle event structure properly
        if isinstance(event, dict) and "type" in event and "payload" in event:
            # Event from main.py: {"type": event_type, "payload": payload}
            formatted_event = {
                "event": event["type"],
                "payload": event["payload"]
            }
        else:
            # Direct event
            formatted_event = {"event": event}
        
        print(f"[WS DEBUG] Formatted event: {formatted_event}")
        print(f"[WS DEBUG] Number of clients: {len(self.clients)}")
        
        # Always push the event itself
        await self.broadcast(formatted_event)
        # Always push the latest hardware state after any event
        state = self.get_full_state()
        print("[WS] hardware_state:", state)  # DEBUG: print hardware state being sent
        await self.broadcast({"event": "hardware_state", "state": state})
