"""
AppManager: Handles polling switches and updating the 7-segment display
"""
from boss.hardware.switch_reader import SwitchInput
from boss.hardware.display import DisplayInterface
import time


from boss.core.event_bus import EventBus
import time

from typing import Optional

# AppManager is now a simple container for switch_reader, display, and event_bus.
class AppManager:
    def __init__(self, switch_reader: SwitchInput, display: DisplayInterface, event_bus: Optional[EventBus] = None):
        self.switch_reader = switch_reader
        self.display = display
        self.event_bus = event_bus
