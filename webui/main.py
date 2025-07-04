from boss.web_ui.server import app, ws_manager
import uvicorn
import threading

def start_web_ui(hardware):
    ws_manager.hardware = hardware
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000)).start()
