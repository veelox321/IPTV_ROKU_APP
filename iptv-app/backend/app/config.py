"""Application configuration loaded from environment variables."""

from functools import lru_cache
import logging
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration for the IPTV backend."""

    DEBUG: bool = Field(default=False, env="DEBUG")
    iptv_host: str | None = Field(default=None, env="IPTV_HOST")
    iptv_username: str | None = Field(default=None, env="IPTV_USERNAME")
    iptv_password: str | None = Field(default=None, env="IPTV_PASSWORD")
    cache_ttl_seconds: int = Field(default=21600, env="CACHE_TTL_SECONDS")
    verify_ssl: bool = Field(default=True, env="VERIFY_SSL")

    class Config:
        env_file = str(Path(__file__).resolve().parents[1] / ".env")
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


def configure_logging(debug: bool) -> None:
    """Configure application logging."""

    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
