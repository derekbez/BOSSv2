"""
Unit tests for EventBus app lifecycle and custom event types (US-EB-002, US-EB-003)
"""
from boss.core.event_bus import EventBus

def test_app_lifecycle_events():
    bus = EventBus()
    received = []
    def on_app_started(event_type, payload):
        received.append((event_type, payload))
    bus.register_event_type("app_started", {"app_name": str, "version": str, "timestamp": str})
    bus.subscribe("app_started", on_app_started)
    bus.publish("app_started", {"app_name": "test_app", "version": "1.0", "timestamp": "2025-07-01T12:00:00Z"})
    assert received[0][0] == "app_started"
    assert received[0][1]["app_name"] == "test_app"
    assert received[0][1]["version"] == "1.0"


def test_custom_event_type_registration_and_publish():
    bus = EventBus()
    received = []
    # Register a custom event type at runtime
    bus.register_event_type("app.quiz.completed", {"score": int, "max_score": int, "user_id": str})
    def on_quiz_completed(event_type, payload):
        received.append(payload)
    bus.subscribe("app.quiz.completed", on_quiz_completed)
    bus.publish("app.quiz.completed", {"score": 8, "max_score": 10, "user_id": "user42"})
    assert received[0]["score"] == 8
    assert received[0]["max_score"] == 10
    assert received[0]["user_id"] == "user42"
