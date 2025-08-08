"""
Mini-app models and business rules for B.O.S.S.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import json


class AppStatus(Enum):
    """Status of a mini-app."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class AppManifest:
    """Manifest metadata for a mini-app."""
    name: str
    description: str
    version: str
    author: str
    entry_point: str = "main.py"
    timeout_seconds: int = 300  # 5 minutes default
    requires_network: bool = False
    requires_audio: bool = False
    tags: Optional[List[str]] = None
    preferred_screen_backend: str = "auto"  # "auto", "rich", or "pillow"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_file(cls, manifest_path: Path) -> "AppManifest":
        """Load manifest from JSON file."""
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            
            # Handle different manifest formats
            # Map legacy format fields to new format
            if "id" in data and "name" not in data:
                data["name"] = data.get("title", data["id"])
            if "title" in data and "name" not in data:
                data["name"] = data["title"]
            
            # Provide defaults for required fields if missing
            if "version" not in data:
                data["version"] = "1.0.0"
            if "author" not in data:
                data["author"] = "Unknown"
            
            # Remove unknown fields that would cause TypeError
            known_fields = {
                "name", "description", "version", "author", "entry_point", 
                "timeout_seconds", "requires_network", "requires_audio", "tags",
                "preferred_screen_backend"
            }
            filtered_data = {k: v for k, v in data.items() if k in known_fields}
            
            return cls(**filtered_data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid manifest file {manifest_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "entry_point": self.entry_point,
            "timeout_seconds": self.timeout_seconds,
            "requires_network": self.requires_network,
            "requires_audio": self.requires_audio,
            "tags": self.tags,
            "preferred_screen_backend": getattr(self, 'preferred_screen_backend', 'auto')
        }


@dataclass
class App:
    """A mini-app entity with its metadata and runtime state."""
    switch_value: int  # 0-255
    manifest: AppManifest
    app_path: Path
    status: AppStatus = AppStatus.STOPPED
    last_run_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate app configuration."""
        if not 0 <= self.switch_value <= 255:
            raise ValueError(f"Switch value must be 0-255, got {self.switch_value}")
        
        if not self.app_path.exists():
            raise ValueError(f"App path does not exist: {self.app_path}")
        
        entry_point_path = self.app_path / self.manifest.entry_point
        if not entry_point_path.exists():
            raise ValueError(f"Entry point does not exist: {entry_point_path}")
    
    @property
    def is_running(self) -> bool:
        """Check if the app is currently running."""
        return self.status in (AppStatus.STARTING, AppStatus.RUNNING)
    
    @property
    def can_start(self) -> bool:
        """Check if the app can be started."""
        return self.status in (AppStatus.STOPPED, AppStatus.ERROR)
    
    def mark_starting(self) -> None:
        """Mark app as starting."""
        if not self.can_start:
            raise ValueError(f"Cannot start app in status {self.status}")
        self.status = AppStatus.STARTING
        self.error_message = None
    
    def mark_running(self) -> None:
        """Mark app as running."""
        if self.status != AppStatus.STARTING:
            raise ValueError(f"Cannot mark running from status {self.status}")
        self.status = AppStatus.RUNNING
    
    def mark_stopping(self) -> None:
        """Mark app as stopping."""
        if not self.is_running:
            raise ValueError(f"Cannot stop app in status {self.status}")
        self.status = AppStatus.STOPPING
    
    def mark_stopped(self) -> None:
        """Mark app as stopped."""
        self.status = AppStatus.STOPPED
        self.last_run_time = None
    
    def mark_error(self, error_message: str) -> None:
        """Mark app as error state."""
        self.status = AppStatus.ERROR
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "switch_value": self.switch_value,
            "manifest": self.manifest.to_dict(),
            "app_path": str(self.app_path),
            "status": self.status.value,
            "last_run_time": self.last_run_time,
            "error_message": self.error_message
        }
    
    # --- Screen backend preference helpers (US-027) ---
    def should_use_rich_backend(self, system_default: str = "pillow") -> bool:
        """Determine if this app should use Rich backend based on preference."""
        preferred = getattr(self.manifest, 'preferred_screen_backend', 'auto')
        
        if preferred == "rich":
            return True
        if preferred == "pillow":
            return False
        return system_default == "rich"
    
    def get_backend_preference_info(self) -> Dict[str, Any]:
        """Get information about backend preference for logging/debugging."""
        preferred = getattr(self.manifest, 'preferred_screen_backend', 'auto')
        has_preference = hasattr(self.manifest, 'preferred_screen_backend')
        return {
            "preferred_backend": preferred,
            "manifest_specified": has_preference,
            "fallback_reason": "Using system default" if preferred == "auto" else "App preference"
        }
    
    def validate_backend_preference(self) -> bool:
        """Validate that the backend preference is a valid value."""
        preferred = getattr(self.manifest, 'preferred_screen_backend', 'auto')
        return preferred in {"auto", "rich", "pillow"}
