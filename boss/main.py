"""
Main entry point for B.O.S.S. system with new architecture.
"""

import sys
import os
import signal
from pathlib import Path
from typing import Optional

# Add boss package to Python path
# Add repository root to Python path (avoid shadowing stdlib modules like `logging`).
# Previously we inserted the `boss` package directory which caused imports like
# `import logging` to resolve to `boss/logging` instead of the stdlib `logging`.
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Now we can import BOSS modules
from boss.config import get_effective_config, validate_config, setup_directories
from boss.logging import setup_logging, log_startup_banner, log_system_info, configure_external_loggers
from boss.hardware import create_hardware_factory, log_hardware_summary
from boss.core import EventBus
from boss.core.event_handlers import SystemEventHandler, HardwareEventHandler
from boss.core import AppManager, AppRunner, HardwareManager, SystemManager
from boss.core import AppAPI


def create_boss_system(force_hardware_type: Optional[str] = None):
    """
    Create and configure the complete BOSS system.
    
    Args:
        force_hardware_type: Force specific hardware type ("gpio", "webui", "mock")
        
    Returns:
        Tuple of (system_manager, config)
    """
    # Load configuration
    config = get_effective_config(force_hardware_type)
    
    # Set up logging
    setup_logging(config)
    configure_external_loggers()
    
    # Log startup information
    log_startup_banner()
    log_system_info()
    
    # Validate configuration
    if not validate_config(config):
        raise ValueError("Invalid configuration - check logs for details")
    
    # Set up directories
    setup_directories(config)
    
    # Create hardware factory
    hardware_factory = create_hardware_factory(
        config.hardware, 
        config.system.force_hardware_type
    )
    log_hardware_summary(hardware_factory, config.hardware)
    
    # Create event bus
    # Use positional arg to avoid analyzer confusion on dynamic exports
    event_bus = EventBus(config.system.event_queue_size)
    
    # Create services
    hardware_manager = HardwareManager(hardware_factory, event_bus)
    
    apps_directory = Path(__file__).parent / config.system.apps_directory

    app_manager = AppManager(
        apps_directory=apps_directory,
        event_bus=event_bus,
        hardware_service=hardware_manager,
        config=config,
        system_default_backend=getattr(config.hardware, 'screen_backend', 'textual'),
    )
    
    # Create app API factory function
    def create_app_api_factory(app_name: str, app_path: Path) -> AppAPI:
        return AppAPI(
            event_bus=event_bus, 
            app_name=app_name, 
            app_path=app_path, 
            app_manager=app_manager
        )
    
    app_runner = AppRunner(event_bus=event_bus, app_api_factory=create_app_api_factory)
    
    # Create system manager
    system_manager = SystemManager(
        event_bus=event_bus, 
        hardware_service=hardware_manager, 
        app_manager=app_manager, 
        app_runner=app_runner
    )
    
    # Set up event handlers
    # - SystemEventHandler: bridges core events (e.g., switch_changed -> display_update)
    # - HardwareEventHandler: applies output events to hardware
    _ = SystemEventHandler(event_bus=event_bus)
    _ = HardwareEventHandler(event_bus=event_bus, hardware_service=hardware_manager)
    
    return system_manager, config


def main():
    """Main entry point."""
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="B.O.S.S. - Buttons, Operations, Switches & Screen")
    parser.add_argument("--hardware", choices=["gpio", "webui", "mock"], 
                       help="Force hardware type")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="Override log level")
    
    args = parser.parse_args()
    
    # Set environment overrides
    if args.log_level:
        os.environ["BOSS_LOG_LEVEL"] = args.log_level
    
    if args.config:
        os.environ["BOSS_CONFIG_PATH"] = str(args.config)
    
    system_manager = None
    
    try:
        # Create BOSS system
        system_manager, config = create_boss_system(args.hardware)
        
        logger = logging.getLogger(__name__)
        logger.info("BOSS system created successfully")
        
        # Start the system
        system_manager.start()
        
        # Wait for shutdown signal
        try:
            logger.info("BOSS system running - Press Ctrl+C to stop")
            system_manager.wait_for_shutdown()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received - shutting down...")
            # Make sure the shutdown event is set
            system_manager._shutdown_event.set()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            system_manager._shutdown_event.set()
        
    except Exception as e:
        # Set up basic logging if system creation failed
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to start BOSS system: {e}")
        sys.exit(1)
    
    finally:
        if system_manager is not None:
            try:
                # Get logger for shutdown messages
                import logging
                shutdown_logger = logging.getLogger(__name__)
                shutdown_logger.info("Initiating system shutdown...")
                system_manager.stop()
                shutdown_logger.info("System shutdown complete")
            except Exception as e:
                print(f"Error during shutdown: {e}")
        
        # Force exit if needed (shouldn't be necessary with proper daemon threads)
        import time
        time.sleep(0.5)  # Give threads a moment to finish
        print("BOSS shutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
