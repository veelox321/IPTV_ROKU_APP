"""JSON file cache utilities for channel data."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "channels.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_cache() -> dict[str, Any] | None:
    """Load cached channel data from disk if available."""

    if not CACHE_PATH.exists():
        return None
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return None


def save_cache(host: str, channels: list[dict[str, Any]]) -> None:
    """Write channel data to disk with a timestamp."""

    payload = {
        "timestamp": _now().isoformat(),
        "host": host,
        "channels": channels,
    }
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def is_cache_valid(cache: dict[str, Any], host: str, ttl_seconds: int) -> bool:
    """Validate cache timestamp and host."""

    if cache.get("host") != host:
        return False
    timestamp = cache.get("timestamp")
    if not timestamp:
        return False
    try:
        cached_at = datetime.fromisoformat(timestamp)
    except ValueError:
        return False
    expires_at = cached_at + timedelta(seconds=ttl_seconds)
    return _now() <= expires_at
