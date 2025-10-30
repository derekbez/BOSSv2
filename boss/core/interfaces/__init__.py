"""Core interfaces: hardware, services, and app API.

Moved from boss.domain.interfaces.* to align with flattened architecture.
"""

from .hardware import *
from .services import *
from .app_api import *

__all__ = [
    # exported by modules
]
