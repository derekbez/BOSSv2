from boss.webui.server import app, ws_manager
import uvicorn
import threading

def start_web_ui(hardware):
    ws_manager.hardware = hardware
    # Use 127.0.0.1 for local dev, and fix static path issues
    threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8070)).start()
