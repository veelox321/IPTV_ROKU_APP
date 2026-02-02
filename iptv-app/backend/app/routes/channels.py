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


@router.post("/refresh")
def refresh_channels() -> dict[str, str | int]:
    """Force refresh the channel cache."""

    if not auth.has_credentials():
        LOGGER.debug("Refresh request rejected: missing credentials.")
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    credentials = auth.get_credentials()
    if credentials is None:
        LOGGER.debug("Refresh request rejected: credentials unavailable.")
        raise HTTPException(status_code=400, detail="Credentials not found.")

    try:
        playlist_text = iptv.fetch_m3u(credentials)
        channels = iptv.parse_m3u(playlist_text)
        LOGGER.debug("Parsed channels count=%s", len(channels))
        channels = iptv.filter_channels(channels)
    except RuntimeError as exc:
        LOGGER.exception("IPTV refresh failed.")
        cached = cache.load_cache()
        if cached:
            cached_channels = cached.get("channels", [])
            LOGGER.debug("Returning partial response from cache count=%s.", len(cached_channels))
            return {"status": "partial", "total": len(cached_channels)}
        raise HTTPException(status_code=502, detail=str(exc))

    cache.save_cache(credentials.host, channels)
    LOGGER.debug("Channel cache updated after refresh.")
    return {"status": "ok", "total": len(channels)}


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
        "logged_in": logged_in,
        "cache_available": cache_available,
        "last_refresh": last_refresh,
        "channel_count": channel_count,
    }
