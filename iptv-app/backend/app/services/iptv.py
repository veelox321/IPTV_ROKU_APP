"""Service for fetching IPTV data via Xtream Codes API."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests

from app.models import Channel, CredentialsIn


def _normalize_channel(raw: dict[str, Any], credentials: CredentialsIn) -> Channel:
    stream_id = str(raw.get("stream_id") or raw.get("id") or "")
    name = raw.get("name") or "Unknown"
    group = raw.get("category_name") or raw.get("group") or "Ungrouped"
    stream_url = urljoin(
        credentials.host.rstrip("/") + "/",
        f"live/{credentials.username}/{credentials.password}/{stream_id}.m3u8",
    )
    return Channel(id=stream_id, name=name, group=group, stream_url=stream_url)


def fetch_channels(credentials: CredentialsIn, verify_ssl: bool) -> list[Channel]:
    """Fetch live channels from Xtream Codes API."""

    endpoint = urljoin(
        credentials.host.rstrip("/") + "/",
        "player_api.php",
    )
    params = {
        "username": credentials.username,
        "password": credentials.password,
        "action": "get_live_streams",
    }
    response = requests.get(endpoint, params=params, timeout=30, verify=verify_ssl)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        return []
    return [_normalize_channel(item, credentials) for item in payload]
