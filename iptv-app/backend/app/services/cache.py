"""JSON file cache utilities for channel data."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import threading

_refresh_lock = threading.Lock()
_refreshing = False

CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "channels.json"
LOGGER = logging.getLogger(__name__)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payload to disk atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(path)


def _normalize_cache_payload(payload: Any) -> dict[str, Any] | None:
    """Validate and normalize the cache payload structure."""

    if not isinstance(payload, dict):
        LOGGER.warning("Channel cache payload is not a dictionary.")
        return None

    channels = payload.get("channels")
    if not isinstance(channels, list):
        LOGGER.warning("Channel cache payload has invalid channels list.")
        return None

    from app.services import iptv

    for channel in channels:
        if not isinstance(channel, dict):
            continue
        if "category" not in channel:
            channel["category"] = iptv.normalize_category(str(channel.get("group", "")))
        if "group" not in channel:
            channel["group"] = "Unknown"
        if "name" not in channel:
            channel["name"] = "Unknown"
        if "url" not in channel:
            channel["url"] = ""

    payload.setdefault("channel_count", len(channels))
    payload.setdefault("timestamp", None)
    payload.setdefault("host", None)
    return payload


def is_refreshing() -> bool:
    """Check whether a refresh job is currently running."""

    with _refresh_lock:
        return _refreshing


def set_refreshing(value: bool) -> None:
    """Set the refresh-in-progress flag."""

    global _refreshing
    with _refresh_lock:
        _refreshing = value


def try_set_refreshing() -> bool:
    """Atomically set the refreshing flag if not already set."""

    global _refreshing
    with _refresh_lock:
        if _refreshing:
            return False
        _refreshing = True
        return True


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_cache() -> dict[str, Any] | None:
    """Load cached channel data from disk if available."""

    if not CACHE_PATH.exists():
        LOGGER.debug("Channel cache not found at path=%s.", CACHE_PATH)
        return None
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            normalized = _normalize_cache_payload(payload)
            if normalized is None:
                LOGGER.warning("Channel cache payload structure invalid.")
                return None
            LOGGER.debug("Channel cache loaded from disk.")
            return normalized
    except json.JSONDecodeError:
        LOGGER.warning("Channel cache contains invalid JSON.", exc_info=True)
        return None
    except Exception:
        LOGGER.exception("Failed to read channel cache from disk.")
        return None


def save_cache(host: str, channels: list[dict[str, Any]]) -> None:
    """Write channel data to disk with a timestamp."""

    payload = {
        "timestamp": _now().isoformat(),
        "host": host,
        "channel_count": len(channels),
        "channels": channels,
    }
    _atomic_write(CACHE_PATH, payload)
    LOGGER.debug(
        "Channel cache written to disk for host=%s count=%s.", host, len(channels)
    )


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


def get_stats(cache_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Return aggregate stats for cached channels."""

    if not cache_payload:
        return {
            "total": 0,
            "tv": 0,
            "movies": 0,
            "series": 0,
            "other": 0,
        }

    from app.services import iptv

    channels = cache_payload.get("channels", [])
    counts = iptv.count_categories(channels)
    counts["total"] = cache_payload.get("channel_count", len(channels))
    return counts
