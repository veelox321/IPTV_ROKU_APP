"""IPTV service for fetching and parsing M3U playlists."""

from __future__ import annotations

from typing import Any, Iterable
import logging
import re
from urllib.parse import urlparse

import requests
import urllib3

from app.models import CredentialsIn

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "IPTVSmartersPro",
    "Connection": "close",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
}

DEFAULT_FILTER_KEYWORDS = ["ufc", "paramount"]
EXTINF_RE = re.compile(r"#EXTINF:-?\d*(?:\s+.*)?,(.*)$")


def _normalize_host(host: str) -> str:
    parsed = urlparse(host)
    if parsed.scheme:
        netloc = parsed.netloc or parsed.path
    else:
        netloc = host
    return netloc.strip().strip("/")


def build_m3u_url(credentials: CredentialsIn) -> str:
    host = _normalize_host(credentials.host)
    return f"http://{host}/playlist/{credentials.username}/{credentials.password}/m3u"


def fetch_m3u(credentials: CredentialsIn) -> str:
    if not credentials.host or not credentials.username or not credentials.password:
        raise RuntimeError("Incomplete IPTV credentials")

    url = build_m3u_url(credentials)
    LOGGER.debug("M3U download start: url=%s", url)
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            verify=False,
            allow_redirects=True,
            trust_env=False,
        )
    except requests.exceptions.SSLError as exc:
        LOGGER.exception("SSL error during M3U download.")
        raise RuntimeError("SSL verification failed (self-signed certificate)") from exc
    except requests.exceptions.ConnectionError as exc:
        LOGGER.exception("Connection error during M3U download.")
        raise RuntimeError("IPTV server closed the connection") from exc
    except requests.exceptions.Timeout as exc:
        LOGGER.exception("Timeout during M3U download.")
        raise RuntimeError("IPTV request timed out") from exc
    except requests.exceptions.RequestException as exc:
        LOGGER.exception("Request error during M3U download.")
        raise RuntimeError(f"IPTV request failed: {exc}") from exc
    except Exception as exc:
        LOGGER.exception("Unexpected IPTV error during M3U download.")
        raise RuntimeError(f"Unexpected IPTV error: {exc}") from exc

    LOGGER.debug("M3U response status: %s", response.status_code)
    if response.status_code != 200:
        raise RuntimeError(f"IPTV server returned HTTP {response.status_code}")

    playlist_text = response.text or ""
    LOGGER.debug("M3U download complete: bytes=%s", len(playlist_text.encode("utf-8")))
    if not playlist_text.strip():
        raise RuntimeError("Empty M3U playlist received from IPTV provider")
    return playlist_text


def parse_m3u(playlist_text: str) -> list[dict[str, Any]]:
    channels: list[dict[str, Any]] = []
    pending_name: str | None = None

    for line in playlist_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#EXTINF"):
            match = EXTINF_RE.match(stripped)
            pending_name = match.group(1).strip() if match else None
            continue
        if stripped.startswith("#"):
            continue
        if pending_name:
            channels.append({"name": pending_name, "url": stripped})
            pending_name = None

    LOGGER.debug("Parsed M3U channels count=%s", len(channels))
    return channels


def filter_channels(
    channels: Iterable[dict[str, Any]], keywords: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    if not keywords:
        keywords = DEFAULT_FILTER_KEYWORDS
    lowered = [keyword.lower() for keyword in keywords]
    filtered = [
        channel
        for channel in channels
        if any(keyword in channel.get("name", "").lower() for keyword in lowered)
    ]
    LOGGER.debug("Filtered channels count=%s keywords=%s", len(filtered), lowered)
    return filtered
