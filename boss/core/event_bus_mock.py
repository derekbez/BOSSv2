"""
MockEventBus: A mock implementation of the EventBus API for testing.
"""
from typing import Callable, Dict, List, Any, Optional

class MockEventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._published: List[tuple] = []
        self._event_types: Dict[str, Dict[str, Any]] = {}

    def register_event_type(self, event_type: str, schema: Optional[Dict[str, Any]] = None):
        self._event_types[event_type] = schema or {}

    def subscribe(self, event_type: str, callback: Callable[[str, dict], None], filter: Optional[dict] = None, mode: str = "sync"):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append({"callback": callback, "filter": filter, "mode": mode})

    def publish(self, event_type: str, payload: dict):
        self._published.append((event_type, payload))
        for sub in self._subscribers.get(event_type, []):
            filt = sub.get("filter")
            if filt:
                if not all(payload.get(k) == v for k, v in filt.items()):
                    continue
            sub["callback"](event_type, payload)

    def get_published(self):
        return self._published

    def clear(self):
        self._published.clear()
        self._subscribers.clear()
