"""In-memory credential storage service."""

from typing import Optional

from app.models import CredentialsIn


_credentials: Optional[CredentialsIn] = None


def set_credentials(credentials: CredentialsIn) -> None:
    """Persist credentials in memory for this process."""

    global _credentials
    _credentials = credentials


def get_credentials() -> Optional[CredentialsIn]:
    """Return credentials if they have been set."""

    return _credentials


def has_credentials() -> bool:
    """Check whether credentials are present."""

    return _credentials is not None
