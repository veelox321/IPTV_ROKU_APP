"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration for the IPTV backend."""

    iptv_host: str | None = Field(default=None, env="IPTV_HOST")
    iptv_username: str | None = Field(default=None, env="IPTV_USERNAME")
    iptv_password: str | None = Field(default=None, env="IPTV_PASSWORD")
    cache_ttl_seconds: int = Field(default=21600, env="CACHE_TTL_SECONDS")
    verify_ssl: bool = Field(default=True, env="VERIFY_SSL")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
