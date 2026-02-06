"""Application configuration loaded from environment variables."""

from functools import lru_cache
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CACHE_DIR = Path(
    os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"),
) / "iptv_roku_app"
DEFAULT_CREDENTIALS_FILE = Path(__file__).resolve().parents[1] / ".local" / "credentials.json"


class Settings(BaseSettings):
    """Runtime configuration for the IPTV backend."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        case_sensitive=False,
    )

    debug: bool = Field(default=False, validation_alias="DEBUG")
    cache_dir: Path = Field(default=DEFAULT_CACHE_DIR, validation_alias="CACHE_DIR")
    cache_ttl_seconds: int = Field(default=21600, validation_alias="CACHE_TTL_SECONDS")
    verify_ssl: bool = Field(default=True, validation_alias="VERIFY_SSL")
    credentials_file: Path = Field(
        default=DEFAULT_CREDENTIALS_FILE,
        validation_alias="CREDENTIALS_FILE",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
