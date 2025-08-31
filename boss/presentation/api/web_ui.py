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

logger = logging.getLogger("boss.presentation.api.web_ui")

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
        self.loop = None
        
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
            event_bus.subscribe("switch_change", self._on_switch_changed)  # legacy name
            event_bus.subscribe("switch_changed", self._on_switch_changed)  # canonical name
            # Display events: prefer canonical and output updates. Avoid legacy duplicate events.
            event_bus.subscribe("display_update", self._on_display_changed)  # canonical name
            event_bus.subscribe("output.display.updated", self._on_display_changed)
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Store the event loop when we first get an async context
            if self.loop is None:
                import asyncio
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    self.loop = asyncio.get_event_loop()
            
            logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
            
            # Send initial hardware state
            await self._send_initial_state(websocket)
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

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
                logger.debug(f"Failed to send message to client: {e}")
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
        leds = self.hardware_dict.get('leds')
        if leds:
            try:
                from boss.domain.models.hardware_state import LedColor
                for color in ['red', 'yellow', 'green', 'blue']:
                    led_color = LedColor(color)
                    if hasattr(leds, 'get_led_state'):
                        led_state = leds.get_led_state(led_color)
                        state[f'led_{color}'] = led_state.is_on if led_state else False
                    else:
                        state[f'led_{color}'] = False
            except Exception as e:
                logger.debug(f"Error getting LED states: {e}")
                for color in ['red', 'yellow', 'green', 'blue']:
                    state[f'led_{color}'] = False
        else:
            for color in ['red', 'yellow', 'green', 'blue']:
                state[f'led_{color}'] = False
        
        # Display state
        display = self.hardware_dict.get('display')
        if display:
            # Prefer a current numeric value if available, else fall back to last value, else placeholder
            if hasattr(display, '_current_value') and getattr(display, '_current_value') is not None:
                state['display'] = str(getattr(display, '_current_value'))
            elif hasattr(display, '_last_value') and getattr(display, '_last_value') is not None:
                state['display'] = str(getattr(display, '_last_value'))
            else:
                state['display'] = "----"
        else:
            state['display'] = "----"
        
        # Switch state
        switches = self.hardware_dict.get('switches')
        if switches:
            if hasattr(switches, 'read_switches'):
                switch_state = switches.read_switches()
                state['switch_value'] = switch_state.value if switch_state else 0
            elif hasattr(switches, '_switch_value'):
                state['switch_value'] = switches._switch_value
            else:
                state['switch_value'] = 0
        else:
            state['switch_value'] = 0
        
        # Screen state
        screen = self.hardware_dict.get('screen')
        if screen:
            # Try different attributes that might contain screen content
            content = ""
            if hasattr(screen, 'last_output'):
                content = str(screen.last_output or "")
            elif hasattr(screen, 'current_content'):
                content = str(screen.current_content or "")
            elif hasattr(screen, 'buffer'):
                content = str(screen.buffer or "")
            elif hasattr(screen, 'content'):
                content = str(screen.content or "")
            elif hasattr(screen, '_content'):
                content = str(screen._content or "")
            state['screen_content'] = content
        else:
            state['screen_content'] = ""
        
        return state
    
    def _schedule_broadcast(self, message: dict):
        """Schedule a broadcast message, handling different thread contexts."""
        import asyncio
        
        if not self.active_connections:
            return  # No connections, skip broadcast
            
        try:
            # Try to get the current running loop
            try:
                current_loop = asyncio.get_running_loop()
                # If we're in the same loop as stored, create task directly
                if self.loop and current_loop == self.loop:
                    asyncio.create_task(self.broadcast(message))
                elif self.loop and self.loop.is_running():
                    # We're in a different thread, schedule on the stored loop
                    asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
                else:
                    logger.warning("No valid event loop available for broadcast")
            except RuntimeError:
                # No running loop in current thread
                if self.loop and self.loop.is_running():
                    # Schedule on the stored loop from another thread
                    asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
                else:
                    logger.warning("No event loop available for WebSocket broadcast")
        except Exception as e:
            logger.error(f"Failed to schedule broadcast: {e}")

    # Event handlers for real-time updates
    def _on_led_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle LED state change events."""
        self._schedule_broadcast({
            "event": "led_changed",
            "payload": payload,
            "timestamp": time.time()
        })

    def _on_display_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle display update events."""
        self._schedule_broadcast({
            "event": "display_changed",
            "payload": payload,
            "timestamp": time.time()
        })

    def _on_screen_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle screen update events."""
        self._schedule_broadcast({
            "event": "screen_changed",
            "payload": payload,
            "timestamp": time.time()
        })

    def _on_switch_changed(self, event_type: str, payload: Dict[str, Any]):
        """Handle switch change events."""
        self._schedule_broadcast({
            "event": "switch_changed",
            "payload": payload,
            "timestamp": time.time()
        })

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
            return html_path.read_text(encoding="utf-8")
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
        
        # Handle button presses through the hardware components
        logger.info(f"WebUI button press request: {button_id}")
        
        if button_id == 'main':
            # Main Go button
            go_button = hardware_dict.get('go_button')
            logger.info(f"Go button object: {go_button}")
            if go_button and hasattr(go_button, 'handle_press'):
                go_button.handle_press()
                logger.info("Go button handle_press called")
            elif go_button and hasattr(go_button, '_press_callback') and go_button._press_callback:
                go_button._press_callback()
                logger.info("Go button callback called")
            else:
                logger.warning("Go button not properly connected")
        else:
            # Color buttons - check if LED is on before processing button press
            buttons = hardware_dict.get('buttons')
            leds = hardware_dict.get('leds')
            
            # Check if the corresponding LED is active
            led_is_active = False
            if leds and hasattr(leds, 'get_led_state'):
                try:
                    from boss.domain.models.hardware_state import LedColor
                    led_color = LedColor(button_id)
                    led_state = leds.get_led_state(led_color)
                    led_is_active = led_state.is_on if led_state else False
                except (ValueError, AttributeError):
                    led_is_active = False
            
            if not led_is_active:
                logger.info(f"Button {button_id} press ignored - corresponding LED is OFF (button not active)")
                return {"status": "ignored", "button": button_id, "reason": "LED not active"}
            
            # Process button press since LED is active
            if buttons and hasattr(buttons, 'handle_button_press'):
                logger.debug(f"Processing {button_id} button press (LED is active)")
                buttons.handle_button_press(button_id)
                logger.info(f"Color button {button_id} press processed successfully")
            else:
                logger.error(f"Button {button_id} hardware not properly initialized - buttons object: {buttons}")
                raise HTTPException(status_code=500, detail=f"Button hardware not available for {button_id}")
        
        return {"status": "success", "button": button_id, "action": "pressed"}
    
    # Switch API endpoints  
    @app.post("/api/switch/set")
    async def set_switch(request: SwitchSetRequest):
        """Set the switch value (0-255)."""
        if not 0 <= request.value <= 255:
            raise HTTPException(status_code=400, detail="Switch value must be between 0 and 255")
        
        switches = hardware_dict.get('switches')
        if not switches:
            raise HTTPException(status_code=404, detail="Switches not found")
        
        # Set switch value using the WebUI hardware method
        if hasattr(switches, 'handle_switch_change'):
            switches.handle_switch_change(request.value)
        else:
            logger.warning("Switch handle_switch_change method not available")
        
        # Publish a canonical system display_update so every backend mirrors the value
        if event_bus:
            event_bus.publish("display_update", {"value": request.value}, "system")
        
        return {"status": "success", "value": request.value}
    
    # LED API endpoints (for manual control)
    @app.post("/api/led/{color}/set") 
    async def set_led(color: str, request: LEDSetRequest):
        """Set LED state manually."""
        valid_colors = ['red', 'yellow', 'green', 'blue']
        if color not in valid_colors:
            raise HTTPException(status_code=400, detail=f"Invalid LED color: {color}")
        
        leds = hardware_dict.get('leds')
        if not leds:
            raise HTTPException(status_code=404, detail=f"LEDs not found")
        
        # Set LED state using the proper LED interface
        try:
            from boss.domain.models.hardware_state import LedColor
            led_color = LedColor(color)
            if hasattr(leds, 'set_led'):
                leds.set_led(led_color, request.state)
            else:
                logger.warning(f"LED set_led method not available")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid LED color: {color}")
        
        return {"status": "success", "color": color, "state": request.state}
    
    # Display API endpoints
    @app.post("/api/display/set")
    async def set_display(request: DisplaySetRequest):
        """Set the 7-segment display content."""
        display = hardware_dict.get('display')
        if not display:
            raise HTTPException(status_code=404, detail="Display not found")
        
        # Try to parse as number first, then fallback to text
        try:
            # If it's a number, use show_number
            number = int(request.text)
            if hasattr(display, 'show_number') and 0 <= number <= 9999:
                display.show_number(number)
            elif hasattr(display, 'show_text'):
                display.show_text(request.text)
        except ValueError:
            # Not a number, show as text
            if hasattr(display, 'show_text'):
                display.show_text(request.text)
        
        return {"status": "success", "text": request.text}
    
    # Screen API endpoints
    @app.post("/api/screen/set")
    async def set_screen(request: ScreenSetRequest):
        """Set screen content."""
        screen = hardware_dict.get('screen')
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Set screen content using various methods
        if hasattr(screen, 'display_text'):
            screen.display_text(request.text)
        elif hasattr(screen, 'show_text'):
            screen.show_text(request.text)
        elif hasattr(screen, 'print'):
            screen.print(request.text)
        
        # Manually trigger screen update event for web UI
        if event_bus:
            event_bus.publish("screen_update", {
                "text": request.text,
                "screen_content": request.text,
                "timestamp": time.time()
            })
        
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
        
        # Manually trigger screen clear event for web UI
        if event_bus:
            event_bus.publish("screen_update", {
                "text": "",
                "screen_content": "",
                "action": "clear",
                "timestamp": time.time()
            })
        
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

    @app.get("/api/state")
    async def get_state():
        """Get the current emulated hardware state (LEDs, display, switches, screen)."""
        try:
            return {"state": ws_manager._get_current_state(), "timestamp": time.time()}
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/apps")
    async def list_apps():
        """List available applications."""
        # This would integrate with the app manager
        return {"apps": [], "message": "App listing not yet implemented"}
    
    return app
