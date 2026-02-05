"""JSON file cache utilities for channel data."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "channels.json"
LOGGER = logging.getLogger(__name__)
_refresh_lock = Lock()
_refreshing = False


def _now() -> datetime:
    """Return the current UTC time."""

    return datetime.now(timezone.utc)


def is_refreshing() -> bool:
    """Return whether a background refresh is currently in progress."""

    with _refresh_lock:
        return _refreshing


def set_refreshing(refreshing: bool) -> None:
    """Update the in-memory refresh flag in a thread-safe way."""

    global _refreshing
    with _refresh_lock:
        _refreshing = refreshing


def load_cache() -> dict[str, Any] | None:
    """Load cached channel data from disk if available."""

    if not CACHE_PATH.exists():
        LOGGER.debug("Channel cache not found.")
        return None
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if not isinstance(payload, dict):
                LOGGER.warning("Channel cache invalid: payload is not a dict.")
                return None
            if "channels" not in payload or not isinstance(payload["channels"], list):
                LOGGER.warning("Channel cache invalid: missing channels list.")
                return None
            if "timestamp" not in payload or "host" not in payload:
                LOGGER.warning("Channel cache invalid: missing required metadata.")
                return None
            payload["channel_count"] = payload.get(
                "channel_count",
                len(payload["channels"]),
            )
            LOGGER.debug("Channel cache loaded from disk.")
            return payload
    except json.JSONDecodeError:
        LOGGER.warning("Channel cache contains invalid JSON.", exc_info=True)
        return None
    except OSError:
        LOGGER.warning("Channel cache could not be read.", exc_info=True)
        return None


def save_cache(host: str, channels: list[dict[str, Any]]) -> None:
    """Write channel data to disk with a timestamp."""

    payload = {
        "timestamp": _now().isoformat(),
        "host": host,
        "channel_count": len(channels),
        "channels": channels,
    }
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    LOGGER.debug("Channel cache written to disk for host=%s.", host)


def is_cache_valid(cache: dict[str, Any], host: str, ttl_seconds: int) -> bool:
    """Validate cache timestamp and host."""

    if cache.get("host") != host:
        LOGGER.debug("Channel cache invalidated due to host mismatch.")
        return False
    timestamp = cache.get("timestamp")
    if not timestamp:
        LOGGER.debug("Channel cache invalidated due to missing timestamp.")
        return False
    try:
        cached_at = datetime.fromisoformat(timestamp)
    except ValueError:
        LOGGER.debug("Channel cache invalidated due to malformed timestamp.")
        return False
    expires_at = cached_at + timedelta(seconds=ttl_seconds)
    is_valid = _now() <= expires_at
    if not is_valid:
        LOGGER.debug("Channel cache expired.")
    return is_valid


def get_stats(cache: dict[str, Any]) -> dict[str, int]:
    """Return channel counts grouped by normalized category."""

    counts = {"tv": 0, "movies": 0, "series": 0, "other": 0}
    for channel in cache.get("channels", []):
        category = channel.get("category", "other")
        if category not in counts:
            category = "other"
        counts[category] += 1
    counts["total"] = cache.get("channel_count", sum(counts.values()))
    return counts
