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
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from backend.app.config import get_settings
from backend.app.services import iptv

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GLOBAL STATE
# ---------------------------------------------------------------------------

_CACHE_LOCK = threading.Lock()
_REFRESH_LOCK = threading.Lock()
_REFRESHING = False
_REFRESH_METADATA_LOCK = threading.Lock()
_LAST_REFRESH_STATUS: str | None = None
_LAST_REFRESH_ERROR: str | None = None
_LAST_SUCCESSFUL_REFRESH: str | None = None
_REFRESH_STARTED_AT: str | None = None
_LOAD_LOG_COUNT = 0
_LOAD_LOG_LIMIT = 5
_CACHE_SCHEMA_VERSION = 1
_CREATED_BY = "iptv-backend"



def get_cache_path() -> Path:
    """Return the cache file path (outside the repo by default)."""
    settings = get_settings()
    return settings.cache_dir / "channels.json"


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_write(path: Path, payload: dict[str, Any]) -> int:
    """Write JSON payload to disk atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    start = time.monotonic()
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
        size = fh.tell()
    tmp.replace(path)
    elapsed = time.monotonic() - start
    if get_settings().debug:
        LOGGER.info(
            "Atomic write complete tmp=%s final=%s bytes=%d elapsed=%.2fs exists=%s",
            tmp.resolve(),
            path.resolve(),
            size,
            elapsed,
            path.exists(),
        )
    return size


def _invalidate_cache_file(path: Path, reason: str) -> None:
    """Move a corrupted cache file aside so it is not reused."""
    if not path.exists():
        return
    try:
        timestamp = _now().strftime("%Y%m%dT%H%M%S")
        quarantined = path.with_suffix(f".corrupt-{timestamp}.json")
        path.replace(quarantined)
        LOGGER.warning(
            "Cache invalidated: reason=%s path=%s quarantined=%s",
            reason,
            path.resolve(),
            quarantined.resolve(),
        )
    except Exception:
        LOGGER.exception("Failed to invalidate cache file path=%s", path.resolve())


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
    global _REFRESHING, _REFRESH_STARTED_AT, _LAST_REFRESH_STATUS
    with _REFRESH_LOCK:
        _REFRESHING = value
        _REFRESH_STARTED_AT = _now().isoformat() if value else None
    if value:
        with _REFRESH_METADATA_LOCK:
            _LAST_REFRESH_STATUS = "loading"


def try_set_refreshing() -> bool:
    """Atomically set the refreshing flag if not already set."""
    global _REFRESHING, _REFRESH_STARTED_AT, _LAST_REFRESH_STATUS
    with _REFRESH_LOCK:
        if _REFRESHING:
            return False
        _REFRESHING = True
        _REFRESH_STARTED_AT = _now().isoformat()
    with _REFRESH_METADATA_LOCK:
        _LAST_REFRESH_STATUS = "loading"
        return True


def set_last_error(error: str | None) -> None:
    """Persist the last refresh error in memory."""
    global _LAST_REFRESH_STATUS, _LAST_REFRESH_ERROR
    with _REFRESH_METADATA_LOCK:
        _LAST_REFRESH_STATUS = "failed" if error else "success"
        _LAST_REFRESH_ERROR = error


def get_refresh_started_at() -> str | None:
    """Return the timestamp when refresh was set in motion."""
    with _REFRESH_LOCK:
        return _REFRESH_STARTED_AT


def get_refresh_metadata(cache_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Return refresh metadata, favoring in-memory state."""
    if cache_payload is None:
        cached_status = None
        cached_error = None
        cached_success = None
    else:
        cached_status = cache_payload.get("last_refresh_status")
        cached_error = cache_payload.get("last_refresh_error")
        cached_success = cache_payload.get("last_successful_refresh")

    with _REFRESH_METADATA_LOCK:
        status = _LAST_REFRESH_STATUS or cached_status or ("missing" if cache_payload is None else "success")
        error = _LAST_REFRESH_ERROR if _LAST_REFRESH_ERROR is not None else cached_error
        last_success = _LAST_SUCCESSFUL_REFRESH or cached_success

    return {
        "refresh_status": status,
        "last_error": error,
        "last_successful_refresh": last_success,
    }


# ---------------------------------------------------------------------------
# CACHE IO
# ---------------------------------------------------------------------------


def load_cache() -> dict[str, Any] | None:
    """Load cached channel data from disk."""
    global _LOAD_LOG_COUNT
    cache_path = get_cache_path()
    should_log = get_settings().debug or _LOAD_LOG_COUNT < _LOAD_LOG_LIMIT
    if should_log:
        _LOAD_LOG_COUNT += 1
    if not cache_path.exists():
        if should_log:
            LOGGER.info(
                "Cache read attempt: path=%s exists=false",
                cache_path.resolve(),
            )
        LOGGER.debug("Channel cache not found at %s", cache_path)
        return None

    try:
        if should_log:
            size_bytes = cache_path.stat().st_size
            LOGGER.info(
                "Cache read attempt: path=%s exists=true size_bytes=%s",
                cache_path.resolve(),
                size_bytes,
            )
        with _CACHE_LOCK, cache_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        channels = payload.get("channels")
        if not isinstance(channels, list):
            LOGGER.warning("Invalid cache payload: channels is not a list")
            _invalidate_cache_file(cache_path, "invalid_channels_payload")
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
        payload.setdefault("cache_header", {})
        payload.setdefault("last_refresh_status", "success")
        payload.setdefault("last_refresh_error", None)
        payload.setdefault("last_successful_refresh", payload.get("timestamp"))

        _sync_refresh_metadata(payload)

        if should_log:
            LOGGER.info(
                "Cache loaded: keys=%s channel_count=%s timestamp=%s host=%s",
                sorted(payload.keys()),
                payload.get("channel_count"),
                payload.get("timestamp"),
                payload.get("host"),
            )
        LOGGER.debug("Channel cache loaded (%d channels)", len(channels))
        return payload

    except json.JSONDecodeError:
        LOGGER.exception("Channel cache JSON is invalid")
        _invalidate_cache_file(cache_path, "json_decode_error")
        return None
    except Exception:
        LOGGER.exception("Failed to load channel cache")
        return None


def save_cache(host: str, channels: list[dict[str, Any]]) -> None:
    """Persist channels and precomputed metadata to disk."""
    started_at = time.monotonic()
    normalized = [_normalize_channel(ch) for ch in channels]
    group_counts = _compute_group_counts(normalized)
    stats = _compute_stats(normalized)
    timestamp = _now().isoformat()

    payload = {
        "host": host,
        "timestamp": timestamp,
        "channels": normalized,
        "channel_count": len(normalized),
        "stats": stats,
        "categories": sorted({ch["category"] for ch in normalized}),
        "group_counts": group_counts,
        "cache_header": {
            "schema_version": _CACHE_SCHEMA_VERSION,
            "created_by": _CREATED_BY,
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "python_executable": sys.executable,
        },
        "last_refresh_status": "success",
        "last_refresh_error": None,
        "last_successful_refresh": timestamp,
    }

    cache_path = get_cache_path()
    with _CACHE_LOCK:
        bytes_written = _atomic_write(cache_path, payload)

    elapsed = time.monotonic() - started_at
    LOGGER.info(
        "Channel cache saved host=%s channels=%d categories=%d bytes=%d elapsed=%.2fs path=%s",
        host,
        payload["channel_count"],
        len(payload["categories"]),
        bytes_written,
        elapsed,
        cache_path.resolve(),
    )
    _sync_refresh_metadata(payload)


def _sync_refresh_metadata(payload: dict[str, Any]) -> None:
    """Sync refresh metadata from payload into memory."""
    global _LAST_REFRESH_STATUS, _LAST_REFRESH_ERROR, _LAST_SUCCESSFUL_REFRESH
    with _REFRESH_METADATA_LOCK:
        _LAST_REFRESH_STATUS = payload.get("last_refresh_status")
        _LAST_REFRESH_ERROR = payload.get("last_refresh_error")
        _LAST_SUCCESSFUL_REFRESH = payload.get("last_successful_refresh")


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
