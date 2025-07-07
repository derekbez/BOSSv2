"""
B.O.S.S. Web UI Main Module
Provides a web-based debug dashboard for development and testing.
"""

import logging
import threading
from typing import Dict, Any
import uvicorn
from boss.webui.server import create_app

logger = logging.getLogger(__name__)

def start_web_ui(hardware_dict: Dict[str, Any], event_bus, port=8070) -> None:
    """
    Start the web UI debug dashboard for development mode.
    
    Args:
        hardware_dict: Dictionary containing all hardware device instances
        event_bus: The main event bus for publishing events
        port: Port to run the server on (default: 8070)
    """
    try:
        app = create_app(hardware_dict, event_bus)
        
        def run_server():
            uvicorn.run(
                app, 
                host="127.0.0.1", 
                port=port,
                log_level="warning"  # Reduce uvicorn noise
            )
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        logger.info(f"BOSS Web UI started at http://localhost:{port}")
        logger.info("Web UI debug dashboard initialized")
        logger.info("Available hardware devices:")
        for name, device in hardware_dict.items():
            if device:
                logger.info(f"  {name}: {type(device).__name__}")
        
    except Exception as e:
        logger.error(f"Failed to start web UI: {e}")
        raise
