"""Shared Streamlit helpers for the IPTV admin UI."""

from __future__ import annotations

import json
from typing import Any

import requests

DEFAULT_API_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 30


def _extract_error(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if detail:
                return str(detail)
        return json.dumps(payload)
    except json.JSONDecodeError:
        return response.text or f"HTTP {response.status_code}"


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
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if not response.ok:
            return None, _extract_error(response)
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Network error: {exc}"
    except json.JSONDecodeError:
        return None, "Server returned invalid JSON."
