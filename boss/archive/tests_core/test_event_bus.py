import pytest
from boss.core.event_bus import EventBus

def test_basic_publish_subscribe():
    bus = EventBus()
    received = []
    def cb(event_type, payload):
        received.append((event_type, payload))
    bus.register_event_type("button_press", {"button": str, "timestamp": str})
    bus.subscribe("button_press", cb)
    bus.publish("button_press", {"button": "red", "timestamp": "2025-07-01T12:00:00Z"})
    assert received == [("button_press", {"button": "red", "timestamp": "2025-07-01T12:00:00Z"})]

def test_multiple_subscribers():
    bus = EventBus()
    calls = []
    def cb1(event_type, payload):
        calls.append(("cb1", event_type, payload))
    def cb2(event_type, payload):
        calls.append(("cb2", event_type, payload))
    bus.register_event_type("led_state_changed")
    bus.subscribe("led_state_changed", cb1)
    bus.subscribe("led_state_changed", cb2)
    bus.publish("led_state_changed", {"led": "green", "state": "on"})
    assert any(c[0] == "cb1" for c in calls)
    assert any(c[0] == "cb2" for c in calls)

def test_event_type_registration():
    bus = EventBus()
    bus.register_event_type("seven_segment_updated", {"value": int, "timestamp": str})
    assert "seven_segment_updated" in bus._event_types

def test_subscriber_exception_does_not_break_bus():
    bus = EventBus()
    called = []
    def bad_cb(event_type, payload):
        raise ValueError("fail!")
    def good_cb(event_type, payload):
        called.append(True)
    bus.register_event_type("screen_updated")
    bus.subscribe("screen_updated", bad_cb)
    bus.subscribe("screen_updated", good_cb)
    bus.publish("screen_updated", {"action": "display_text", "content": "hi"})
    assert called == [True]
