"""Pydantic models for request and response validation."""

from pydantic import BaseModel, Field


class CredentialsIn(BaseModel):
    """Incoming IPTV credentials for login."""

    host: str = Field(..., min_length=3, description="IPTV host URL or hostname")
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class Channel(BaseModel):
    """Normalized channel data returned to clients."""

    name: str
    group: str
    category: str
    url: str
    tvg_logo: str | None = None
    tvg_chno: str | None = None


class ChannelListResponse(BaseModel):
    """Response wrapper for channel lists."""

    channels: list[Channel]
    total: int
    page: int
    page_size: int
    cached: bool = False


class StatusResponse(BaseModel):
    """Service status payload."""

    logged_in: bool
    refreshing: bool
    cache_available: bool
    last_refresh: str | None
    channel_count: int
    refresh_status: str = "success"
    last_error: str | None = None
    last_successful_refresh: str | None = None


class StatsResponse(BaseModel):
    """Aggregate channel counts by category."""

    total: int
    tv: int
    movies: int
    series: int
    other: int
