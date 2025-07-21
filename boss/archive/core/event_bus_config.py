"""
EventBusConfig: Configuration for event logging and filtering in EventBus
"""
from typing import List, Optional

class EventBusConfig:
    def __init__(self, log_all_events: bool = True, log_event_types: Optional[List[str]] = None):
        self.log_all_events = log_all_events
        self.log_event_types = log_event_types or []
