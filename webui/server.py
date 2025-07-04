from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from boss.web_ui.handlers import register_routes
from boss.web_ui.ws import WebSocketManager

app = FastAPI()
app.mount("/", StaticFiles(directory="boss/web_ui/static", html=True), name="static")

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()

# Register API routes and pass mock hardware
register_routes(app, ws_manager)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
