"""
API routes for IPTV channel operations.

Endpoints:
- POST   /login
- GET    /channels
- POST   /refresh
- GET    /status
- GET    /stats
- GET    /groups
- GET    /health
"""

import logging
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.app.models import (
    ChannelListResponse,
    CredentialsIn,
    StatsResponse,
    StatusResponse,
)
from backend.app.services import auth, cache, iptv

LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["channels"])


# ============================================================================
# AUTH
# ============================================================================

@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""
    auth.set_credentials(credentials)
    LOGGER.info("Login accepted for host=%s", credentials.host)
    return {"status": "ok"}


# ============================================================================
# CHANNELS
# ============================================================================

@router.get("/channels", response_model=ChannelListResponse)
def get_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    category: str | None = Query(None, min_length=1),
    group: str | None = Query(None, min_length=1),
) -> ChannelListResponse:
    """
    Return paginated channels from cache.

    Filtering is applied BEFORE pagination.
    Streaming-safe: no full list slicing.
    """

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cached channels available. Run /refresh first.")

    channels: Iterable[dict] = cached.get("channels", [])

    search_l = search.lower() if search else None
    category_l = category.lower() if category else None
    group_l = group.lower() if group else None

    def matches(ch: dict) -> bool:
        if search_l and search_l not in ch.get("name", "").lower():
            return False
        if category_l and ch.get("category", "other") != category_l:
            return False
        if group_l and group_l not in ch.get("group", "").lower():
            return False
        return True

    offset = (page - 1) * page_size
    items: list[dict] = []
    total = 0

    for ch in channels:
        if not matches(ch):
            continue

        if offset <= total < offset + page_size:
            items.append(ch)

        total += 1

    return ChannelListResponse(
        channels=items,
        cached=True,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# REFRESH (BACKGROUND)
# ============================================================================

def _refresh_job(credentials: CredentialsIn) -> None:
    """Background task: fetch, parse and cache IPTV playlist."""
    LOGGER.info("Background refresh started")

    try:
        playlist = iptv.fetch_m3u(credentials)
        channels = iptv.parse_m3u(playlist)

        LOGGER.info("Parsed %d channels", len(channels))
        cache.save_cache(credentials.host, channels)

    except Exception:
        LOGGER.exception("Background refresh failed")

    finally:
        cache.set_refreshing(False)
        LOGGER.info("Background refresh finished")


@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger a non-blocking refresh of the channel cache."""

    if not auth.has_credentials():
        raise HTTPException(400, "Credentials required")

    if not cache.try_set_refreshing():
        return {"status": "already_running"}

    credentials = auth.get_credentials()
    if credentials is None:
        cache.set_refreshing(False)
        raise HTTPException(400, "Credentials missing")

    background_tasks.add_task(_refresh_job, credentials)
    return {"status": "started"}


# ============================================================================
# STATUS / STATS
# ============================================================================

@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Return backend and cache status."""

    cached = cache.load_cache()

    return StatusResponse(
        logged_in=auth.has_credentials(),
        refreshing=cache.is_refreshing(),
        cache_available=cached is not None,
        last_refresh=cached.get("timestamp") if cached else None,
        channel_count=cached.get("channel_count", 0) if cached else 0,
    )


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    """Return aggregated channel statistics."""

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    counts = cache.get_stats(cached)

    return StatsResponse(
        total=counts["total"],
        tv=counts["tv"],
        movies=counts["movies"],
        series=counts["series"],
        other=counts["other"],
    )


@router.get("/groups")
def groups() -> dict:
    """Return categories and most common group titles."""

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    return {
        "categories": cached.get("categories", []),
        "groups": cached.get("group_counts", {}),
    }


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok"})
