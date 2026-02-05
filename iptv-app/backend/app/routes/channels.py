"""API routes for channel operations."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models import ChannelListResponse, CredentialsIn, StatsResponse, StatusResponse
from app.services import auth, cache, iptv

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""

    auth.set_credentials(credentials)
    LOGGER.debug("Login credentials accepted for host=%s.", credentials.host)
    return {"status": "ok"}


@router.get("/channels")
def get_channels(
    page: int = Query(..., ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        ...,
        ge=1,
        le=100,
        description="Page size (max 100).",
    ),
    search: str | None = Query(default=None, min_length=1),
    category: str | None = Query(default=None, min_length=1),
) -> ChannelListResponse:
    """Return paginated channels from cache."""

    cached = cache.load_cache()
    if not cached:
        LOGGER.debug("Channel cache miss; no cache file available.")
        raise HTTPException(
            status_code=404,
            detail="No cached channels available. Run /refresh to fetch fresh data.",
        )

    channels = cached.get("channels", [])
    LOGGER.debug("Channel cache hit; returning cached channels.")

    search_lower = search.lower() if search else None
    category_lower = category.lower() if category else None

    def matches(channel: dict) -> bool:
        if search_lower and search_lower not in str(channel.get("name", "")).lower():
            return False
        if category_lower and category_lower != str(channel.get("category", "")).lower():
            return False
        return True

    offset = (page - 1) * page_size
    page_items = []
    total = 0
    for channel in channels:
        if not matches(channel):
            continue
        if offset <= total < offset + page_size:
            page_items.append(channel)
        total += 1

    return ChannelListResponse(
        channels=page_items,
        cached=True,
        total=total,
        page=page,
        page_size=page_size,
    )

def _refresh_job(credentials: CredentialsIn) -> None:
    """Background refresh job for downloading and parsing channels."""

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
    """Queue a non-blocking refresh of the channel cache."""

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Credentials required.")

    if not cache.try_set_refreshing():
        return {"status": "already_running"}

    credentials = auth.get_credentials()
    if credentials is None:
        cache.set_refreshing(False)
        raise HTTPException(status_code=400, detail="Credentials required.")
    background_tasks.add_task(_refresh_job, credentials)

    return {"status": "started"}



@router.get("/status")
def status() -> StatusResponse:
    """Return credential and cache status information."""

    logged_in = auth.has_credentials()
    cached = cache.load_cache()
    cache_available = cached is not None
    last_refresh = cached.get("timestamp") if cached else None
    channel_count = cached.get("channel_count", 0) if cached else 0
    LOGGER.debug(
        "Status requested logged_in=%s cache_available=%s last_refresh=%s channel_count=%s",
        logged_in,
        cache_available,
        last_refresh,
        channel_count,
    )
    return {
        "logged_in": auth.has_credentials(),
        "refreshing": cache.is_refreshing(),
        "cache_available": cached is not None,
        "last_refresh": cached.get("timestamp") if cached else None,
        "channel_count": cached.get("channel_count", 0) if cached else 0,
    }

@router.get("/stats")
def channel_stats() -> StatsResponse:
    """Return aggregated channel counts from cache."""

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    counts = cache.get_stats(cached)
    return StatsResponse(**counts)


@router.get("/groups")
def list_categories() -> dict[str, list[str]]:
    """Return available channel categories based on cached data."""

    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")
    categories = {
        channel.get("category", "other") for channel in cached.get("channels", [])
    }
    return {"categories": sorted(categories)}


@router.get("/health")
def health_check() -> JSONResponse:
    """Basic service health check endpoint."""

    return JSONResponse(content={"status": "ok"})
