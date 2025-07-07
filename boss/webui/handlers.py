from fastapi import Request
import platform


# --- Web UI API route handlers for BOSS debug dashboard ---
def press_button_handler(ws_manager, button_id: str):
    event_bus = ws_manager.hardware.get("event_bus")
    if event_bus:
        event_bus.publish("input.button.pressed", {"button_id": button_id})
    return {"status": "ok"}


def set_switch_handler(ws_manager, value):
    event_bus = ws_manager.hardware.get("event_bus")
    if event_bus:
        event_bus.publish("input.switch.set", {"value": value})
    return {"value": value}


def set_led_handler(ws_manager, color, state):
    event_bus = ws_manager.hardware.get("event_bus")
    if event_bus:
        event_bus.publish("output.led.set", {"color": color, "state": state})
    return {"status": "ok", "state": state}


def set_display_handler(ws_manager, text):
    event_bus = ws_manager.hardware.get("event_bus")
    if event_bus:
        event_bus.publish("output.display.set", {"text": text})
    return {"status": "ok", "text": text}


def set_screen_handler(ws_manager, text):
    event_bus = ws_manager.hardware.get("event_bus")
    if event_bus:
        event_bus.publish("output.screen.set", {"text": text})
    return {"status": "ok", "text": text}


def list_apps_handler(ws_manager):
    api = ws_manager.hardware.get("api")
    if api and hasattr(api, "list_apps"):
        return {"apps": api.list_apps()}
    return {"apps": []}


def start_app_handler(ws_manager, app_name):
    api = ws_manager.hardware.get("api")
    if api and hasattr(api, "launch_app"):
        api.launch_app(app_name)
        return {"status": "started", "app": app_name}
    return {"status": "error", "error": "API or launch_app not found"}


def stop_app_handler(ws_manager, app_name):
    api = ws_manager.hardware.get("api")
    if api and hasattr(api, "stop_app"):
        api.stop_app(app_name)
        return {"status": "stopped", "app": app_name}
    return {"status": "error", "error": "API or stop_app not found"}


def system_info_handler(ws_manager):
    import platform
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "mocked": [k for k, v in ws_manager.hardware.items() if hasattr(v, 'is_mock') and v.is_mock],
    }


def register_routes(app, ws_manager):
    # Button press
    @app.post("/api/button/{button_id}/press")
    async def press_button(button_id: str):
        return press_button_handler(ws_manager, button_id)

    # Switch set
    @app.post("/api/switch/set")
    async def set_switch(req: Request):
        data = await req.json()
        value = data.get("value")
        return set_switch_handler(ws_manager, value)

    # LED control
    @app.post("/api/led/{color}/set")
    async def set_led(color: str, req: Request):
        data = await req.json()
        state = data.get("state")
        return set_led_handler(ws_manager, color, state)

    # Display text
    @app.post("/api/display/set")
    async def set_display(req: Request):
        data = await req.json()
        text = data.get("text")
        return set_display_handler(ws_manager, text)

    # Screen text
    @app.post("/api/screen/set")
    async def set_screen(req: Request):
        data = await req.json()
        text = data.get("text")
        return set_screen_handler(ws_manager, text)

    # List apps
    @app.get("/api/apps")
    async def list_apps():
        return list_apps_handler(ws_manager)

    # Launch app
    @app.post("/api/app/{app_name}/start")
    async def start_app(app_name: str):
        return start_app_handler(ws_manager, app_name)

    # Stop app
    @app.post("/api/app/{app_name}/stop")
    async def stop_app(app_name: str):
        return stop_app_handler(ws_manager, app_name)

    # System info
    @app.get("/api/system/info")
    async def system_info():
        return system_info_handler(ws_manager)
