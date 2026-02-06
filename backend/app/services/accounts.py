"""Local credentials persistence service (outside Git)."""

from __future__ import annotations

from pathlib import Path
import json
import logging
import threading

from backend.app.models import CredentialsIn

LOGGER = logging.getLogger(__name__)

_LOCK = threading.Lock()


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def _credentials_path() -> Path:
    return _data_dir() / "credentials.json"


def _atomic_write(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    tmp.replace(path)


def save_credentials(credentials: CredentialsIn) -> None:
    """Persist credentials to disk atomically."""
    payload = credentials.model_dump()
    path = _credentials_path()
    with _LOCK:
        _atomic_write(path, payload)
    LOGGER.info("[ACCOUNT] Credentials saved successfully host=%s", credentials.host)


def load_credentials() -> CredentialsIn | None:
    """Load credentials from disk. Returns None if missing or invalid."""
    path = _credentials_path()
    if not path.exists():
        LOGGER.info("[ACCOUNT] No saved credentials found")
        return None

    try:
        with _LOCK, path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        credentials = CredentialsIn.model_validate(payload)
        LOGGER.info("[ACCOUNT] Loaded credentials for host=%s", credentials.host)
        return credentials
    except json.JSONDecodeError:
        LOGGER.warning("[ACCOUNT] Credentials file is corrupted")
        return None
    except Exception:
        LOGGER.exception("[ACCOUNT] Failed to load saved credentials")
        return None


def has_credentials() -> bool:
    """Return True if valid credentials are present on disk."""
    return load_credentials() is not None


def clear_credentials() -> None:
    """Remove credentials from disk if present."""
    path = _credentials_path()
    try:
        with _LOCK:
            if path.exists():
                path.unlink()
        LOGGER.info("[ACCOUNT] Credentials cleared successfully")
    except Exception:
        LOGGER.exception("[ACCOUNT] Failed to clear credentials")
