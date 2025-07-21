"""
Hardware state models for B.O.S.S.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class LedColor(Enum):
    """Available LED colors."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"


class ButtonColor(Enum):
    """Available button colors."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"


@dataclass
class SwitchState:
    """Current state of the 8-bit switch array."""
    value: int  # 0-255
    individual_switches: Dict[int, bool]  # switch_number -> on/off
    
    def __post_init__(self):
        """Validate switch state consistency."""
        if not 0 <= self.value <= 255:
            raise ValueError(f"Switch value must be 0-255, got {self.value}")


@dataclass
class ButtonState:
    """State of a single button."""
    color: ButtonColor
    is_pressed: bool
    last_press_time: Optional[float] = None


@dataclass
class LedState:
    """State of a single LED."""
    color: LedColor
    is_on: bool
    brightness: float = 1.0  # 0.0 to 1.0
    
    def __post_init__(self):
        """Validate LED state."""
        if not 0.0 <= self.brightness <= 1.0:
            raise ValueError(f"LED brightness must be 0.0-1.0, got {self.brightness}")


@dataclass
class DisplayState:
    """State of the 7-segment display."""
    value: Optional[int] = None  # Number to display (0-9999) or None for blank
    is_blinking: bool = False
    brightness: float = 1.0
    
    def __post_init__(self):
        """Validate display state."""
        if self.value is not None and not 0 <= self.value <= 9999:
            raise ValueError(f"Display value must be 0-9999 or None, got {self.value}")
        if not 0.0 <= self.brightness <= 1.0:
            raise ValueError(f"Display brightness must be 0.0-1.0, got {self.brightness}")


@dataclass
class HardwareState:
    """Complete state of all hardware components."""
    switches: SwitchState
    buttons: Dict[ButtonColor, ButtonState]
    leds: Dict[LedColor, LedState]
    display: DisplayState
    go_button_pressed: bool = False
    
    @classmethod
    def create_default(cls) -> "HardwareState":
        """Create default hardware state with all components off/inactive."""
        return cls(
            switches=SwitchState(value=0, individual_switches={i: False for i in range(8)}),
            buttons={color: ButtonState(color=color, is_pressed=False) for color in ButtonColor},
            leds={color: LedState(color=color, is_on=False) for color in LedColor},
            display=DisplayState(value=0),
            go_button_pressed=False
        )
