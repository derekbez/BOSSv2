"""UI facade: re-export presentation modules under a flat namespace.

This keeps Presentation out of the Phase 2 moves while offering stable
import paths for UI functionality.
"""

from boss.ui.api import web_ui as web_api  # FastAPI server, WebSocket manager
from boss.ui.text import utils as text_utils  # Text UI helpers

__all__ = [
    "web_api",
    "text_utils",
]
