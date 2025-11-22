"""Runtime test helpers for event-driven waiting without arbitrary sleeps."""
from __future__ import annotations

import time
from typing import Callable, Optional

# Generic wait helper -------------------------------------------------------

def wait_for(predicate: Callable[[], bool], timeout: float = 2.0, interval: float = 0.02) -> bool:
    """Wait until predicate returns True or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()

# Event bus oriented helpers ------------------------------------------------

def wait_for_app_started(event_bus, app_name: str, timeout: float = 2.0) -> bool:
    """Wait for lifecycle event that an app has started."""
    started = {"flag": False}
    def _handler(event_type, payload):
        # Accept both canonical or transitional names if present
        name = payload.get("name") or payload.get("app_name")
        if name == app_name:
            started["flag"] = True
    sub_id = event_bus.subscribe("app_started", _handler)
    try:
        return wait_for(lambda: started["flag"], timeout=timeout)
    finally:
        event_bus.unsubscribe(sub_id)


def wait_for_app_finished(event_bus, app_name: str, timeout: float = 3.0) -> bool:
    finished = {"flag": False}
    def _handler(event_type, payload):
        name = payload.get("name") or payload.get("app_name")
        if name == app_name:
            finished["flag"] = True
    sub_id = event_bus.subscribe("app_finished", _handler)
    try:
        return wait_for(lambda: finished["flag"], timeout=timeout)
    finally:
        event_bus.unsubscribe(sub_id)

__all__ = ["wait_for", "wait_for_app_started", "wait_for_app_finished"]
