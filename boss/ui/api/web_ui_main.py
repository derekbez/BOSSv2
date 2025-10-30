"""
B.O.S.S. Web UI Main Module
Provides a web-based debug dashboard for development and testing.
"""

import logging
import signal
import socket
import threading
from typing import Dict, Any, Optional
import uvicorn
from boss.ui.api.web_ui import create_app

logger = logging.getLogger(__name__)

# Global server instance for shutdown control
_server_instance = None
_server_thread = None

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True

def is_webui_running(port: int = 8070) -> bool:
    """Check if the WebUI is already running by testing if we can connect to the port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            return result == 0  # 0 means connection successful
    except (OSError, ConnectionError):
        return False

def find_available_port(start_port: int = 8070, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def start_web_ui(hardware_dict: Dict[str, Any], event_bus, port=8070) -> Optional[int]:
    """
    Start the web UI debug dashboard for development mode.
    
    Args:
        hardware_dict: Dictionary containing all hardware device instances
        event_bus: The main event bus for publishing events
        port: Port to run the server on (default: 8070)
        
    Returns:
        The port number the WebUI is running on, or None if failed to start
    """
    # Check if WebUI is already running on the requested port
    if is_webui_running(port):
        logger.info(f"WebUI is already running on port {port}")
        logger.info(f"Access it at http://localhost:{port}")
        return port
    
    # Check if port is in use by something else
    if is_port_in_use(port):
        logger.warning(f"Port {port} is in use by another service")
        # Try to find an alternative port
        alt_port = find_available_port(port + 1)
        if alt_port:
            logger.info(f"Using alternative port {alt_port}")
            port = alt_port
        else:
            logger.error("No available ports found for WebUI")
            return None
    
    try:
        app = create_app(hardware_dict, event_bus)
        
        def run_server():
            global _server_instance
            try:
                config = uvicorn.Config(
                    app, 
                    host="127.0.0.1", 
                    port=port,
                    log_level="warning",  # Reduce uvicorn noise
                    access_log=False      # Disable access logs
                )
                _server_instance = uvicorn.Server(config)
                _server_instance.run()
            except Exception as e:
                logger.error(f"Uvicorn server error: {e}")
        
        global _server_thread
        _server_thread = threading.Thread(target=run_server, daemon=True)
        _server_thread.start()
        
        logger.info(f"BOSS Web UI started at http://localhost:{port}")
        logger.info("Web UI debug dashboard initialized")
        logger.info("Available hardware devices:")
        for name, device in hardware_dict.items():
            if device:
                logger.info(f"  {name}: {type(device).__name__}")
        
        return port
        
    except Exception as e:
        logger.error(f"Failed to start web UI: {e}")
        return None


def stop_web_ui():
    """Stop the WebUI server if it's running."""
    global _server_instance, _server_thread
    
    if _server_instance:
        try:
            logger.info("Stopping WebUI server...")
            _server_instance.should_exit = True
            if hasattr(_server_instance, 'force_exit'):
                _server_instance.force_exit = True
            
            # Give it a moment to shutdown gracefully
            if _server_thread and _server_thread.is_alive():
                _server_thread.join(timeout=2.0)
                
            _server_instance = None
            _server_thread = None
            logger.info("WebUI server stopped")
        except Exception as e:
            logger.warning(f"Error stopping WebUI server: {e}")
    else:
        logger.debug("No WebUI server to stop")
