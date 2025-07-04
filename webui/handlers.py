from fastapi import Request

def register_routes(app, ws_manager):
    @app.post("/api/button/{button_id}/press")
    async def press_button(button_id: str):
        hw = ws_manager.hardware.get(f"button_{button_id}")
        if hw:
            hw.press()  # Publishes EventBus event
        return {"status": "ok"}

    @app.post("/api/switch/set")
    async def set_switch(req: Request):
        data = await req.json()
        value = data.get("value")
        ws_manager.hardware["switch"].set(value)
        return {"value": value}
