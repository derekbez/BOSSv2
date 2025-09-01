"""
App Runner Service - Manages execution of mini-apps in threads.
"""

import logging
import threading
import time
import sys
import importlib.util
from pathlib import Path
from typing import Optional, Any
from boss.domain.models.app import App, AppStatus
from boss.domain.interfaces.services import AppRunnerService

logger = logging.getLogger(__name__)


class AppRunner(AppRunnerService):
    """Service for running mini-apps in threads."""
    
    def __init__(self, event_bus, app_api_factory):
        self.event_bus = event_bus
        self.app_api_factory = app_api_factory
        self._current_app: Optional[App] = None
        self._current_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self._lock = threading.RLock()
    
    def start_app(self, app: App) -> None:
        """Start running an app in a new thread."""
        with self._lock:
            # Stop current app if running
            if self._current_app and self._current_app.is_running:
                self.stop_current_app()

            # If we're relaunching the same App object (or it hasn't fully
            # transitioned to STOPPED yet), wait briefly for it to settle.
            if not app.can_start:
                deadline = time.time() + 1.0  # up to ~1s grace
                while not app.can_start and time.time() < deadline:
                    time.sleep(0.05)

            # As a last resort (threads can't be force-killed), reset state to
            # STOPPED to avoid raising on mark_starting; the previous thread, if
            # still alive, will finish and publish app_stopped. We prefer not to
            # run two concurrent instances, but this unblocks accidental status
            # races.
            if not app.can_start:
                logger.warning(
                    f"Previous instance of {app.manifest.name} not fully stopped; forcing status reset"
                )
                try:
                    app.mark_stopped()
                except Exception:
                    pass
            
            # Mark app as starting
            app.mark_starting()
            self._current_app = app
            
            # Create stop event
            self._stop_event = threading.Event()
            
            # Start app thread
            self._current_thread = threading.Thread(
                target=self._run_app_thread,
                args=(app, self._stop_event),
                daemon=True,
                name=f"App-{app.manifest.name}"
            )
            
            logger.info(f"Starting app: {app.manifest.name} (switch {app.switch_value})")
            self._current_thread.start()
            
            # Publish app started event
            self.event_bus.publish("app_started", {
                "app_name": app.manifest.name,
                "switch_value": app.switch_value
            }, "app_runner")
    
    def stop_current_app(self, timeout: float = 5.0) -> bool:
        """Stop the currently running app.

        Returns True if the app thread terminated within timeout, else False.
        """
        with self._lock:
            if not self._current_app or not self._current_app.is_running:
                return True
            
            app = self._current_app
            logger.info(f"Stopping app: {app.manifest.name}")
            
            # Mark app as stopping
            app.mark_stopping()
            
            # Signal app to stop
            if self._stop_event:
                self._stop_event.set()
            
            # Wait for thread to finish with timeout
            if self._current_thread and self._current_thread.is_alive():
                self._current_thread.join(timeout=timeout)
                
                # Force terminate if still running
                if self._current_thread.is_alive():
                    logger.warning(f"App {app.manifest.name} did not stop gracefully")
                    # Note: Python doesn't allow force-killing threads safely
                    # Apps should respect the stop_event
                    stopped = False
                else:
                    stopped = True
            else:
                stopped = True
            
            # Clean up
            self._current_app = None
            self._current_thread = None
            self._stop_event = None
            return stopped
    
    def get_running_app(self) -> Optional[App]:
        """Get the currently running app."""
        return self._current_app if self._current_app and self._current_app.is_running else None
    
    def _run_app_thread(self, app: App, stop_event: threading.Event) -> None:
        """Run app in thread with error handling and timeout."""
        # Track timeout status across try/finally
        timed_out = {"value": False}
        try:
            # Mark app as running
            app.mark_running()
            app.last_run_time = time.time()

            # Load app module
            app_module = self._load_app_module(app)
            if not app_module:
                raise Exception("Failed to load app module")

            # Check for required run function
            if not hasattr(app_module, 'run'):
                raise Exception("App module missing 'run' function")

            # Run the app with timeout
            start_time = time.time()
            timeout = app.manifest.timeout_seconds

            logger.info(f"Running app: {app.manifest.name}")

            # Set up timeout monitoring
            def timeout_monitor():
                stop_event.wait(timeout)
                if not stop_event.is_set():
                    logger.warning(f"App {app.manifest.name} timed out after {timeout} seconds")
                    timed_out["value"] = True
                    stop_event.set()

            timeout_thread = threading.Thread(target=timeout_monitor, daemon=True)
            timeout_thread.start()

            # Create app API for this specific app
            app_api = self.app_api_factory(app.manifest.name, app.app_path)

            # Run the app
            app_module.run(stop_event, app_api)

            # App finished normally
            runtime = time.time() - start_time
            logger.info(f"App {app.manifest.name} finished normally after {runtime:.1f} seconds")
        except Exception as e:
            error_msg = f"App error: {e}"
            logger.error(f"Error running app {app.manifest.name}: {error_msg}")

            # Mark app as error
            app.mark_error(error_msg)

            # Publish app error event
            self.event_bus.publish("app_error", {
                "app_name": app.manifest.name,
                "switch_value": app.switch_value,
                "error": error_msg
            }, "app_runner")
        finally:
            # Ensure app is marked as stopped
            if app.status != AppStatus.ERROR:
                app.mark_stopped()
            # Determine reason and publish app_stopped for both normal completion and requested stop
            reason = "timeout" if timed_out.get("value") else ("stopped" if stop_event.is_set() else "normal")
            try:
                self.event_bus.publish("app_stopped", {
                    "app_name": app.manifest.name,
                    "switch_value": app.switch_value,
                    "reason": reason
                }, "app_runner")
            except Exception:
                pass
            # Clean up runner state if still pointing to this app
            with self._lock:
                if self._current_app is app:
                    self._current_app = None
                    self._current_thread = None
                    self._stop_event = None
    
    def _load_app_module(self, app: App) -> Optional[Any]:
        """Dynamically load app module."""
        try:
            entry_point_path = app.app_path / app.manifest.entry_point
            
            if not entry_point_path.exists():
                logger.error(f"Entry point not found: {entry_point_path}")
                return None
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"app_{app.manifest.name}",
                entry_point_path
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Could not create module spec for {entry_point_path}")
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            
            # Add app path to sys.path temporarily for relative imports
            app_path_str = str(app.app_path)
            if app_path_str not in sys.path:
                sys.path.insert(0, app_path_str)
                try:
                    spec.loader.exec_module(module)
                finally:
                    sys.path.remove(app_path_str)
            else:
                spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logger.error(f"Error loading app module {app.manifest.name}: {e}")
            return None
