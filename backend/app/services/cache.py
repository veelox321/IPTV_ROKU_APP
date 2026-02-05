"""
JSON file cache utilities for IPTV channel data.

Responsibilities:
- Atomic disk persistence
- Thread-safe refresh state
- Cache validation (TTL / host)
- Precomputed stats & categories (O(1) endpoints)
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from backend.app.services import iptv
from backend.app.utils.cache_utils import get_cache_path

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GLOBAL STATE
# ---------------------------------------------------------------------------

_CACHE_LOCK = threading.Lock()
_REFRESH_LOCK = threading.Lock()
_REFRESHING = False

# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payload to disk atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    tmp.replace(path)


def _normalize_channel(channel: dict[str, Any]) -> dict[str, Any]:
    """Ensure required channel fields exist."""
    channel.setdefault("name", "Unknown")
    channel.setdefault("url", "about:blank")
    group = str(channel.get("group") or "Unknown").strip() or "Unknown"
    channel["group"] = group
    raw_category = str(channel.get("category") or "").strip()
    channel["category"] = iptv.coerce_category(raw_category, group)
    return channel


def _compute_stats(channels: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Compute IPTV category statistics (ONE TIME)."""
    stats = {
        "tv": 0,
        "movies": 0,
        "series": 0,
        "other": 0,
    }

    for ch in channels:
        raw_category = str(ch.get("category") or "").strip()
        normalized = iptv.coerce_category(raw_category, str(ch.get("group") or ""))
        stats[normalized if normalized in stats else "other"] += 1

    stats["total"] = sum(stats.values())
    return stats


def _compute_group_counts(channels: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Compute raw group-title counts for fast /groups endpoint."""
    counts: dict[str, int] = {}
    for ch in channels:
        group = str(ch.get("group") or "Unknown").strip() or "Unknown"
        counts[group] = counts.get(group, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# REFRESH STATE
# ---------------------------------------------------------------------------


def is_refreshing() -> bool:
    """Return whether a refresh job is currently running."""
    with _REFRESH_LOCK:
        return _REFRESHING


def set_refreshing(value: bool) -> None:
    """Set the refresh-in-progress flag."""
    global _REFRESHING
    with _REFRESH_LOCK:
        _REFRESHING = value


def try_set_refreshing() -> bool:
    """Atomically set the refreshing flag if not already set."""
    global _REFRESHING
    with _REFRESH_LOCK:
        if _REFRESHING:
            return False
        _REFRESHING = True
        return True


# ---------------------------------------------------------------------------
# CACHE IO
# ---------------------------------------------------------------------------


def load_cache() -> dict[str, Any] | None:
    """Load cached channel data from disk."""
    cache_path = get_cache_path()
    if not cache_path.exists():
        LOGGER.debug("Channel cache not found at %s", cache_path)
        return None

    try:
        with _CACHE_LOCK, cache_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        channels = payload.get("channels")
        if not isinstance(channels, list):
            LOGGER.warning("Invalid cache payload: channels is not a list")
            return None

        # Normalize channels in-place
        for ch in channels:
            if isinstance(ch, dict):
                _normalize_channel(ch)

        payload.setdefault("channel_count", len(channels))

        stats = payload.get("stats")
        if not isinstance(stats, dict):
            stats = _compute_stats(channels)
            payload["stats"] = stats
        if "total" not in stats:
            stats["total"] = payload.get("channel_count", len(channels))

        payload.setdefault(
            "categories",
            sorted({ch.get("category", "other") for ch in channels}),
        )

        payload.setdefault("group_counts", _compute_group_counts(channels))

        LOGGER.debug("Channel cache loaded (%d channels)", len(channels))
        return payload

    except json.JSONDecodeError:
        LOGGER.exception("Channel cache JSON is invalid")
        return None
    except Exception:
        LOGGER.exception("Failed to load channel cache")
        return None


def save_cache(host: str, channels: list[dict[str, Any]]) -> None:
    """Persist channels and precomputed metadata to disk."""
    normalized = [_normalize_channel(ch) for ch in channels]
    group_counts = _compute_group_counts(normalized)
    stats = _compute_stats(normalized)

    payload = {
        "host": host,
        "timestamp": _now().isoformat(),
        "channels": normalized,
        "channel_count": len(normalized),
        "stats": stats,
        "categories": sorted({ch["category"] for ch in normalized}),
        "group_counts": group_counts,
    }

    cache_path = get_cache_path()
    with _CACHE_LOCK:
        _atomic_write(cache_path, payload)

    LOGGER.info(
        "Channel cache saved host=%s channels=%d categories=%d",
        host,
        payload["channel_count"],
        len(payload["categories"]),
    )


# ---------------------------------------------------------------------------
# CACHE VALIDATION
# ---------------------------------------------------------------------------


def is_cache_valid(
    cache: dict[str, Any],
    host: str,
    ttl_seconds: int,
) -> bool:
    """Validate cache host and TTL."""
    if cache.get("host") != host:
        LOGGER.debug("Cache invalid: host mismatch")
        return False

    timestamp = cache.get("timestamp")
    if not timestamp:
        LOGGER.debug("Cache invalid: missing timestamp")
        return False

    try:
        cached_at = datetime.fromisoformat(timestamp)
    except ValueError:
        LOGGER.debug("Cache invalid: malformed timestamp")
        return False

    if _now() > cached_at + timedelta(seconds=ttl_seconds):
        LOGGER.debug("Cache expired")
        return False

    return True


# ---------------------------------------------------------------------------
# PUBLIC FAST PATHS
# ---------------------------------------------------------------------------


def get_stats(cache_payload: dict[str, Any] | None) -> dict[str, int]:
    """Return cached stats (O(1))."""
    empty = {
        "tv": 0,
        "movies": 0,
        "series": 0,
        "other": 0,
        "total": 0,
    }
    if not cache_payload:
        return empty

    channels = cache_payload.get("channels", [])
    stats = cache_payload.get("stats")
    if not isinstance(stats, dict) or any(
        key not in stats for key in ("tv", "movies", "series", "other")
    ):
        stats = _compute_stats(channels)
        cache_payload["stats"] = stats

    stats["total"] = int(
        stats.get(
            "total",
            cache_payload.get("channel_count", len(channels)),
        )
    )
    return {
        "tv": int(stats.get("tv", 0)),
        "movies": int(stats.get("movies", 0)),
        "series": int(stats.get("series", 0)),
        "other": int(stats.get("other", 0)),
        "total": int(stats.get("total", 0)),
    }
