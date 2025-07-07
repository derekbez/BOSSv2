"""
BOSS Web UI FastAPI Server
Provides REST API and WebSocket endpoints for hardware emulation.
"""
import json
import logging
import time
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger("boss.webui.server")

# Request/Response Models
class ButtonPressRequest(BaseModel):
    pass

class SwitchSetRequest(BaseModel):
    value: int

class LEDSetRequest(BaseModel):
    state: bool

class DisplaySetRequest(BaseModel):
    text: str

class ScreenSetRequest(BaseModel):
    text: str

class WebSocketManager:
    """Manages WebSocket connections and broadcasts hardware state updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.hardware_dict: Dict[str, Any] = {}
        self.event_bus = None
        
    def set_hardware(self, hardware_dict: Dict[str, Any], event_bus):
        """Set the hardware dictionary and event bus reference."""
        self.hardware_dict = hardware_dict
        self.event_bus = event_bus
        
        # Subscribe to all relevant events for real-time updates
        if event_bus:
            event_bus.subscribe("output.led.state_changed", self._on_led_changed)
            event_bus.subscribe("output.display.updated", self._on_display_changed)
            event_bus.subscribe("output.screen.updated", self._on_screen_changed)
            event_bus.subscribe("input.switch.changed", self._on_switch_changed)
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial hardware state
        await self._send_initial_state(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def _send_initial_state(self, websocket: WebSocket):
        """Send the current hardware state to a newly connected client."""
        try:
            state = self._get_current_state()
            await websocket.send_text(json.dumps({
                "event": "initial_state",
                "payload": state,
                "timestamp": time.time()
            }))
        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")
    
    def _get_current_state(self) -> Dict[str, Any]:
        """Get the current state of all hardware components."""
        state = {}
        
        # LED states
        for color in ['red', 'yellow', 'green', 'blue']:
            led = self.hardware_dict.get(f'led_{color}')
            if led and hasattr(led, 'is_on'):
                state[f'led_{color}'] = led.is_on()
            else:
                state[f'led_{color}'] = False
        
        # Display state
        display = self.hardware_dict.get('display')
        if display and hasattr(display, 'last_value'):
            state['display'] = str(display.last_value or "----")
        else:
            state['display'] = "----"
        
        # Switch state
        switch_reader = self.hardware_dict.get('switch_reader')
        if switch_reader and hasattr(switch_reader, 'read_value'):
            state['switch_value'] = switch_reader.read_value()
        else:
            state['switch_value'] = 0
        
        # Screen state (basic text content)
        screen = self.hardware_dict.get('screen')
        if screen and hasattr(screen, 'last_output'):
            state['screen_content'] = str(screen.last_output or "")
        else:
            state['screen_content'] = ""
        
        return state
    
    # Event handlers for real-time updates
    def _on_led_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle LED state change events."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast({
                    "event": "led_changed",
                    "payload": payload,
                    "timestamp": time.time()
                }))
        except Exception as e:
            logger.warning(f"Failed to broadcast LED event: {e}")
    
    def _on_display_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle display update events."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast({
                    "event": "display_changed", 
                    "payload": payload,
                    "timestamp": time.time()
                }))
        except Exception as e:
            logger.warning(f"Failed to broadcast display event: {e}")
    
    def _on_screen_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle screen update events."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast({
                    "event": "screen_changed",
                    "payload": payload, 
                    "timestamp": time.time()
                }))
        except Exception as e:
            logger.warning(f"Failed to broadcast screen event: {e}")
    
    def _on_switch_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle switch change events."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast({
                    "event": "switch_changed",
                    "payload": payload,
                    "timestamp": time.time()
                }))
        except Exception as e:
            logger.warning(f"Failed to broadcast switch event: {e}")

# Global WebSocket manager instance
ws_manager = WebSocketManager()

def create_app(hardware_dict: Dict[str, Any], event_bus) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(title="BOSS Web UI", description="Hardware Emulator for BOSS Development")
    
    # Set up WebSocket manager
    ws_manager.set_hardware(hardware_dict, event_bus)
    
    # Mount static files
    static_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        """Serve the main HTML page."""
        html_path = static_path / "index.html"
        if html_path.exists():
            return html_path.read_text()
        else:
            return """
            <html>
                <head><title>BOSS Web UI</title></head>
                <body>
                    <h1>BOSS Web UI Hardware Emulator</h1>
                    <p>Static files not found. Please check the installation.</p>
                </body>
            </html>
            """
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time communication."""
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming WebSocket messages if needed
                logger.debug(f"Received WebSocket message: {data}")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
    
    # Button API endpoints
    @app.post("/api/button/{button_id}/press")
    async def press_button(button_id: str):
        """Simulate a button press."""
        valid_buttons = ['red', 'yellow', 'green', 'blue', 'main']
        if button_id not in valid_buttons:
            raise HTTPException(status_code=400, detail=f"Invalid button: {button_id}")
        
        button = hardware_dict.get(f'btn_{button_id}')
        if not button:
            raise HTTPException(status_code=404, detail=f"Button {button_id} not found")
        
        # Simulate button press
        if hasattr(button, 'press'):
            button.press()
        
        return {"status": "success", "button": button_id, "action": "pressed"}
    
    # Switch API endpoints  
    @app.post("/api/switch/set")
    async def set_switch(request: SwitchSetRequest):
        """Set the switch value (0-255)."""
        if not 0 <= request.value <= 255:
            raise HTTPException(status_code=400, detail="Switch value must be between 0 and 255")
        
        switch_reader = hardware_dict.get('switch_reader')
        if not switch_reader:
            raise HTTPException(status_code=404, detail="Switch reader not found")
        
        # Set switch value
        if hasattr(switch_reader, 'set_value'):
            switch_reader.set_value(request.value)
        
        return {"status": "success", "value": request.value}
    
    # LED API endpoints (for manual control)
    @app.post("/api/led/{color}/set") 
    async def set_led(color: str, request: LEDSetRequest):
        """Set LED state manually."""
        valid_colors = ['red', 'yellow', 'green', 'blue']
        if color not in valid_colors:
            raise HTTPException(status_code=400, detail=f"Invalid LED color: {color}")
        
        led = hardware_dict.get(f'led_{color}')
        if not led:
            raise HTTPException(status_code=404, detail=f"LED {color} not found")
        
        # Set LED state
        if request.state:
            if hasattr(led, 'on'):
                led.on()
        else:
            if hasattr(led, 'off'):
                led.off()
        
        return {"status": "success", "color": color, "state": request.state}
    
    # Display API endpoints
    @app.post("/api/display/set")
    async def set_display(request: DisplaySetRequest):
        """Set the 7-segment display content."""
        display = hardware_dict.get('display')
        if not display:
            raise HTTPException(status_code=404, detail="Display not found")
        
        # Set display content
        if hasattr(display, 'show_message'):
            display.show_message(request.text)
        
        return {"status": "success", "text": request.text}
    
    # Screen API endpoints
    @app.post("/api/screen/set")
    async def set_screen(request: ScreenSetRequest):
        """Set screen content."""
        screen = hardware_dict.get('screen')
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Set screen content
        if hasattr(screen, 'display_text'):
            screen.display_text(request.text)
        
        return {"status": "success", "text": request.text}
    
    @app.post("/api/screen/clear")
    async def clear_screen():
        """Clear the screen."""
        screen = hardware_dict.get('screen')
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Clear screen
        if hasattr(screen, 'clear'):
            screen.clear()
        
        return {"status": "success", "action": "cleared"}
    
    # System info endpoints
    @app.get("/api/system/info")
    async def get_system_info():
        """Get system information and hardware status."""
        info = {
            "hardware_status": {},
            "connections": len(ws_manager.active_connections),
            "timestamp": time.time()
        }
        
        # Check hardware component availability
        components = ['btn_red', 'btn_yellow', 'btn_green', 'btn_blue', 'btn_main',
                     'led_red', 'led_yellow', 'led_green', 'led_blue', 
                     'display', 'switch_reader', 'screen']
        
        for component in components:
            info["hardware_status"][component] = component in hardware_dict and hardware_dict[component] is not None
        
        return info
    
    @app.get("/api/apps")
    async def list_apps():
        """List available applications."""
        # This would integrate with the app manager
        return {"apps": [], "message": "App listing not yet implemented"}
    
    return app
