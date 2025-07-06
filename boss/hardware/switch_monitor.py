import threading
import time
from typing import Callable, Optional

class SwitchMonitor:
    """
    Monitors a SwitchInput for value changes and publishes 'switch_change' events to the event bus.
    """
    def __init__(self, switch_reader, event_bus, poll_interval=0.05):
        self.switch_reader = switch_reader
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self._last_value = None
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self):
        while not self._stop.is_set():
            value = self.switch_reader.read_value()
            if self._last_value is None or (self._last_value is not None and value != self._last_value):
                self.event_bus.publish("switch_change", {
                    "value": value,
                    "previous_value": self._last_value,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
            self._last_value = value
            time.sleep(self.poll_interval)
