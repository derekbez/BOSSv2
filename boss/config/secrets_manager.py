"""Lightweight secrets helper for mini-apps & services.

Loads environment variables directly. In development it also (optionally) reads
`secrets/secrets.env` if present, without overriding already-set process env.

Design goals:
* Zero external dependencies
* Predictable precedence (process > file)
* Safe to import early (lazy file parse)
* Future pluggable backends (encrypted file, OS keyring) without API break
"""
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Default: repo-root/secrets/secrets.env
# __file__ = boss/config/secrets_manager.py -> parents[2] = repo root
_DEFAULT_SECRET_FILE = Path(__file__).resolve().parents[2] / "secrets" / "secrets.env"
_SYSTEM_SECRET_FILE = Path("/etc/boss/secrets.env")  # production Pi standard


class _SecretsManager:
    def __init__(self, secret_file: Path = _DEFAULT_SECRET_FILE):
        self._secret_file = secret_file
        self._loaded = False
        self._file_cache: Dict[str, str] = {}
        self._lock = RLock()

    # Public API -----------------------------------------------------
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return secret by key.

        Precedence: process env > file cache > default.
        """
        if key in os.environ:
            return os.environ[key]
        self._ensure_loaded()
        return self._file_cache.get(key, default)

    def as_dict(self) -> Dict[str, str]:
        """Return a merged snapshot of secrets (process env takes precedence)."""
        self._ensure_loaded()
        out = dict(self._file_cache)
        out.update(os.environ)  # overwrite with real env values
        return out

    # Internal -------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_file()
            self._loaded = True

    def _load_file(self) -> None:
        """Load secrets from first existing candidate file.

        Precedence for file loading (process env still wins overall):
        1. Explicit override via env BOSS_SECRETS_FILE
        2. Instance-provided path (repo local secrets/secrets.env)
        3. System path /etc/boss/secrets.env
        """
        candidates = []
        override = os.environ.get("BOSS_SECRETS_FILE")
        if override:
            candidates.append(Path(override))
        candidates.append(self._secret_file)
        if _SYSTEM_SECRET_FILE not in candidates:
            candidates.append(_SYSTEM_SECRET_FILE)

        for path in candidates:
            if not path.exists():
                continue
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        logger.warning("Ignoring malformed secret line (no '='): %s", line)
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and key not in os.environ:  # do not override real env
                        self._file_cache[key] = value
                logger.debug("Loaded secrets from %s (keys=%d)", path, len(self._file_cache))
                return  # stop after first existing file
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed loading secrets file: %s", path)
        # None found; silent (acceptable) — rely purely on process env


# Singleton instance
secrets = _SecretsManager()

__all__ = ["secrets", "_SecretsManager"]
