"""Utilities for creating temporary mini-apps in tests.

These helpers centralize app/manifest creation to remove duplicated inline
string templates in tests. Use these in integration tests requiring dynamic
app scenarios.
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Optional

DEFAULT_MANIFEST = {
    "description": "Test app",
    "version": "1.0.0",
    "author": "Test Suite",
    "entry_point": "main.py",
    "timeout_seconds": 5,
}

def create_app(apps_dir: Path, name: str, run_body: str = "", preferred_backend: Optional[str] = None, timeout_seconds: int = 5) -> Path:
    """Create a test mini-app directory.

    Args:
        apps_dir: Root apps directory.
        name: Directory + manifest name.
        run_body: Additional Python code inside the run function.
        preferred_backend: Optional preferred screen backend.
        timeout_seconds: App timeout for manifest.
    Returns:
        Path to created app directory.
    """
    app_dir = apps_dir / name
    app_dir.mkdir(parents=True, exist_ok=True)

    manifest = dict(DEFAULT_MANIFEST)
    manifest.update({"name": name, "timeout_seconds": timeout_seconds})
    if preferred_backend:
        manifest["preferred_screen_backend"] = preferred_backend

    (app_dir / "manifest.json").write_text(json.dumps(manifest))

    run_py = f"""def run(stop_event, api):\n    api.log_info('{name} started')\n    {run_body}\n    stop_event.set()\n"""
    (app_dir / "main.py").write_text(run_py)
    return app_dir

__all__ = ["create_app"]
