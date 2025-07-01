"""
AppManager: Handles polling switches and updating the 7-segment display
"""
from boss.hardware.switch_reader import SwitchInput
from boss.hardware.display import DisplayInterface
import time


from boss.core.event_bus import EventBus
import time

from typing import Optional

class AppManager:
    def __init__(self, switch_reader: SwitchInput, display: DisplayInterface, event_bus: Optional[EventBus] = None):
        self.switch_reader = switch_reader
        self.display = display
        self.last_value = None
        self.event_bus = event_bus

    def poll_and_update_display(self):
        """Poll switch value and update display if changed. Publishes switch_change event."""
        value = self.switch_reader.read_value()
        if value != self.last_value:
            self.display.show_number(value)
            if self.event_bus:
                self.event_bus.publish("switch_change", {
                    "value": value,
                    "previous_value": self.last_value,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
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
