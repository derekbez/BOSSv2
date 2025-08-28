"""
Logging setup for B.O.S.S.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional
from boss.domain.models.config import BossConfig


def setup_logging(config: BossConfig) -> None:
    """
    Set up logging configuration.
    
    Args:
        config: BOSS configuration
    """
    # Create logs directory if it doesn't exist
    log_file_path = Path(config.system.log_file)
    if not log_file_path.is_absolute():
        # Make it relative to project root
        current_dir = Path(__file__).parent.parent.parent
        log_file_path = current_dir / log_file_path
    
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.system.log_level, logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (route to stderr so Textual can control stdout cleanly)
    # If BOSS_CONSOLE_LOG_STDOUT=1 is set, keep legacy stdout behavior.
    log_stdout = os.getenv("BOSS_CONSOLE_LOG_STDOUT", "0") == "1"
    console_stream = sys.stdout if log_stdout else sys.stderr
    console_handler = logging.StreamHandler(console_stream)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=config.system.log_max_size_mb * 1024 * 1024,
            backupCount=config.system.log_backup_count
        )
        file_handler.setLevel(getattr(logging, config.system.log_level, logging.INFO))
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Log successful setup
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - Level: {config.system.log_level}, File: {log_file_path}")
        
    except Exception as e:
        # If file logging fails, at least we have console logging
        console_logger = logging.getLogger(__name__)
        console_logger.error(f"Failed to set up file logging: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_system_info() -> None:
    """Log system information at startup."""
    import platform
    import sys
    
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("B.O.S.S. (Buttons, Operations, Switches & Screen) Starting")
    logger.info("=" * 60)
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info("=" * 60)


def configure_external_loggers() -> None:
    """Configure logging levels for external libraries."""
    # Reduce noise from external libraries
    external_loggers = [
        'urllib3',
        'requests',
        'RPi',
        'pygame',
        'PIL'
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)


class ContextualLogger:
    """Logger with contextual information."""
    
    def __init__(self, logger: logging.Logger, context: Optional[dict] = None):
        self.logger = logger
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        """Add context to log message."""
        if self.context:
            context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"[{context_str}] {message}"
        return message
    
    def debug(self, message: str) -> None:
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str) -> None:
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str) -> None:
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str) -> None:
        self.logger.error(self._format_message(message))
    
    def critical(self, message: str) -> None:
        self.logger.critical(self._format_message(message))


def get_contextual_logger(name: str, context: Optional[dict] = None) -> ContextualLogger:
    """
    Get a contextual logger.
    
    Args:
        name: Logger name
        context: Context dictionary
        
    Returns:
        ContextualLogger instance
    """
    logger = get_logger(name)
    return ContextualLogger(logger, context)


def log_startup_banner() -> None:
    """Log the startup banner."""
    logger = get_logger(__name__)
    
    banner = r"""
 ____   ___  ____  ____
| __ ) / _ \/ ___/ ___|
|  _ \| | | \___ \___ \
| |_) | |_| |___) |__) |
|____/ \___/____/____/
    
    Buttons, Operations, Switches & Screen
    A modular hardware interface system
    """
    
    for line in banner.strip().split('\n'):
        logger.info(line)
