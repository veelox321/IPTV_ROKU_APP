"""Shared Streamlit helpers for the IPTV admin UI."""

from __future__ import annotations

import json
from typing import Any

import requests

DEFAULT_API_URL = "http://localhost:8000"


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Send a JSON request and return parsed payload or an error message."""

    try:
        response = requests.request(
            method,
            url,
            json=payload,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Network error: {exc}"
    except json.JSONDecodeError:
        return None, "Server returned invalid JSON."
