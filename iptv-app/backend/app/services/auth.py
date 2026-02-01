"""In-memory credential storage service."""

from typing import Optional

from app.config import get_settings
from app.models import CredentialsIn


_credentials: Optional[CredentialsIn] = None


def load_env_credentials() -> Optional[CredentialsIn]:
    """Load credentials from environment if fully configured."""

    settings = get_settings()
    if not settings.IPTV_HOST or not settings.IPTV_USERNAME or not settings.IPTV_PASSWORD:
        return None

    return CredentialsIn(
        host=settings.IPTV_HOST,
        username=settings.IPTV_USERNAME,
        password=settings.IPTV_PASSWORD,
    )


def set_credentials(credentials: CredentialsIn) -> None:
    """Persist credentials in memory for this process."""

    global _credentials
    _credentials = credentials


def get_credentials() -> Optional[CredentialsIn]:
    """Return credentials if they have been set or loaded from env."""

    global _credentials
    if _credentials is not None:
        return _credentials

    env_credentials = load_env_credentials()
    if env_credentials is not None:
        _credentials = env_credentials
    return _credentials


def has_credentials() -> bool:
    """Check whether credentials are present."""

    return get_credentials() is not None
