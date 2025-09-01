"""Smoke tests for migrated mini-apps (app_jokes, current_weather).

These tests execute the app run function with a mock/stub API facade and a controllable
stop_event to ensure basic lifecycle (start, simple interaction, stop) works without
raising exceptions. Network calls in current_weather are monkeypatched to avoid
external dependency and to keep tests fast/deterministic.
"""
from __future__ import annotations
import importlib
import threading
import time
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# Helper minimal mock API surface compatible with the app expectations.
# (We avoid pulling full system wiring for speed.)
# ---------------------------------------------------------------------------

class DummyScreen:
    def __init__(self):
        self.last_text = None
    def clear_screen(self):
        pass
    def clear(self):  # some older apps might call clear()
        pass
    def display_text(self, text: str, **kwargs):
        self.last_text = text

class DummyHardware:
    def set_led(self, color: str, state: bool):
        pass

class DummyEventBus:
    def __init__(self):
        self._subs: Dict[int, tuple[str, Any]] = {}
        self._next = 1
    def subscribe(self, event_type: str, handler):
        sid = self._next
        self._next += 1
        self._subs[sid] = (event_type, handler)
        return sid
    def unsubscribe(self, sid: int):
        self._subs.pop(sid, None)
    # Minimal publish for button simulation
    def publish_button(self, button: str):
        for (_, (etype, handler)) in list(self._subs.items()):
            if etype == "button_pressed":
                handler("button_pressed", {"button": button})

class DummyAPI:
    def __init__(self, app_dir: Path):
        self.screen = DummyScreen()
        self.hardware = DummyHardware()
        self.event_bus = DummyEventBus()
        self._app_dir = app_dir
        self._config = {}
    def log_info(self, msg: str):
        pass
    def log_error(self, msg: str):
        pass
    def get_asset_path(self, name: str) -> str:
        return str(self._app_dir / "assets" / name)
    def get_app_asset_path(self) -> str:
        return str(self._app_dir / "assets")
    def get_config_value(self, key: str, default=None):
        return self._config.get(key, default)
    def get_app_config(self, default=None):
        return default or {}

# ---------------------------------------------------------------------------
# Parametrized smoke test
# ---------------------------------------------------------------------------

APP_CASES = [
    {  # static asset-driven example
        "name": "app_jokes",
        "module": "boss.apps.app_jokes.main",
        "simulate": ["yellow"],
        "duration": 1.2,
    },
    {  # network weather example (mocked)
        "name": "current_weather",
        "module": "boss.apps.current_weather.main",
        "simulate": [],
        "duration": 1.2,
        "mock_weather": {
            "current_weather": {"temperature": 20, "windspeed": 5, "cloudcover": 42}
        },
    },
    {  # network news example (mocked headlines)
        "name": "breaking_news",
        "module": "boss.apps.breaking_news.main",
        "simulate": ["green"],
        "duration": 1.2,
        "mock_fn": "fetch_headlines",
        "mock_value": ["Headline One", "Headline Two"],
    },
    {  # local assets snippet example
        "name": "public_domain_book_snippet",
        "module": "boss.apps.public_domain_book_snippet.main",
        "simulate": ["green"],
        "duration": 1.0,
    },
    {  # random emoji combo asset app
        "name": "random_emoji_combo",
        "module": "boss.apps.random_emoji_combo.main",
        "simulate": ["green"],
        "duration": 1.0,
    },
    {  # joke fetching app with button punchline reveal
        "name": "joke_of_the_moment",
        "module": "boss.apps.joke_of_the_moment.main", 
        "simulate": ["green"],
        "duration": 1.2,
        "mock_fn": "fetch_joke",
        "mock_value": {"type": "twopart", "setup": "Test setup", "delivery": "Test punchline"},
    },
]

@pytest.mark.parametrize("case", APP_CASES, ids=lambda c: c["name"])
def test_app_smoke(case, monkeypatch):
    mod = importlib.import_module(case["module"])

    # Targeted monkeypatching for network apps to keep tests offline
    if case["name"] == "current_weather" and hasattr(mod, "fetch_weather"):
        monkeypatch.setattr(mod, "fetch_weather", lambda lat, lon, timeout: case["mock_weather"])
    if case.get("mock_fn") and hasattr(mod, case["mock_fn"]):
        monkeypatch.setattr(mod, case["mock_fn"], lambda *a, **k: case.get("mock_value"))

    app_dir = Path(__file__).parents[3] / "boss" / "apps" / case["name"]
    assert app_dir.exists(), f"App directory missing: {app_dir}"

    api = DummyAPI(app_dir)
    stop_event = threading.Event()

    # Launch app in thread
    t = threading.Thread(target=mod.run, args=(stop_event, api), daemon=True)
    t.start()

    # Allow initialization
    time.sleep(0.4)

    # Simulate button presses
    for btn in case.get("simulate", []):
        api.event_bus.publish_button(btn)
        time.sleep(0.1)

    # Let it run briefly
    time.sleep(case.get("duration", 1.0))

    # Stop
    stop_event.set()
    t.join(timeout=2.0)
    assert not t.is_alive(), f"App thread did not stop: {case['name']}"

    # Basic assertions on screen output
    assert api.screen.last_text is not None, "No screen output captured"

# ---------------------------------------------------------------------------
# Focused unit-style test for weather formatting (if available)
# ---------------------------------------------------------------------------

def test_current_weather_format_function():
    mod = importlib.import_module("boss.apps.current_weather.main")
    if hasattr(mod, "format_weather"):
        txt = mod.format_weather({"current_weather": {"temperature": 1, "windspeed": 2, "cloudcover": 3}})
        assert "Temp:" in txt and "Wind:" in txt and "Cloud:" in txt
