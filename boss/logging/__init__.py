"""Flat facade for logging setup (localized)."""

from .logger import *  # noqa: F401,F403

__all__ = [
    "setup_logging",
    "get_logger",
    "log_system_info",
    "configure_external_loggers",
    "ContextualLogger",
    "get_contextual_logger",
    "log_startup_banner",
]
