"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the IPTV backend."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        case_sensitive=False,
    )

    debug: bool = Field(default=False, validation_alias="DEBUG")
    iptv_host: str | None = Field(default=None, validation_alias="IPTV_HOST")
    iptv_username: str | None = Field(default=None, validation_alias="IPTV_USERNAME")
    iptv_password: str | None = Field(default=None, validation_alias="IPTV_PASSWORD")
    cache_ttl_seconds: int = Field(default=21600, validation_alias="CACHE_TTL_SECONDS")
    verify_ssl: bool = Field(default=True, validation_alias="VERIFY_SSL")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
