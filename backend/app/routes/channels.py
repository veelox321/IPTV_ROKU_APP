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

router = APIRouter()


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------


@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""
    auth.set_credentials(credentials)
    LOGGER.debug("Login accepted for host=%s", credentials.host)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# CHANNELS
# ---------------------------------------------------------------------------


@router.get("/channels", response_model=ChannelListResponse)
def get_channels(
    page: int = Query(1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="Number of items per page (max 100).",
    ),
    search: str | None = Query(None, min_length=1),
    category: str | None = Query(None, min_length=1),
    group: str | None = Query(None, min_length=1),
) -> ChannelListResponse:
    """
    Return paginated channels from cache.

    Filtering is applied before pagination.
    Pagination is streaming-safe (no full list slicing).
    """

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="No cached channels available. Run /refresh first.",
        )

    channels: Iterable[dict] = cached.get("channels", [])

    search_l = search.lower() if search else None
    category_l = category.lower() if category else None
    group_l = group.lower() if group else None

    def matches(channel: dict) -> bool:
        if search_l and search_l not in channel.get("name", "").lower():
            return False
        if category_l and channel.get("category", "other").lower() != category_l:
            return False
        if group_l and group_l not in channel.get("group", "").lower():
            return False
        return True

    offset = (page - 1) * page_size
    items: list[dict] = []
    total = 0

    for channel in channels:
        if not matches(channel):
            continue

        if offset <= total < offset + page_size:
            items.append(channel)

        total += 1

    return ChannelListResponse(
        channels=items,
        cached=True,
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# REFRESH (BACKGROUND)
# ---------------------------------------------------------------------------


def _refresh_job(credentials: CredentialsIn) -> None:
    """Background task: download, parse, and cache IPTV channels."""
    LOGGER.info("Background refresh started")

    try:
        playlist_text = iptv.fetch_m3u(credentials)
        channels = iptv.parse_m3u(playlist_text)

        LOGGER.info("Parsed %d channels", len(channels))
        cache.save_cache(credentials.host, channels)

    except Exception:
        LOGGER.exception("Background refresh failed")

    finally:
        cache.set_refreshing(False)
        LOGGER.info("Background refresh finished")


@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks) -> dict[str, str]:
    """
    Trigger a non-blocking refresh of the channel cache.
    Only one refresh can run at a time.
    """

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Credentials required.")

    if not cache.try_set_refreshing():
        return {"status": "already_running"}

    credentials = auth.get_credentials()
    if credentials is None:
        cache.set_refreshing(False)
        raise HTTPException(status_code=400, detail="Credentials missing.")

    background_tasks.add_task(_refresh_job, credentials)
    return {"status": "started"}


# ---------------------------------------------------------------------------
# STATUS / STATS
# ---------------------------------------------------------------------------


@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Return backend and cache status."""
    cached = cache.load_cache()

    channel_count = len(cached.get("channels", [])) if cached else 0

    return StatusResponse(
        logged_in=auth.has_credentials(),
        refreshing=cache.is_refreshing(),
        cache_available=cached is not None,
        last_refresh=cached.get("timestamp") if cached else None,
        channel_count=channel_count,
    )


@router.get("/stats", response_model=StatsResponse)
def channel_stats() -> StatsResponse:
    """Return aggregated channel statistics (O(1))."""
    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    stats = cache.get_stats(cached)

    return StatsResponse(
        total=stats.get("total", 0),
        tv=stats.get("tv", 0),
        movies=stats.get("movies", 0),
        series=stats.get("series", 0),
        other=stats.get("other", 0),
    )


@router.get("/groups")
def list_categories() -> dict[str, list[dict[str, int]] | list[str]]:
    """Return available channel categories and group-title counts (O(1))."""
    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    categories = cached.get("categories")
    group_counts = cached.get("group_counts")
    if categories is None or group_counts is None:
        raise HTTPException(500, "Group metadata not available in cache")

    groups = [
        {"name": name, "count": count}
        for name, count in sorted(
            group_counts.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
    ]

    return {
        "categories": categories,
        "groups": groups[:200],
    }


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------


@router.get("/health")
def health_check() -> JSONResponse:
    """Basic health check endpoint."""
    return JSONResponse(content={"status": "ok"})
