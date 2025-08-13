"""
Configuration management for B.O.S.S.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from boss.domain.models.config import BossConfig, HardwareConfig, SystemConfig

logger = logging.getLogger(__name__)




def get_config_path() -> Path:
    """Get the configuration file path."""
    # Check environment variable first
    config_path = os.environ.get("BOSS_CONFIG_PATH")
    if config_path:
        return Path(config_path)

    # Always use the canonical config path: <project_root>/boss/config/boss_config.json
    # Find project root (the parent of the 'boss' package)
    current_dir = Path(__file__).resolve()
    # Traverse up until we find the 'boss' directory
    for parent in current_dir.parents:
        if (parent / "boss" / "config" / "boss_config.json").exists():
            return parent / "boss" / "config" / "boss_config.json"
    # Fallback: assume this file is in <project_root>/boss/infrastructure/config/
    project_root = Path(__file__).parent.parent.parent
    return project_root / "boss" / "config" / "boss_config.json"


def load_config(config_path: Optional[Path] = None) -> BossConfig:
    """
    Load configuration from file. Config file is REQUIRED.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        BossConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if config_path is None:
        config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            f"B.O.S.S. requires a valid configuration file to match your hardware setup. "
            f"Please ensure {config_path} exists with correct pin assignments."
        )
    
    try:
        logger.info(f"Loading configuration from {config_path}")
        config = BossConfig.from_file(config_path)
        
        # Validate the loaded configuration
        if not validate_config(config):
            raise ValueError("Configuration validation failed")
            
        logger.info("Configuration loaded and validated successfully")
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise ValueError(f"Failed to load valid configuration: {e}") from e


def save_config(config: BossConfig, config_path: Optional[Path] = None) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save
        config_path: Optional path to config file
    """
    if config_path is None:
        config_path = get_config_path()
    
    try:
        config.save_to_file(config_path)
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")


def get_effective_config(force_hardware_type: Optional[str] = None) -> BossConfig:
    """
    Get effective configuration with environment overrides.
    
    Args:
        force_hardware_type: Force specific hardware type
        
    Returns:
        BossConfig with environment overrides applied
    """
    config = load_config()
    
    # Apply environment overrides
    if force_hardware_type:
        config.system.force_hardware_type = force_hardware_type
        logger.info(f"Hardware type forced to: {force_hardware_type}")
    
    # Check for test mode
    if os.environ.get("BOSS_TEST_MODE") == "1":
        config.system.force_hardware_type = "mock"
        config.system.log_level = "DEBUG"
        logger.info("Test mode enabled - using mock hardware")
    
    # Check for development mode
    if os.environ.get("BOSS_DEV_MODE") == "1":
        config.system.webui_enabled = True
        config.system.log_level = "DEBUG"
        logger.info("Development mode enabled")
    
    # Apply log level override
    log_level = os.environ.get("BOSS_LOG_LEVEL")
    if log_level:
        config.system.log_level = log_level.upper()
        logger.info(f"Log level set to: {config.system.log_level}")
    
    return config


def validate_config(config: BossConfig) -> bool:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
    """
    valid = True
    
    # Validate hardware config
    if not 1 <= config.hardware.switch_data_pin <= 40:
        logger.error(f"Invalid switch data pin: {config.hardware.switch_data_pin}")
        valid = False
    
    if not 1 <= config.hardware.go_button_pin <= 40:
        logger.error(f"Invalid Go button pin: {config.hardware.go_button_pin}")
        valid = False
    
    # Validate pin uniqueness (for GPIO mode)
    used_pins = set()
    all_pins = [
        config.hardware.switch_data_pin,
        config.hardware.go_button_pin,
        config.hardware.display_clk_pin,
        config.hardware.display_dio_pin
    ]
    all_pins.extend(config.hardware.switch_select_pins)
    all_pins.extend(config.hardware.button_pins.values())
    all_pins.extend(config.hardware.led_pins.values())
    
    for pin in all_pins:
        if pin in used_pins:
            logger.error(f"Duplicate pin assignment: {pin}")
            valid = False
        used_pins.add(pin)

    # Validate screen settings and backend
    backend = (getattr(config.hardware, 'screen_backend', 'rich') or '').lower()
    if backend not in {"rich", "pillow"}:
        logger.warning(f"Invalid screen_backend '{backend}' in config; defaulting to 'rich'")
        try:
            config.hardware.screen_backend = 'rich'
        except Exception:
            pass
    else:
        # Normalize stored value
        try:
            config.hardware.screen_backend = backend
        except Exception:
            pass

    if getattr(config.hardware, 'screen_width', 0) <= 0 or getattr(config.hardware, 'screen_height', 0) <= 0:
        logger.error(f"Invalid screen dimensions: {config.hardware.screen_width}x{config.hardware.screen_height}")
        valid = False
    else:
        logger.info(
            f"Screen configured as {config.hardware.screen_width}x{config.hardware.screen_height}, backend={config.hardware.screen_backend}"
        )
        # Hint to verify framebuffer geometry on Linux
        try:
            import platform
            if platform.system() == 'Linux':
                logger.info("Tip: Verify framebuffer geometry matches config: fbset -fb /dev/fb0 -i")
        except Exception:
            pass
    
    # Validate system config
    if config.system.app_timeout_seconds < 1:
        logger.error(f"Invalid app timeout: {config.system.app_timeout_seconds}")
        valid = False
    
    if config.system.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.error(f"Invalid log level: {config.system.log_level}")
        valid = False
    
    return valid


def get_apps_directory(config: BossConfig) -> Path:
    """Get the apps directory path."""
    current_dir = Path(__file__).parent.parent.parent
    return current_dir / config.system.apps_directory


def get_logs_directory(config: BossConfig) -> Path:
    """Get the logs directory path."""
    current_dir = Path(__file__).parent.parent.parent
    log_file_path = Path(config.system.log_file)
    if log_file_path.is_absolute():
        return log_file_path.parent
    else:
        return current_dir / log_file_path.parent


def setup_directories(config: BossConfig) -> None:
    """Ensure required directories exist."""
    directories = [
        get_apps_directory(config),
        get_logs_directory(config),
        get_config_path().parent
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
