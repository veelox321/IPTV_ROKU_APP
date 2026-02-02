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
    url: str


class ChannelListResponse(BaseModel):
    """Response wrapper for channel lists."""

    channels: list[Channel]
    cached: bool = False
    total: int
