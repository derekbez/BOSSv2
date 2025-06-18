"""
GoButtonManager: Handles Go button press to launch/terminate mini-apps
"""
from boss.hardware.button import ButtonInterface
from boss.core.app_manager import AppManager
from boss.core.config import ConfigManager
import threading

class GoButtonManager:
    def __init__(self, go_button: ButtonInterface, app_manager: AppManager, config: ConfigManager):
        self.go_button = go_button
        self.app_manager = app_manager
        self.config = config
        self.app_thread = None
        self.stop_event = threading.Event()
        self.current_app = None
        self.go_button.set_callback(self.handle_go_press)

    def handle_go_press(self):
        value = self.app_manager.last_value
        app_info = self.config.get_app_for_value(value)
        if self.app_thread and self.app_thread.is_alive():
            self.stop_event.set()
            self.app_thread.join()
        if app_info:
            self.stop_event.clear()
            self.current_app = app_info["app"]
            params = app_info.get("params", {})
            self.app_thread = threading.Thread(
                target=self.run_app,
                args=(self.current_app, params),
                daemon=True
            )
            self.app_thread.start()

    def run_app(self, app_name, params):
        # Dynamically import and run the app
        import importlib
        stop_event = self.stop_event
        api = None  # Would be the hardware API object
        try:
            app_module = importlib.import_module(f"boss.apps.{app_name}")
            app_module.run(stop_event, api)
        except Exception as e:
            print(f"Error running app {app_name}: {e}")
