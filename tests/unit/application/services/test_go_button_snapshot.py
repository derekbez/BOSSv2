import logging
import threading

from boss.core import SystemManager


class DummyEventBus:
    def __init__(self):
        self.published = []
        self._subs = {}
    def publish(self, event_type, payload, source=None):
        self.published.append((event_type, payload, source))
    def subscribe(self, event_type, handler):
        # store handler to mimic subscription interface
        self._subs.setdefault(event_type, []).append(handler)
    def start(self):
        return None
    def stop(self):
        return None
    def get_stats(self):
        return {"subscriptions": len(self._subs)}

class DummyHardwareService:
    def __init__(self, switch_value=7):
        class SwitchState:
            def __init__(self, value):
                self.value = value
        class HwState:
            def __init__(self, value):
                self.switches = SwitchState(value)
        self._state = HwState(switch_value)
    def get_hardware_state(self):
        return self._state


def test_go_button_snapshot_publishes_display_update():
    bus = DummyEventBus()
    hw = DummyHardwareService(switch_value=42)
    manager = SystemManager(bus, hw, app_manager=None, app_runner=None)

    # Call the handler directly
    manager._on_go_button_pressed("go_button_pressed", {})

    # Check that a display_update was published with the sampled value
    found = [p for p in bus.published if p[0] == "display_update"]
    assert found, "No display_update published"
    assert found[0][1]["value"] == 42
