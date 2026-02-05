"""Cache path helpers for IPTV data."""

from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings


CACHE_FILENAME = "channels.json"


def get_cache_path() -> Path:
    """Return the cache file path (outside the repo by default)."""
    settings = get_settings()
    return settings.cache_dir / CACHE_FILENAME
