"""API routes for channel operations."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.config import get_settings
from app.models import CredentialsIn
from app.services import auth, cache, iptv

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""

    auth.set_credentials(credentials)
    LOGGER.debug("Login credentials accepted for host=%s.", credentials.host)
    return {"status": "ok"}


def _require_credentials() -> None:
    """Ensure credentials exist before running channel operations."""

    if not auth.has_credentials():
        LOGGER.debug("Channel request rejected: missing credentials.")
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    credentials = auth.get_credentials()
    if credentials is None:
        LOGGER.debug("Channel request rejected: credentials unavailable.")
        raise HTTPException(status_code=400, detail="Credentials not found.")


def _get_cached_payload() -> dict[str, Any]:
    """Return cached payload or raise a descriptive error."""

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    cached = cache.load_cache()
    if not cached:
        LOGGER.debug("Channel cache miss; no cache file available.")
        raise HTTPException(
            status_code=404,
            detail="No cached channels available. Run /refresh to fetch fresh data.",
        )

    if not cache.is_cache_valid(cached, credentials.host, settings.cache_ttl_seconds):
        LOGGER.debug("Channel cache invalid; host mismatch or expired.")
        raise HTTPException(
            status_code=412,
            detail="Cached channels expired or host mismatch. Run /refresh.",
        )

    LOGGER.debug("Channel cache hit; returning cached channels.")
    return cached


@router.get("/channels")
def get_channels(
    page: int = Query(..., ge=1),
    page_size: int = Query(..., ge=1, le=100),
    search: str | None = Query(default=None, min_length=1),
    category: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return paginated channels from the cache."""

    _require_credentials()

    cached = _get_cached_payload()
    channels = cached.get("channels", [])

    if category:
        category_lower = category.lower()
        channels = [
            channel
            for channel in channels
            if channel.get("category", "").lower() == category_lower
        ]

    if search:
        search_lower = search.lower()
        channels = [
            channel
            for channel in channels
            if search_lower in channel.get("name", "").lower()
        ]

    total = len(channels)
    start = (page - 1) * page_size
    end = start + page_size
    paged = channels[start:end]

    return {
        "status": "ok",
        "channels": paged,
        "cached": True,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _run_refresh() -> None:
    """Run the blocking refresh in a background worker."""

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        LOGGER.error("Refresh aborted: credentials unavailable.")
        cache.set_refreshing(False)
        return

    try:
        channels = iptv.fetch_channels(credentials, settings.verify_ssl)
        cache.save_cache(credentials.host, channels)
        LOGGER.info("Channel cache updated after refresh.")
    except RuntimeError as exc:
        LOGGER.error("IPTV refresh failed: %s", exc)
    finally:
        cache.set_refreshing(False)


@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Force refresh the channel cache asynchronously."""

    _require_credentials()

    if cache.is_refreshing():
        LOGGER.debug("Refresh rejected: already in progress.")
        raise HTTPException(status_code=409, detail="Refresh already in progress.")

    cache.set_refreshing(True)
    background_tasks.add_task(_run_refresh)
    LOGGER.info("Background refresh scheduled.")
    return {"status": "accepted"}


@router.get("/status")
def get_status() -> dict[str, Any]:
    """Return refresh status and cache metadata."""

    _require_credentials()

    cached = cache.load_cache() or {}
    return {
        "refreshing": cache.is_refreshing(),
        "last_refresh": cached.get("timestamp"),
        "channel_count": cached.get("channel_count", 0),
        "host": cached.get("host"),
    }


@router.get("/stats")
def get_stats() -> dict[str, Any]:
    """Return cached channel counts by category."""

    _require_credentials()

    cached = _get_cached_payload()
    return {"status": "ok", "stats": cache.get_stats(cached)}


@router.get("/groups")
def get_groups() -> dict[str, Any]:
    """Return distinct groups present in the cached channels."""

    _require_credentials()

    cached = _get_cached_payload()
    groups = sorted({channel.get("group", "Other") for channel in cached.get("channels", [])})
    return {"status": "ok", "groups": groups}


@router.get("/health")
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""

    return {"status": "ok"}
