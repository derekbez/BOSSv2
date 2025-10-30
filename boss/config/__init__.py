"""Flat facade for configuration layer.

Re-exports config manager utilities and the secrets singleton from local modules.
"""

from .config_manager import *  # noqa: F401,F403
from .secrets_manager import secrets  # explicit export

__all__ = [
    # config manager API
    "get_config_path",
    "load_config",
    "save_config",
    "get_effective_config",
    "validate_config",
    "get_apps_directory",
    "get_logs_directory",
    "setup_directories",
    # secrets
    "secrets",
]
