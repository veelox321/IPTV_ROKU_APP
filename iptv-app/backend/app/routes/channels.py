"""API routes for channel operations."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import CredentialsIn
from app.services import auth, cache, iptv

router = APIRouter()


class RefreshResponse(BaseModel):
    """Response for refresh attempts."""

    status: Literal["ok", "partial", "error"]
    detail: str = Field(..., min_length=1)
    cached_channels: int | None = None
    channels: list[Channel] | None = None
    total: int | None = None


class StatusResponse(BaseModel):
    """Status summary for the IPTV backend."""

    logged_in: bool
    cache_available: bool
    last_refresh: str | None
    channel_count: int


@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""

    auth.set_credentials(credentials)
    return {"status": "ok"}


@router.get("/channels")
def get_channels(search: str | None = Query(default=None, min_length=1)) -> dict:
    """Return channels, using cached data when valid."""

    if not auth.has_credentials():
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    cached = cache.load_cache()
    if not cached or not cache.is_cache_valid(cached, credentials.host, settings.cache_ttl_seconds):
        return {
            "status": "partial",
            "detail": "No cached channels available. Run /refresh to fetch fresh data.",
        }

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
        raise HTTPException(
            status_code=400,
            detail="Credentials required. Provide via /login or env settings.",
        )

    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    try:
        channels = iptv.fetch_channels(
            {"host": credentials.host, "username": credentials.username, "password": credentials.password},
            settings.verify_ssl,
            debug=settings.DEBUG,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    cache.save_cache(credentials.host, channels)
    return {"status": "ok"}
