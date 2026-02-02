"""In-memory credential storage service."""

from typing import Optional
import logging

from app.config import get_settings
from app.models import CredentialsIn

LOGGER = logging.getLogger(__name__)

_credentials: Optional[CredentialsIn] = None


def load_env_credentials() -> Optional[CredentialsIn]:
    """Load credentials from environment if fully configured."""

    settings = get_settings()
    if not settings.iptv_host or not settings.iptv_username or not settings.iptv_password:
        return None

    return CredentialsIn(
        host=settings.iptv_host,
        username=settings.iptv_username,
        password=settings.iptv_password,
    )


def set_credentials(credentials: CredentialsIn) -> None:
    """Persist credentials in memory for this process."""

    global _credentials
    _credentials = credentials
    LOGGER.debug("Credentials updated in memory via /login for host=%s.", credentials.host)


def get_credentials() -> Optional[CredentialsIn]:
    """Return credentials if they have been set or loaded from env."""

    global _credentials
    if _credentials is not None:
        return _credentials

    env_credentials = load_env_credentials()
    if env_credentials is not None:
        _credentials = env_credentials
        LOGGER.debug("Loaded credentials from environment fallback for host=%s.", env_credentials.host)
    return _credentials


def has_credentials() -> bool:
    """Check whether credentials are present."""

    return get_credentials() is not None
