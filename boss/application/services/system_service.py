"""
System Service - Manages overall system lifecycle and coordination.
"""

import logging
import os
import signal
import sys
import threading
import time
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
        self._webui_port = None  # Track dev UI port for shutdown (if any)
    # Legacy backend switching removed; attribute retained previously is now unnecessary.

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Set up event subscriptions
        self._setup_event_handlers()
        # Optional: basic hot-reload of screen backend when config change event occurs
        try:
            self.event_bus.subscribe("config.changed", self._on_config_changed)
        except Exception:
            pass
    
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
            
            # Optionally start a dev UI via factory (no-op on real GPIO/mock)
            hardware_type = getattr(self.hardware_service.hardware_factory, 'hardware_type', 'unknown')
            try:
                components_map = {
                    'buttons': self.hardware_service.buttons,
                    'go_button': self.hardware_service.go_button,
                    'leds': self.hardware_service.leds,
                    'switches': self.hardware_service.switches,
                    'display': self.hardware_service.display,
                    'screen': self.hardware_service.screen,
                    'speaker': self.hardware_service.speaker,
                }
                if hasattr(self.hardware_service.hardware_factory, 'start_dev_ui'):
                    port = self.hardware_service.hardware_factory.start_dev_ui(self.event_bus, components_map)  # type: ignore
                    if port:
                        self._webui_port = port
                        logger.info(f"Development UI started at http://localhost:{port}")
            except Exception as e:
                logger.debug(f"Dev UI start skipped: {e}")
            
            # Show current switch value on 7-seg before running the startup app
            try:
                state = self.hardware_service.get_hardware_state()
                if state and state.switches:
                    self.event_bus.publish("display_update", {"value": state.switches.value}, "system")
            except Exception as e:
                logger.debug(f"Initial display update skipped: {e}")

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

        # Only publish a normal shutdown event if we're not already inside a
        # specific shutdown handling path (reboot/poweroff/exit_to_os). This
        # prevents a second "normal" reason from overwriting the original
        # intent in logs and avoids re-entrancy.
        if not getattr(self, "_handling_specific_shutdown", False):
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
    
    # WebUI-specific helper removed; factory handles dev UI lifecycle
    
    def stop_webui_if_running(self) -> None:
        """Stop WebUI development interface if it's running."""
        if self._webui_port:
            try:
                if hasattr(self.hardware_service.hardware_factory, 'stop_dev_ui'):
                    self.hardware_service.hardware_factory.stop_dev_ui()  # type: ignore
                logger.info(f"Development UI on port {self._webui_port} stopped")
                self._webui_port = None
            except Exception as e:
                logger.debug(f"Error stopping development UI: {e}")
    
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
            import time
            from boss.domain.models.hardware_state import LedColor
            led_colors = [LedColor("red"), LedColor("yellow"), LedColor("green"), LedColor("blue")]

            # Blink all LEDs 5 times
            for i in range(5):
                for color in led_colors:
                    if hasattr(self.hardware_service, 'leds') and self.hardware_service.leds:
                        self.hardware_service.leds.set_led(color, True)
                time.sleep(0.2)
                for color in led_colors:
                    if hasattr(self.hardware_service, 'leds') and self.hardware_service.leds:
                        self.hardware_service.leds.set_led(color, False)
                time.sleep(0.15)

            # Show message on screen if available
            try:
                if hasattr(self.hardware_service, 'screen') and self.hardware_service.screen:
                    self.hardware_service.screen.display_text(
                        "BOSS might not be ready\n\nThe expected Startup app could not be found.",
                        align='center',
                        color='yellow',
                        font_size=28
                    )
            except Exception:
                pass

            # Show fallback on 7-segment display if available
            try:
                if hasattr(self.hardware_service, 'display') and self.hardware_service.display:
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
        # Use a local var for brevity
        bus = self.event_bus
        # Handle app launch requests (from Go button or API)
        bus.subscribe("app_launch_requested", self._on_app_launch_requested)
        # Go button direct event
        bus.subscribe("go_button_pressed", self._on_go_button_pressed)
        # Feedback / lifecycle events
        bus.subscribe("app_started", self._on_app_started)
        # App stopped (cleanup / display restore etc.)
        bus.subscribe("app_stopped", self._on_app_stopped)
        # Handle admin shutdown requests
        bus.subscribe("system_shutdown", self._on_system_shutdown_requested)
        # Note: Hardware output events (led_update, display_update, screen_update)
        # are handled elsewhere (HardwareEventHandler)

    def _on_config_changed(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle config change (screen backend hot-reload removed for simplicity)."""
        return None
    
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

                # Immediate user feedback: set 7-seg to LOAD and light all LEDs briefly
                self._show_transition_feedback()

                # If an app is running, stop it first (shorter timeout for snappier UX)
                try:
                    stopped = self.app_runner.stop_current_app(timeout=1.2)
                    if not stopped:
                        logger.warning("Previous app did not stop within timeout; proceeding with new launch")
                except Exception as e:
                    logger.debug(f"stop_current_app error: {e}")

                # Start new app
                self.app_runner.start_app(app)
                self.app_manager.set_current_app(app)
            else:
                logger.warning(f"No app mapped to switch value {switch_value}")
                # Could show an error on screen here
                
        except Exception as e:
            logger.error(f"Error launching app: {e}")

    def _on_app_stopped(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle app stopped events (cleanup & display restore)."""
        # When an app stops, restore switch value on 7-seg if idle
        try:
            current_app = self.app_runner.get_running_app()
            if current_app is None:
                state = self.hardware_service.get_hardware_state()
                if self.hardware_service.display and hasattr(self.hardware_service.display, 'show_number'):
                    self.hardware_service.display.show_number(state.switches.value)
                # Central LED normalization: ensure all LEDs are off when no app is running.
                try:
                    if self.hardware_service.leds:
                        for c in ("red", "yellow", "green", "blue"):
                            try:
                                self.hardware_service.leds.set_led(c, False)  # type: ignore[arg-type]
                            except Exception:
                                pass
                except Exception:
                    pass
                # If the app ended due to timeout, auto-launch the startup app (switch 0) to show ready state
                try:
                    if payload.get("reason") == "timeout":
                        startup_app = self.app_manager.get_app_by_switch_value(0)
                        if startup_app:
                            logger.info("Timed-out app; launching startup app (switch 0)")
                            # Provide quick visual feedback
                            self._show_transition_feedback()
                            self.app_runner.start_app(startup_app)
                            self.app_manager.set_current_app(startup_app)
                except Exception as e:
                    logger.debug(f"Failed to auto-launch startup app after timeout: {e}")
        except Exception:
            pass

    def _on_app_started(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Clear transition indicators once the new app thread has started."""
        try:
            # Turn LEDs off after transition
            if self.hardware_service.leds:
                for c in ("red","yellow","green","blue"):
                    try:
                        self.hardware_service.leds.set_led(c, False)
                    except Exception:
                        pass
            # Restore 7-seg to current switch value (clears LOAD) unless app already changed it
            try:
                state = self.hardware_service.get_hardware_state()
                if state and self.hardware_service.display and hasattr(self.hardware_service.display, 'show_number'):
                    self.hardware_service.display.show_number(state.switches.value)
            except Exception:
                pass
            # App may overwrite screen quickly; no extra action needed here.
        except Exception:
            pass
    
    def _on_go_button_pressed(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle Go button press."""
        # Snapshot current switch value immediately to avoid races with the
        # background monitor or multiplexed switch settling. Publish a
        # display_update using the sampled value so the 7-seg shows the
        # canonical value at the moment of launch.
        try:
            # Small stabilization delay to allow mechanical switches/mux to settle
            # (10ms is conservative for common hardware)
            try:
                time.sleep(0.01)
            except Exception:
                pass

            hw_state = self.hardware_service.get_hardware_state()
            switch_value = 0
            if hw_state and hw_state.switches:
                switch_value = hw_state.switches.value

            logger.info(f"Go button pressed. Snapshot switch value: {switch_value}")
            # Ensure the display mirrors the sampled value immediately
            try:
                self.event_bus.publish("display_update", {"value": switch_value}, "system")
            except Exception:
                logger.debug("Failed to publish immediate display_update on go press")

        except Exception as e:
            logger.debug(f"Error snapshotting switches on go press: {e}")

        # Trigger app launch (transition feedback handled in launch handler)
        self.event_bus.publish("app_launch_requested", {}, "system")

    # ------------------------------------------------------------------
    # Visual / tactile feedback helpers
    # ------------------------------------------------------------------
    def _show_transition_feedback(self) -> None:
        """Provide immediate visual feedback that an app transition is in progress."""
        try:
            # 7-seg: show LOAD / or dashes (fallback if show_text not available)
            disp = self.hardware_service.display
            if disp:
                if hasattr(disp, 'show_text'):
                    try:
                        disp.show_text("LOAD")
                    except Exception:
                        pass
                elif hasattr(disp, 'show_number'):
                    try:
                        # Use 4 dashes as a neutral transition marker if possible
                        disp.show_text("----")  # type: ignore
                    except Exception:
                        pass

            # LEDs: turn all on to signal processing
            leds = self.hardware_service.leds
            if leds:
                for c in ("red","yellow","green","blue"):
                    try:
                        leds.set_led(c, True)
                    except Exception:
                        pass
        except Exception:
            logger.debug("Transition feedback error", exc_info=True)
    
    def _on_system_shutdown_requested(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle system shutdown requests from admin apps.

        Supported reasons:
          reboot      - Graceful stop followed by OS reboot
          poweroff    - Graceful stop followed by OS poweroff
          exit_to_os  - Graceful stop only (do not restart service)
          normal/other- Graceful stop
        """
        reason = payload.get("reason", "normal")
        logger.info(f"System shutdown requested (reason='{reason}')")

        # Mark that we are handling a specific shutdown to suppress the
        # automatic normal event emission inside stop().
        self._handling_specific_shutdown = reason in {"reboot", "poweroff", "exit_to_os"}

        try:
            if reason in {"reboot", "poweroff"}:
                # Use new helper to ensure the system action runs AFTER a full, clean stop
                self._graceful_stop_then_action(reason)
            elif reason == "exit_to_os":
                logger.info("Exiting BOSS to OS (no reboot/poweroff)")
                self._graceful_stop_then_action(None)
                logger.info("BOSS exited to OS. (If it restarts, adjust systemd Restart policy)")
            else:
                logger.info("Normal system shutdown path engaged")
                self._graceful_stop_then_action(None)
        finally:
            # Clear flag so subsequent start/stop cycles behave normally (the helper sets this too)
            self._handling_specific_shutdown = False

    def _execute_system_action(self, action: str, command: list) -> None:
        """Execute a system-level action (reboot/poweroff) with logging.

        Args:
            action: Friendly action name (reboot/poweroff)
            command: Command list to run
        """
        import subprocess
        import sys
        if not sys.platform.startswith("linux"):
            logger.warning(f"{action.capitalize()} not supported on this platform")
            return

        # Check privileges (use getattr for cross-platform safety)
        geteuid = getattr(os, "geteuid", None)
        is_root = bool(geteuid and geteuid() == 0)
        if not is_root and command and command[0] == "sudo":
            logger.info(f"Attempting '{action}' via sudo (user={os.getenv('USER')})")
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            logger.info(
                f"System {action} command executed rc={result.returncode} stdout='{result.stdout.strip()}' stderr='{result.stderr.strip()}'"
            )
            if result.returncode != 0:
                logger.warning(
                    f"{action.capitalize()} command failed (rc={result.returncode}). "
                    "Ensure passwordless sudo is configured or adjust service permissions."
                )
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")

    # ------------------------------------------------------------------
    # Improved graceful-stop + optional system action helper
    # ------------------------------------------------------------------
    def _graceful_stop_then_action(self, action: Optional[str]) -> None:
        """Gracefully stop the BOSS system then (optionally) perform a system action.

        Runs the reboot/poweroff command in a short delayed background thread so
        that: (1) logging handlers flush, (2) resources release cleanly, and
        (3) the calling event handler returns promptly without racing the OS
        shutdown. On non-Linux platforms, just logs.

        Args:
            action: 'reboot', 'poweroff', or None
        """
        # Ensure specific-shutdown suppression flag is set for special actions
        self._handling_specific_shutdown = action in {"reboot", "poweroff", "exit_to_os"}

        # Perform normal stop sequence (suppresses extra event when flag set)
        try:
            self.stop()
        except Exception:
            logger.exception("Error during graceful stop prior to system action")

        if action not in {"reboot", "poweroff"}:
            return  # Nothing further to do

        # Delay system action slightly in a daemon thread to allow log flush
        import threading, time

        def _delayed():  # inner closure
            try:
                # Small delay: give log handlers time to finish
                time.sleep(0.8)
                # Flush logging handlers explicitly
                try:
                    import logging as _logging
                    for h in _logging.getLogger().handlers:
                        try:
                            h.flush()
                        except Exception:
                            pass
                except Exception:
                    pass
                if action == "reboot":
                    logger.info("Executing OS reboot command")
                    self._execute_system_action("reboot", ["sudo", "reboot"])
                elif action == "poweroff":
                    logger.info("Executing OS poweroff command")
                    self._execute_system_action("poweroff", ["sudo", "poweroff"])
            except Exception:
                logger.exception("Delayed system action thread error")

        threading.Thread(target=_delayed, name=f"system-{action}-thread", daemon=True).start()
    
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
