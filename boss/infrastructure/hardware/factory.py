"""
Hardware factory with automatic platform detection.
"""

import logging
import platform
import os
from typing import Optional
from boss.domain.interfaces.hardware import HardwareFactory
from boss.domain.models.config import HardwareConfig

logger = logging.getLogger(__name__)


def detect_hardware_platform() -> str:
    """
    Automatically detect the best hardware implementation to use.
    
    Returns:
        "gpio" for Raspberry Pi with GPIO access
        "webui" for development on other platforms
        "mock" for testing
    """
    system = platform.system()
    machine = platform.machine()
    
    # Check if we're on Raspberry Pi (32/64-bit) and GPIO libraries are available
    if system == "Linux" and (machine.startswith("arm") or machine == "aarch64"):
        # Try to import one of the supported GPIO libraries
        try:
            import gpiozero  # noqa: F401
            # Check if lgpio is available (preferred backend for gpiozero)
            try:
                import lgpio  # noqa: F401
                logger.info("Detected Raspberry Pi with gpiozero + lgpio GPIO access (optimal)")
            except ImportError:
                logger.info("Detected Raspberry Pi with gpiozero GPIO access (using fallback backend)")
            return "gpio"
        except ImportError:
            try:
                import lgpio  # noqa: F401
                logger.info("Detected Raspberry Pi with lgpio GPIO access")
                return "gpio"
            except ImportError:
                try:
                    import python_tm1637  # noqa: F401
                    logger.info("Detected Raspberry Pi with python-tm1637 GPIO access")
                    return "gpio"
                except ImportError:
                    logger.info("Raspberry Pi detected but no supported GPIO library available (gpiozero, lgpio, python-tm1637)")
    
    # Check for testing environment
    if os.environ.get("BOSS_TEST_MODE") == "1":
        logger.info("Test mode detected")
        return "mock"
    
    # Default to WebUI for development
    logger.info(f"Development platform detected: {system} {machine}")
    return "webui"


def create_hardware_factory(hardware_config: HardwareConfig, force_type: Optional[str] = None) -> HardwareFactory:
    """
    Create appropriate hardware factory based on platform detection or force type.
    
    Args:
        hardware_config: Hardware configuration
        force_type: Force specific hardware type ("gpio", "webui", "mock")
    
    Returns:
        Hardware factory implementation
    """
    if force_type:
        hardware_type = force_type
        logger.info(f"Forcing hardware type: {hardware_type}")
    else:
        hardware_type = detect_hardware_platform()
    
    if hardware_type == "gpio":
        from .gpio.gpio_factory import GPIOHardwareFactory
        return GPIOHardwareFactory(hardware_config)
    
    elif hardware_type == "webui":
        from .webui.webui_factory import WebUIHardwareFactory
        return WebUIHardwareFactory(hardware_config)
    
    elif hardware_type == "mock":
        from .mock.mock_factory import MockHardwareFactory
        return MockHardwareFactory(hardware_config)
    
    else:
        raise ValueError(f"Unknown hardware type: {hardware_type}")


def log_hardware_summary(factory: HardwareFactory, hardware_config: HardwareConfig) -> None:
    """Log a summary of hardware configuration at startup."""
    logger.info("=" * 50)
    logger.info("BOSS Hardware Configuration Summary")
    logger.info("=" * 50)
    logger.info(f"Hardware Type: {factory.hardware_type}")
    logger.info(f"Platform: {platform.system()} {platform.machine()}")
    
    if factory.hardware_type == "gpio":
        logger.info("GPIO Pin Assignments:")
        logger.info(f"  Switch Data Pin: {hardware_config.switch_data_pin}")
        logger.info(f"  Switch Select Pins: {hardware_config.switch_select_pins}")
        logger.info(f"  Go Button Pin: {hardware_config.go_button_pin}")
        logger.info(f"  Button Pins: {hardware_config.button_pins}")
        logger.info(f"  LED Pins: {hardware_config.led_pins}")
        logger.info(f"  Display CLK Pin: {hardware_config.display_clk_pin}")
        logger.info(f"  Display DIO Pin: {hardware_config.display_dio_pin}")
    
    elif factory.hardware_type == "webui":
        logger.info("Web UI Configuration:")
        logger.info(f"  Development interface available for testing")
        logger.info(f"  Screen Size: {hardware_config.screen_width}x{hardware_config.screen_height}")
    
    elif factory.hardware_type == "mock":
        logger.info("Mock Hardware Configuration:")
        logger.info(f"  All hardware components mocked for testing")
    
    logger.info(f"Audio Enabled: {hardware_config.enable_audio}")
    logger.info(f"Screen Fullscreen: {hardware_config.screen_fullscreen}")
    logger.info("=" * 50)
