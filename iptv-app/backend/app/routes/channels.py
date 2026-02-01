"""API routes for channel operations."""

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.models import ChannelListResponse, CredentialsIn
from app.services import auth, cache, iptv

router = APIRouter()


@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""

    auth.set_credentials(credentials)
    return {"status": "ok"}


@router.get("/channels", response_model=ChannelListResponse)
def get_channels(search: str | None = Query(default=None, min_length=1)) -> ChannelListResponse:
    """Return channels, using cached data when valid."""

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Login required before fetching channels.")

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    cached = cache.load_cache()
    if cached and cache.is_cache_valid(cached, credentials.host, settings.cache_ttl_seconds):
        channels = []
        for channel in cached.get("channels", []):
            if isinstance(channel, dict):
                stream_url = channel.get("stream_url") or channel.get("url")
                if stream_url:
                    channel = {**channel, "stream_url": stream_url}
            channels.append(channel)
        cached_flag = True
    else:
        raise HTTPException(
            status_code=404,
            detail="Channel cache missing or expired. Refresh required.",
        )

    if search:
        search_lower = search.lower()
        channels = [
            channel
            for channel in channels
            if search_lower in channel.get("name", "").lower()
        ]

    return ChannelListResponse(channels=channels, cached=cached_flag, total=len(channels))


@router.post("/refresh", response_model=ChannelListResponse)
def refresh_channels() -> ChannelListResponse:
    """Force refresh the channel cache."""

    if not auth.has_credentials():
        raise HTTPException(status_code=400, detail="Login required before refreshing channels.")

    settings = get_settings()
    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials not found.")

    try:
        channels = iptv.fetch_channels(credentials, settings.verify_ssl)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        cache.save_cache(credentials.host, channels)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to save channel cache.") from exc

    return ChannelListResponse(channels=channels, cached=False, total=len(channels))
