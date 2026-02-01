"""API routes for channel operations."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import Channel, ChannelListResponse, CredentialsIn
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


@router.get("/channels", response_model=ChannelListResponse)
def get_channels(
    search: str | None = Query(default=None, min_length=1),
) -> ChannelListResponse | Response:
    """Return channels from cache only."""

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Login required before fetching channels.")

    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    cached = cache.load_cache()
    channels = []
    cached_flag = False
    if cached and cached.get("host") == credentials.host:
        channels = cached.get("channels", [])
        cached_flag = True

    if not channels:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if search:
        search_lower = search.lower()
        channels = [
            channel
            for channel in channels
            if search_lower in channel.get("name", "").lower()
        ]

    return ChannelListResponse(channels=channels, cached=cached_flag, total=len(channels))


@router.post("/refresh", response_model=RefreshResponse)
def refresh_channels() -> RefreshResponse:
    """Force refresh the channel cache."""

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Login required before refreshing channels.")

    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    settings = get_settings()
    try:
        channels = [
            channel.dict()
            for channel in iptv.fetch_channels(credentials, settings.verify_ssl)
        ]
    except Exception as exc:  # noqa: BLE001 - ensure resilience with upstream failures.
        cached = cache.load_cache()
        cached_channels = 0
        cache_available = False
        if cached and cached.get("host") == credentials.host:
            cached_channels = len(cached.get("channels", []))
            cache_available = cached_channels > 0
        if cache_available:
            return RefreshResponse(
                status="partial",
                detail="IPTV provider unavailable, using cached channels",
                cached_channels=cached_channels,
            )
        raise HTTPException(
            status_code=502,
            detail=f"IPTV provider unavailable: {exc}",
        ) from exc

    cache.save_cache(credentials.host, channels)
    return RefreshResponse(
        status="ok",
        detail="Channels refreshed successfully.",
        channels=channels,
        total=len(channels),
    )


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Return backend status information."""

    credentials = auth.get_credentials()
    cached = cache.load_cache()
    cache_available = False
    last_refresh = None
    channel_count = 0
    if cached:
        cache_available = True
        last_refresh = cached.get("timestamp")
        channel_count = len(cached.get("channels", []))
        if credentials and cached.get("host") != credentials.host:
            cache_available = False
            channel_count = 0
            last_refresh = None

    return StatusResponse(
        logged_in=auth.has_credentials(),
        cache_available=cache_available,
        last_refresh=last_refresh,
        channel_count=channel_count,
    )
