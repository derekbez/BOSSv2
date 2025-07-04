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
        return {
            "led_red": self.hardware["led_red"].is_on(),
            "display": self.hardware["seven_segment"].value,
            "screen": self.hardware["screen"].text,
            "switch": self.hardware["switch"].value
        }
