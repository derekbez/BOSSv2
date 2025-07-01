"""
AppRunner: Manages running, terminating, and force-stopping mini-apps in threads.
"""
import threading
import time
import importlib
from boss.core.logger import get_logger


from boss.core.event_bus import EventBus
import time
from typing import Optional

class AppRunner:
    def __init__(self, timeout=30, event_bus: Optional[EventBus] = None):
        self.app_thread = None
        self.stop_event = threading.Event()
        self.current_app = None
        self.timeout = timeout
        self.logger = get_logger("AppRunner")
        self.event_bus = event_bus

    def run_app(self, app_name, params=None, api=None, version=None):
        self.stop_app()
        self.stop_event.clear()
        self.current_app = app_name
        self.app_thread = threading.Thread(
            target=self._app_thread_func,
            args=(app_name, params or {}, api, version),
            daemon=True
        )
        self.app_thread.start()
        self.logger.info(f"Started app: {app_name}")
        # Publish app_started event
        if self.event_bus:
            self.event_bus.publish("app_started", {
                "app_name": app_name,
                "version": version or "unknown",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

    def _app_thread_func(self, app_name, params, api, version):
        try:
            app_module = importlib.import_module(f"boss.apps.{app_name}")
            app_module.run(self.stop_event, api)
        except Exception as e:
            self.logger.error(f"Error running app {app_name}: {e}")

    def stop_app(self, version=None):
        if self.app_thread and self.app_thread.is_alive():
            self.logger.info(f"Stopping app: {self.current_app}")
            self.stop_event.set()
            self.app_thread.join(timeout=self.timeout)
            if self.app_thread.is_alive():
                self.logger.error(f"App {self.current_app} did not stop in time and was force-terminated.")
            else:
                self.logger.info(f"App {self.current_app} stopped cleanly.")
            # Publish app_stopped event
            if self.event_bus:
                self.event_bus.publish("app_stopped", {
                    "app_name": self.current_app,
                    "version": version or "unknown",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
        self.current_app = None
        self.app_thread = None
