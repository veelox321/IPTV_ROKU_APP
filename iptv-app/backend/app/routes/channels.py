"""API routes for channel operations."""

import logging

from fastapi import APIRouter, HTTPException, Query

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


@router.get("/channels")
def get_channels(search: str | None = Query(default=None, min_length=1)) -> dict:
    """Return channels from cache only."""

    cached = cache.load_cache()
    if not cached:
        LOGGER.debug("Channel cache miss; no cache file available.")
        raise HTTPException(
            status_code=404,
            detail="No cached channels available. Run /refresh to fetch fresh data.",
        )

    channels = cached.get("channels", [])
    LOGGER.debug("Channel cache hit; returning cached channels.")

    if search:
        search_lower = search.lower()
        channels = [
            channel
            for channel in channels
            if search_lower in channel.get("name", "").lower()
        ]

    return {"channels": channels, "cached": True, "total": len(channels)}

def _refresh_job(credentials: CredentialsIn) -> None:
    LOGGER.info("Background refresh started")
    cache.set_refreshing(True)

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


from fastapi import BackgroundTasks

@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks) -> dict[str, str]:
    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Credentials required.")

    if cache.is_refreshing():
        return {"status": "already_running"}

    credentials = auth.get_credentials()
    background_tasks.add_task(_refresh_job, credentials)

    return {"status": "started"}



@router.get("/status")
def status() -> dict[str, object]:
    """Return credential and cache status information."""

    logged_in = auth.has_credentials()
    cached = cache.load_cache()
    cache_available = cached is not None
    last_refresh = cached.get("timestamp") if cached else None
    channel_count = len(cached.get("channels", [])) if cached else 0
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
        "channel_count": len(cached.get("channels", [])) if cached else 0,
    }

@router.get("/stats")
def channel_stats() -> dict[str, int]:
    cached = cache.load_cache()
    if not cached:
        raise HTTPException(404, "No cache available")

    channels = cached.get("channels", [])
    return iptv.count_categories(channels)
