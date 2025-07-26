"""
System Service - Manages overall system lifecycle and coordination.
"""

import logging
import os
import signal
import sys
import threading
from typing import Dict, Any, Optional
from boss.domain.interfaces.services import SystemService

logger = logging.getLogger(__name__)


class SystemManager(SystemService):
    """Service for managing the overall BOSS system."""
    
    def __init__(self, event_bus, hardware_service, app_manager, app_runner):
        self.event_bus = event_bus
        self.hardware_service = hardware_service
        self.app_manager = app_manager
        self.app_runner = app_runner
        
        self._running = False
        self._shutdown_event = threading.Event()
        self._webui_port = None  # Track WebUI port for shutdown
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Set up event subscriptions
        self._setup_event_handlers()
    
    def start(self) -> None:
        """Start the BOSS system."""
        if self._running:
            logger.warning("System already running")
            return
        
        logger.info("Starting BOSS system")
        
        try:
            # Start event bus
            self.event_bus.start()
            
            # Initialize hardware
            self.hardware_service.initialize()
            
            # Load apps
            self.app_manager.load_apps()
            
            # Start hardware monitoring
            self.hardware_service.start_monitoring()
            
            # Mark system as running
            self._running = True
            
            # Start WebUI development interface if needed
            hardware_type = getattr(self.hardware_service.hardware_factory, 'hardware_type', 'unknown')
            self.start_webui_if_needed(hardware_type)
            
            # Run startup app to give immediate feedback
            self._run_startup_app()
            
            # Publish system started event
            self.event_bus.publish("system_started", {"hardware_type": hardware_type}, "system")
            
            logger.info("BOSS system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start BOSS system: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the BOSS system."""
        if not self._running:
            return
        
        logger.info("Stopping BOSS system")
        
        # Mark as stopping
        self._running = False
        
        # Publish shutdown event
        self.event_bus.publish("system_shutdown", {"reason": "normal"}, "system")
        
        try:
            # Stop WebUI development interface
            self.stop_webui_if_running()
            
            # Stop current app
            self.app_runner.stop_current_app()
            
            # Stop hardware monitoring
            self.hardware_service.stop_monitoring()
            
            # Clean up hardware
            self.hardware_service.cleanup()
            
            # Stop event bus
            self.event_bus.stop()
            
            logger.info("BOSS system stopped")
            
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")
        
        # Signal shutdown complete
        self._shutdown_event.set()
    
    def start_webui_if_needed(self, hardware_type: str) -> None:
        """Start WebUI development interface if using webui hardware type."""
        if hardware_type == "webui":
            try:
                from boss.presentation.api.web_ui_main import start_web_ui
                
                # Create hardware dictionary for WebUI
                hardware_dict = {
                    'buttons': self.hardware_service.buttons,
                    'go_button': self.hardware_service.go_button, 
                    'leds': self.hardware_service.leds,
                    'switches': self.hardware_service.switches,
                    'display': self.hardware_service.display,
                    'screen': self.hardware_service.screen
                }
                
                # Start WebUI in background
                port = start_web_ui(hardware_dict, self.event_bus)
                if port:
                    self._webui_port = port
                    logger.info(f"WebUI development interface started at http://localhost:{port}")
                else:
                    logger.warning("Failed to start WebUI development interface")
                    
            except Exception as e:
                logger.warning(f"Could not start WebUI development interface: {e}")
    
    def stop_webui_if_running(self) -> None:
        """Stop WebUI development interface if it's running."""
        if self._webui_port:
            try:
                from boss.presentation.api.web_ui_main import stop_web_ui
                stop_web_ui()
                logger.info(f"WebUI development interface on port {self._webui_port} stopped")
                self._webui_port = None
            except Exception as e:
                logger.warning(f"Error stopping WebUI: {e}")
    
    def _run_startup_app(self) -> None:
        """Run the admin_startup app to provide immediate visual feedback."""
        try:
            # Look for admin_startup app
            startup_app = None
            
            # Try to find the startup app by name
            all_apps = self.app_manager.get_all_apps()
            for app in all_apps.values():  # Iterate over App objects, not dictionary keys
                if app.manifest.name == "admin_startup" or app.app_path.name == "admin_startup":
                    startup_app = app
                    break
            
            if startup_app:
                logger.info("Running startup app for visual feedback")
                # Run the startup app briefly
                self.app_runner.start_app(startup_app)
                
                # The startup app should exit quickly on its own
                # We don't need to explicitly stop it since it's designed to self-terminate
                
            else:
                logger.info("No admin_startup app found - skipping startup feedback")
                # Provide basic feedback instead
                self._provide_basic_startup_feedback()
                
        except Exception as e:
            logger.warning(f"Error running startup app: {e}")
            # Fallback to basic feedback
            self._provide_basic_startup_feedback()
    
    def _provide_basic_startup_feedback(self) -> None:
        """Provide basic startup feedback if no startup app is available."""
        try:
            # Basic LED blink to show system is alive
            for color in ['red', 'yellow', 'green', 'blue']:
                try:
                    from boss.domain.models.hardware_state import LedColor
                    led_color = LedColor(color)
                    if hasattr(self.hardware_service, 'leds') and self.hardware_service.leds:
                        self.hardware_service.leds.set_led(led_color, True)
                except Exception:
                    pass
            
            # Brief pause
            import time
            time.sleep(0.3)
            
            # Turn off LEDs
            for color in ['red', 'yellow', 'green', 'blue']:
                try:
                    from boss.domain.models.hardware_state import LedColor
                    led_color = LedColor(color)
                    if hasattr(self.hardware_service, 'leds') and self.hardware_service.leds:
                        self.hardware_service.leds.set_led(led_color, False)
                except Exception:
                    pass
            
            # Show "READY" on display
            try:
                if hasattr(self.hardware_service, 'display') and self.hardware_service.display:
                    # Try to show a number first, then text
                    try:
                        self.hardware_service.display.show_number(0)  # Show 0000
                    except:
                        self.hardware_service.display.show_text("BOSS")
            except Exception:
                pass
                
            logger.info("Basic startup feedback completed")
            
        except Exception as e:
            logger.debug(f"Error providing basic startup feedback: {e}")
    
    def restart(self) -> None:
        """Restart the BOSS system."""
        logger.info("Restarting BOSS system")
        self.stop()
        self.start()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        current_app = self.app_runner.get_running_app()
        hardware_state = self.hardware_service.get_hardware_state()
        
        return {
            "running": self._running,
            "hardware_type": getattr(self.hardware_service.hardware_factory, 'hardware_type', 'unknown'),
            "current_app": current_app.to_dict() if current_app else None,
            "switch_value": hardware_state.switches.value,
            "apps_loaded": len(self.app_manager.get_all_apps()),
            "event_bus_stats": self.event_bus.get_stats()
        }
    
    def wait_for_shutdown(self) -> None:
        """Wait for system shutdown to complete."""
        try:
            # Wait for shutdown event with periodic timeout to allow interruption
            while not self._shutdown_event.is_set():
                # Wait in short intervals to allow KeyboardInterrupt to be caught
                if self._shutdown_event.wait(timeout=0.5):
                    break  # Shutdown event was set
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt in wait_for_shutdown - setting shutdown event")
            self._shutdown_event.set()
    
    def _setup_event_handlers(self) -> None:
        """Set up system event handlers."""
        # Handle app launch requests (from Go button or API)
        self.event_bus.subscribe("app_launch_requested", self._on_app_launch_requested)
        self.event_bus.subscribe("go_button_pressed", self._on_go_button_pressed)
        
        # Handle admin shutdown requests
        self.event_bus.subscribe("system_shutdown", self._on_system_shutdown_requested)
        
        # Note: Hardware output events (led_update, display_update, screen_update) 
        # are now handled by HardwareEventHandler to avoid duplication
    
    def _on_app_launch_requested(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle app launch requests."""
        try:
            # Get current switch value
            hardware_state = self.hardware_service.get_hardware_state()
            switch_value = hardware_state.switches.value
            
            # Find app for switch value
            app = self.app_manager.get_app_by_switch_value(switch_value)
            
            if app:
                logger.info(f"Launching app for switch {switch_value}: {app.manifest.name}")
                self.app_runner.start_app(app)
                self.app_manager.set_current_app(app)
            else:
                logger.warning(f"No app mapped to switch value {switch_value}")
                # Could show an error on screen here
                
        except Exception as e:
            logger.error(f"Error launching app: {e}")
    
    def _on_go_button_pressed(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle Go button press."""
        # Trigger app launch
        self.event_bus.publish("app_launch_requested", {}, "system")
    
    def _on_system_shutdown_requested(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle system shutdown requests from admin apps."""
        reason = payload.get("reason", "normal")
        logger.info(f"System shutdown requested: {reason}")
        
        if reason == "reboot":
            # Reboot system
            logger.info("Performing system reboot")
            import subprocess
            import sys
            self.stop()  # Graceful BOSS shutdown first
            if sys.platform.startswith('linux'):
                subprocess.run(["sudo", "reboot"], check=False)
            else:
                logger.warning("Reboot not supported on this platform")
                
        elif reason == "poweroff":
            # Power off system  
            logger.info("Performing system poweroff")
            import subprocess
            import sys
            self.stop()  # Graceful BOSS shutdown first
            if sys.platform.startswith('linux'):
                subprocess.run(["sudo", "poweroff"], check=False)
            else:
                logger.warning("Poweroff not supported on this platform")
                
        elif reason == "exit_to_os":
            # Exit BOSS to OS
            logger.info("Exiting BOSS to OS")
            self.stop()  # Graceful BOSS shutdown
            
        else:
            # Normal shutdown
            logger.info("Normal system shutdown")
            self.stop()
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle system signals for graceful shutdown."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down gracefully")
        
        # Set the shutdown event to wake up the main thread
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()
        
        # Stop the system gracefully
        try:
            self.stop()
        except Exception as e:
            logger.error(f"Error during signal-triggered shutdown: {e}")
        
        # Force exit after a shorter delay on Windows (signals can be unreliable)
        def force_exit():
            import time
            time.sleep(1.0)  # Shorter timeout for Windows
            logger.warning("Forcing exit due to shutdown timeout")
            os._exit(0)
        
        threading.Thread(target=force_exit, daemon=True).start()
        
        # On Windows, also try to exit immediately after setting shutdown event
        if sys.platform.startswith('win'):
            import time
            time.sleep(0.1)  # Brief delay to allow logging
            os._exit(0)
