"""In-memory credential storage service."""

from pathlib import Path
from typing import Optional
import logging
import json

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


<<<<<<< HEAD
def load_credentials_from_file(path: Path) -> bool:
    """Load credentials from a JSON file and persist them in memory."""

    if not path.exists():
        LOGGER.debug("Credential file not found at %s", path)
        return False

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        credentials = CredentialsIn(**payload)
    except Exception as exc:
        LOGGER.warning("Failed to load credentials from %s: %s", path, exc)
        return False

    set_credentials(credentials)
    LOGGER.info("Loaded credentials from file for host=%s", credentials.host)
    return True
=======
def clear_credentials() -> None:
    """Clear in-memory credentials."""
    global _credentials
    _credentials = None
    LOGGER.info("Credentials cleared from memory")
>>>>>>> 9191c0ca97134ea448c01292342bb83e8295426b
