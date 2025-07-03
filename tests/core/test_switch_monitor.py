import pytest
import threading
import time
from boss.core.event_bus import EventBus
from boss.core.switch_monitor import SwitchMonitor

class DummySwitch:
    def __init__(self, values):
        self.values = values
        self.idx = 0
    def read_value(self):
        v = self.values[self.idx]
        self.idx = min(self.idx + 1, len(self.values) - 1)
        return v

def test_switch_monitor_publishes_events():
    bus = EventBus()
    received = []
    def handler(event_type, payload):
        received.append((event_type, payload))
    bus.register_event_type("switch_change", {"value": int, "previous_value": int, "timestamp": str})
    bus.subscribe("switch_change", handler)
    switch = DummySwitch([1, 1, 2, 2, 3])
    monitor = SwitchMonitor(switch, bus, poll_interval=0.01)
    monitor.start()
    time.sleep(0.05)
    monitor.stop()
    # Should have two events: 1->2 and 2->3
    assert len(received) == 2
    assert received[0][1]["value"] == 2
    assert received[0][1]["previous_value"] == 1
    assert received[1][1]["value"] == 3
    assert received[1][1]["previous_value"] == 2
