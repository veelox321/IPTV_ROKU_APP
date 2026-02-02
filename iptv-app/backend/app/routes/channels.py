"""API routes for channel operations."""

import logging

from fastapi import APIRouter, HTTPException, Query

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


@router.get("/channels")
def get_channels(search: str | None = Query(default=None, min_length=1)) -> dict:
    """Return channels, using cached data when valid."""

    if not auth.has_credentials():
        LOGGER.debug("Channel request rejected: missing credentials.")
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        LOGGER.debug("Channel request rejected: credentials unavailable.")
        raise HTTPException(status_code=400, detail="Credentials not found.")

    cached = cache.load_cache()
    if not cached:
        LOGGER.debug("Channel cache miss; no cache file available.")
        return {
            "status": "partial",
            "detail": "No cached channels available. Run /refresh to fetch fresh data.",
        }

    if not cache.is_cache_valid(cached, credentials.host, settings.cache_ttl_seconds):
        LOGGER.debug("Channel cache invalid; host mismatch or expired.")
        return {
            "status": "partial",
            "detail": "No cached channels available. Run /refresh to fetch fresh data.",
        }
    LOGGER.debug("Channel cache hit; returning cached channels.")

    channels = cached.get("channels", [])

    if search:
        search_lower = search.lower()
        channels = [
            channel
            for channel in channels
            if search_lower in channel.get("name", "").lower()
        ]

    return {"status": "ok", "channels": channels, "cached": True, "total": len(channels)}


@router.post("/refresh")
def refresh_channels() -> dict[str, str]:
    """Force refresh the channel cache."""

    if not auth.has_credentials():
        LOGGER.debug("Refresh request rejected: missing credentials.")
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        LOGGER.debug("Refresh request rejected: credentials unavailable.")
        raise HTTPException(status_code=400, detail="Credentials not found.")

    try:
        channels = iptv.fetch_channels(
            credentials,
            settings.verify_ssl,
        )
    except RuntimeError as exc:
        LOGGER.debug("IPTV refresh failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    cache.save_cache(credentials.host, channels)
    LOGGER.debug("Channel cache updated after refresh.")
    return {"status": "ok"}