import threading
import queue
from typing import Callable, Dict, List, Any, Optional
import time
import logging
from boss.core.event_bus_config import EventBusConfig

class AsyncEventBus:
    def __init__(self, config: Optional[EventBusConfig] = None, queue_size: int = 1000):
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._event_types: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger("AsyncEventBus")
        self._config = config or EventBusConfig()
        self._queue = queue.Queue(maxsize=queue_size)
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def register_event_type(self, event_type: str, schema: Optional[Dict[str, Any]] = None):
        with self._lock:
            self._event_types[event_type] = schema or {}
            self._logger.debug(f"Registered event type: {event_type}")

    def subscribe(self, event_type: str, callback: Callable[[str, dict], None], filter: Optional[dict] = None):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append({"callback": callback, "filter": filter})
            self._logger.debug(f"Subscribed to {event_type}: {callback} with filter: {filter}")

    def publish(self, event_type: str, payload: dict):
        payload = dict(payload)
        if "timestamp" not in payload:
            payload["timestamp"] = time.time()
        log_this_event = self._config.log_all_events or event_type in self._config.log_event_types
        if log_this_event:
            self._logger.info(f"Event published: {event_type} | {payload}")
        try:
            self._queue.put_nowait((event_type, payload))
        except queue.Full:
            self._logger.warning(f"Event queue full, dropping event: {event_type}")

    def _worker_loop(self):
        while True:
            event_type, payload = self._queue.get()
            with self._lock:
                for sub in self._subscribers.get(event_type, []):
                    filt = sub.get("filter")
                    if filt:
                        if not all(payload.get(k) == v for k, v in filt.items()):
                            continue
                    try:
                        sub["callback"](event_type, payload)
                    except Exception as e:
                        self._logger.error(f"Error in subscriber for {event_type}: {e}")
