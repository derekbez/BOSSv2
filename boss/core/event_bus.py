"""
EventBus: Simple synchronous publish/subscribe event bus for B.O.S.S.
Implements core of US-EB-001 (see event_bus-user_stories.yaml)
"""
import threading
import time
import logging
from typing import Callable, Dict, List, Any, Optional
from boss.core.event_bus_config import EventBusConfig
import uuid


class EventBus:
    def register_event_source(self, name: str, publisher_callback: Callable):
        """Register a new event source (plugin/extensibility)."""
        # For extensibility: store or call publisher_callback as needed
        if not hasattr(self, '_event_sources'):
            self._event_sources = {}
        self._event_sources[name] = publisher_callback
        self._logger.info(f"Registered event source: {name}")
    def __init__(self, config: Optional[EventBusConfig] = None):
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._event_types: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger("EventBus")
        self._config = config or EventBusConfig()

    def register_event_type(self, event_type: str, schema: Optional[Dict[str, Any]] = None):
        """Register a new event type and (optionally) its schema."""
        with self._lock:
            self._event_types[event_type] = schema or {}
            self._logger.debug(f"Registered event type: {event_type}")

    def subscribe(self, event_type: str, callback: Callable[[str, dict], None], filter: Optional[dict] = None, mode: str = "sync"):
        """Subscribe a callback to an event type, with optional payload filter and mode ('sync' or 'async'). Returns a subscription ID for later unsubscription."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            sub_id = str(uuid.uuid4())
            self._subscribers[event_type].append({"id": sub_id, "callback": callback, "filter": filter, "mode": mode})
            self._logger.debug(f"Subscribed to {event_type}: {callback} with filter: {filter} mode: {mode} id: {sub_id}")
            return sub_id

    def unsubscribe(self, sub_id: str):
        """Unsubscribe a callback using its subscription ID."""
        with self._lock:
            for event_type, subs in self._subscribers.items():
                for i, sub in enumerate(subs):
                    if sub.get("id") == sub_id:
                        del subs[i]
                        self._logger.debug(f"Unsubscribed {sub_id} from {event_type}")
                        return True
        self._logger.warning(f"Unsubscribe failed: {sub_id} not found")
        return False

    def publish(self, event_type: str, payload: dict):
        """Publish an event to all subscribers. Adds timestamp if not present. Honors logging config, filtering, and async mode."""
        import threading
        payload = dict(payload)  # Copy to avoid mutation
        if "timestamp" not in payload:
            payload["timestamp"] = time.time()
        # Logging logic
        log_this_event = self._config.log_all_events or event_type in self._config.log_event_types
        if log_this_event:
            self._logger.info(f"Event published: {event_type} | {payload}")
        with self._lock:
            for sub in self._subscribers.get(event_type, []):
                filt = sub.get("filter")
                if filt:
                    # All filter keys must match payload
                    if not all(payload.get(k) == v for k, v in filt.items()):
                        continue
                mode = sub.get("mode", "sync")
                if mode == "async":
                    threading.Thread(target=sub["callback"], args=(event_type, payload), daemon=True).start()
                else:
                    try:
                        sub["callback"](event_type, payload)
                    except Exception as e:
                        self._logger.error(f"Error in subscriber for {event_type}: {e}")
# System shutdown and error event publishing helpers
    def publish_system_shutdown(self, reason: str):
        self.publish("system_shutdown", {
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

    def publish_error(self, error_type: str, message: str, stack_trace: Optional[str] = None):
        payload = {
            "error_type": error_type,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        if stack_trace:
            payload["stack_trace"] = stack_trace
        self.publish("error", payload)

# Example usage and test
if __name__ == "__main__":
    bus = EventBus()
    def on_button(event_type, payload):
        print(f"Button event: {event_type} | {payload}")
    bus.register_event_type("button_press", {"button": str, "timestamp": float})
    sub_id = bus.subscribe("button_press", on_button)
    bus.publish("button_press", {"button": "red"})
    bus.unsubscribe(sub_id)
