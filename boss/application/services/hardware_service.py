# Compatibility shim after Phase 2b move
# Old name: hardware_service; new module: boss.core.hardware_manager
from boss.core.hardware_manager import *  # noqa: F401,F403
