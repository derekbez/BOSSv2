"""
AppManager: Handles polling switches and updating the 7-segment display
"""
from boss.hardware.switch_reader import SwitchInput
from boss.hardware.display import DisplayInterface
import time

class AppManager:
    def __init__(self, switch_reader: SwitchInput, display: DisplayInterface):
        self.switch_reader = switch_reader
        self.display = display
        self.last_value = None

    def poll_and_update_display(self):
        """Poll switch value and update display if changed."""
        value = self.switch_reader.read_value()
        if value != self.last_value:
            self.display.show_number(value)
            self.last_value = value
        return value

    def run_once(self):
        """Run a single poll-update cycle (for testing)."""
        return self.poll_and_update_display()

    def run_loop(self, poll_interval=0.1):
        """Continuously poll and update display."""
        try:
            while True:
                self.poll_and_update_display()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("AppManager stopped.")
