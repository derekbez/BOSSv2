"""
Configuration models for B.O.S.S.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
import json


@dataclass
class HardwareConfig:
    """Hardware configuration settings."""
    # GPIO pin assignments
    switch_data_pin: int = 18
    switch_clock_pin: int = 24
    switch_select_pins: List[int] = field(default_factory=lambda: [22, 23, 25])
    
    go_button_pin: int = 16
    
    # Button pins (color -> pin)
    button_pins: Dict[str, int] = field(default_factory=lambda: {
        "red": 5,
        "yellow": 6,
        "green": 13,
        "blue": 19
    })
    
    # LED pins (color -> pin)
    led_pins: Dict[str, int] = field(default_factory=lambda: {
        "red": 21,
        "yellow": 20,
        "green": 26,
        "blue": 12
    })
    
    # Display pins
    display_clk_pin: int = 2
    display_dio_pin: int = 3
    
    # Screen settings
    screen_width: int = 1280
    screen_height: int = 720
    screen_fullscreen: bool = True
    
    # Audio settings
    enable_audio: bool = True
    audio_volume: float = 0.7


@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    # App settings
    app_timeout_seconds: int = 300
    apps_directory: str = "apps"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/boss.log"
    log_max_size_mb: int = 10
    log_backup_count: int = 5
    
    # Event bus settings
    event_queue_size: int = 1000
    event_timeout_seconds: float = 1.0
    
    # Web UI settings (for development)
    webui_enabled: bool = False
    webui_host: str = "localhost"
    webui_port: int = 8080
    
    # Network settings
    enable_api: bool = False
    api_port: int = 5000
    
    # Hardware detection
    auto_detect_hardware: bool = True
    force_hardware_type: Optional[str] = None  # "gpio", "webui", "mock"


@dataclass
class BossConfig:
    """Complete B.O.S.S. configuration."""
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    @classmethod
    def from_file(cls, config_path: Path) -> "BossConfig":
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            hardware_data = data.get('hardware', {})
            system_data = data.get('system', {})
            
            return cls(
                hardware=HardwareConfig(**hardware_data),
                system=SystemConfig(**system_data)
            )
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            # Return default config if file doesn't exist or is invalid
            return cls()
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "hardware": self.hardware.__dict__,
            "system": self.system.__dict__
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hardware": self.hardware.__dict__,
            "system": self.system.__dict__
        }
