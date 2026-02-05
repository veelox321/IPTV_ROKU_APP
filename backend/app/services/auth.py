"""In-memory credential storage service."""

from typing import Optional
import logging

from backend.app.models import CredentialsIn

LOGGER = logging.getLogger(__name__)

_credentials: Optional[CredentialsIn] = None


def set_credentials(credentials: CredentialsIn) -> None:
    """Persist credentials in memory for this process."""

    global _credentials
    _credentials = credentials
    LOGGER.debug(
        "Credentials updated in memory via /login for host=%s.",
        credentials.host,
    )


def get_credentials() -> Optional[CredentialsIn]:
    """Return credentials if they have been set."""

    return _credentials


def has_credentials() -> bool:
    """Check whether credentials are present."""

    return get_credentials() is not None
