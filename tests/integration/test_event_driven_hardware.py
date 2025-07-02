"""
Integration test: Event-driven hardware events and mini-app subscription
"""
import threading
import time
import pytest
from boss.core.event_bus_mock import MockEventBus
from boss.hardware.button import MockButton
from boss.hardware.led import MockLED
from boss.hardware.display import MockSevenSegmentDisplay
from boss.hardware.switch_reader import MockSwitchReader
from boss.hardware.screen import MockScreen


def test_button_press_event_subscription():
    bus = MockEventBus()
    button = MockButton("yellow", event_bus=bus, button_id="yellow")
    events = []
    def handler(event):
        events.append(event)
    sub_id = bus.subscribe("input.button.pressed", handler, filter={"button_id": "yellow"})
    button.press()
    time.sleep(0.05)
    assert len(events) == 1
    assert events[0]["button_id"] == "yellow"
    bus.unsubscribe(sub_id)


def test_led_state_change_event():
    bus = MockEventBus()
    led = MockLED("red", event_bus=bus)
    events = []
    def handler(event):
        events.append(event)
    sub_id = bus.subscribe("output.led.state_changed", handler, filter={"led_id": "red"})
    led.set_state(True)
    led.set_state(False)
    time.sleep(0.05)
    assert len(events) == 2
    assert events[0]["state"] == "on"
    assert events[1]["state"] == "off"
    bus.unsubscribe(sub_id)


def test_switch_change_event():
    bus = MockEventBus()
    switch = MockSwitchReader(event_bus=bus)
    events = []
    def handler(event):
        events.append(event)
    sub_id = bus.subscribe("input.switch.changed", handler)
    switch.set_value(42)
    switch.set_value(43)
    time.sleep(0.05)
    assert events[0]["current_value"] == 42
    assert events[1]["current_value"] == 43
    bus.unsubscribe(sub_id)


def test_screen_output_event():
    bus = MockEventBus()
    screen = MockScreen(event_bus=bus)
    events = []
    def handler(event):
        events.append(event)
    sub_id = bus.subscribe("output.screen.updated", handler)
    screen.display_text("Hello", color="red")
    screen.clear()
    time.sleep(0.05)
    assert any(e["action"] == "display_text" for e in events)
    assert any(e["action"] == "clear" for e in events)
    bus.unsubscribe(sub_id)

