from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from .handlers import register_routes
from .ws import WebSocketManager

app = FastAPI()
app.mount("/static", StaticFiles(directory="boss/webui/static", html=True), name="static")

ws_manager = WebSocketManager()
register_routes(app, ws_manager)

@app.get("/")
async def root():
    # Serve index.html from the static directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)