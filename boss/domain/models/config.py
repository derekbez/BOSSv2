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
    switch_data_pin: int
    switch_select_pins: List[int]
    go_button_pin: int

    # Button pins (color -> pin)
    button_pins: Dict[str, int]

    # LED pins (color -> pin)
    led_pins: Dict[str, int]

    # Display pins
    display_clk_pin: int
    display_dio_pin: int

    # Screen settings
    screen_width: int
    screen_height: int
    screen_fullscreen: bool
    screen_backend: str

    # Audio settings
    enable_audio: bool
    audio_volume: float
    # Optional polarity for LEDs (True = active-high, False = active-low)
    led_active_high: bool = True
    # Default character wrap width for text screen auto-wrapping (optional)
    screen_wrap_width_chars: int = 80


@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    # App settings
    app_timeout_seconds: int
    apps_directory: str
    
    # Logging settings
    log_level: str
    log_file: str
    log_max_size_mb: int
    log_backup_count: int
    
    # Event bus settings
    event_queue_size: int
    event_timeout_seconds: float
    
    # Web UI settings (for development)
    webui_enabled: bool
    webui_host: str
    webui_port: int
    
    # Network settings
    enable_api: bool
    api_port: int
    
    # Hardware detection
    auto_detect_hardware: bool
    force_hardware_type: Optional[str]


@dataclass
class BossConfig:
    """Complete B.O.S.S. configuration."""
    hardware: HardwareConfig
    system: SystemConfig
    
    @classmethod
    def from_file(cls, config_path: Path) -> "BossConfig":
        """Load configuration from JSON file. All values must be present."""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            # All sections must be present
            if 'hardware' not in data:
                raise ValueError("Missing 'hardware' section in configuration")
            if 'system' not in data:
                raise ValueError("Missing 'system' section in configuration")
            
            hardware_data = data['hardware']
            system_data = data['system']
            
            # Create hardware config - all values required
            hardware_config = HardwareConfig(
                switch_data_pin=hardware_data['switch_data_pin'],
                switch_select_pins=hardware_data['switch_select_pins'],
                go_button_pin=hardware_data['go_button_pin'],
                button_pins=hardware_data['button_pins'],
                led_pins=hardware_data['led_pins'],
                display_clk_pin=hardware_data['display_clk_pin'],
                display_dio_pin=hardware_data['display_dio_pin'],
                screen_width=hardware_data['screen_width'],
                screen_height=hardware_data['screen_height'],
                screen_fullscreen=hardware_data['screen_fullscreen'],
                screen_backend=hardware_data.get('screen_backend', 'rich'),
                enable_audio=hardware_data['enable_audio'],
                audio_volume=hardware_data['audio_volume'],
                led_active_high=hardware_data.get('led_active_high', True),
                screen_wrap_width_chars=hardware_data.get('screen_wrap_width_chars', 80)
            )
            
            # Create system config - all values required
            system_config = SystemConfig(
                app_timeout_seconds=system_data['app_timeout_seconds'],
                apps_directory=system_data['apps_directory'],
                log_level=system_data['log_level'],
                log_file=system_data['log_file'],
                log_max_size_mb=system_data['log_max_size_mb'],
                log_backup_count=system_data['log_backup_count'],
                event_queue_size=system_data['event_queue_size'],
                event_timeout_seconds=system_data['event_timeout_seconds'],
                webui_enabled=system_data['webui_enabled'],
                webui_host=system_data['webui_host'],
                webui_port=system_data['webui_port'],
                enable_api=system_data['enable_api'],
                api_port=system_data['api_port'],
                auto_detect_hardware=system_data['auto_detect_hardware'],
                force_hardware_type=system_data['force_hardware_type']
            )
            
            return cls(hardware=hardware_config, system=system_config)
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid configuration file: {e}")
    
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
