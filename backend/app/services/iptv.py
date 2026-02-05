"""IPTV service for fetching and parsing M3U playlists."""

from __future__ import annotations

from typing import Any, Iterable
import logging
import re
from urllib.parse import urlparse

import requests
import urllib3

from backend.app.config import get_settings
from backend.app.models import CredentialsIn

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "IPTVSmartersPro",
    "Connection": "close",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
}

DEFAULT_FILTER_KEYWORDS = ["ufc", "paramount"]
ATTR_RE = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')

ALLOWED_CATEGORIES = {"tv", "movies", "series", "other"}

CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    (
        "movies",
        (
            "movie",
            "movies",
            "vod",
            "film",
            "cinema",
        ),
    ),
    (
        "series",
        (
            "series",
            "shows",
            "show",
            "season",
            "episode",
        ),
    ),
    (
        "tv",
        (
            "live",
            "tv",
            "sports",
            "sport",
            "news",
            "kids",
            "music",
            "entertainment",
        ),
    ),
]



def _normalize_host(host: str) -> str:
    parsed = urlparse(host)
    if parsed.scheme:
        netloc = parsed.netloc or parsed.path
    else:
        netloc = host
    return netloc.strip().strip("/")


def build_m3u_url(credentials: CredentialsIn) -> str:
    """Build the M3U playlist URL from credentials."""

    host = _normalize_host(credentials.host)
    return f"http://{host}/playlist/{credentials.username}/{credentials.password}/m3u"


def fetch_m3u(credentials: CredentialsIn) -> str:
    """Fetch the M3U playlist for provided credentials."""

    if not credentials.host or not credentials.username or not credentials.password:
        raise RuntimeError("Incomplete IPTV credentials")

    settings = get_settings()
    url = build_m3u_url(credentials)
    LOGGER.debug("M3U download start: url=%s", url)
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            verify=settings.verify_ssl,
            allow_redirects=True,
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



def _safe_text(value: str | None, fallback: str) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else fallback


def _parse_extinf_line(line: str) -> tuple[dict[str, str], str]:
    """Parse an EXTINF line into attributes and display name."""

    header, _, name_part = line.partition(",")
    attrs = {match.group(1): match.group(2) for match in ATTR_RE.finditer(header)}

    name = _safe_text(name_part, "")
    if not name:
        name = _safe_text(attrs.get("tvg-name"), "")
    if not name:
        name = _safe_text(attrs.get("tvg-id"), "Unknown")
    return attrs, name



def _derive_group(attrs: dict[str, str]) -> str:
    """Derive a raw group-title string from EXTINF attributes."""

    for key in ("group-title", "group", "category", "type", "tvg-group"):
        value = attrs.get(key)
        if value and value.strip():
            return value.strip()
    return "Unknown"



def normalize_category(group: str) -> str:
    """Normalize a channel category based on its group title."""

    normalized = (group or "").strip().lower()
    if not normalized:
        return "other"

    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return category
    return "other"


def coerce_category(category: str | None, group: str | None = None) -> str:
    """Ensure a category matches allowed values, falling back to group parsing."""

    normalized = (category or "").strip().lower()
    if normalized in ALLOWED_CATEGORIES:
        return normalized
    return normalize_category(group or normalized)



def parse_m3u(playlist_text: str) -> list[dict]:
    """Parse the M3U playlist into a list of normalized channel dictionaries."""

    channels: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None

    for raw_line in playlist_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            try:
                attrs, display_name = _parse_extinf_line(line)
            except Exception:
                LOGGER.debug("Skipping malformed EXTINF line: %s", line)
                pending = None
                continue

            group = _derive_group(attrs)
            pending = {
                "name": _safe_text(display_name, "Unknown"),
                "group": group,
                "category": normalize_category(group),
            }

            tvg_id = _safe_text(attrs.get("tvg-id"), "")
            tvg_name = _safe_text(attrs.get("tvg-name"), "")
            tvg_logo = _safe_text(attrs.get("tvg-logo"), "")
            tvg_chno = _safe_text(attrs.get("tvg-chno"), "")

            if tvg_id:
                pending["tvg_id"] = tvg_id
            if tvg_name:
                pending["tvg_name"] = tvg_name
            if tvg_logo:
                pending["tvg_logo"] = tvg_logo
            if tvg_chno:
                pending["tvg_chno"] = tvg_chno
            continue

        if line.startswith("#"):
            continue

        url = _safe_text(line, "about:blank")
        if pending:
            pending["url"] = url
            channels.append(pending)
            pending = None
        else:
            channels.append(
                {
                    "name": "Unknown",
                    "group": "Unknown",
                    "category": "other",
                    "url": url,
                }
            )

    if pending:
        pending["url"] = _safe_text(pending.get("url"), "about:blank")
        channels.append(pending)

    return channels



def filter_channels(
    channels: Iterable[dict[str, Any]], keywords: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    """Filter channels by keyword match in their names."""

    if not keywords:
        return list(channels)
    lowered = [keyword.lower() for keyword in keywords]
    filtered = [
        channel
        for channel in channels
        if any(keyword in channel.get("name", "").lower() for keyword in lowered)
    ]
    LOGGER.debug("Filtered channels count=%s keywords=%s", len(filtered), lowered)
    return filtered



def count_categories(channels: list[dict]) -> dict[str, int]:
    """Count channels by normalized category."""

    counts = {"tv": 0, "movies": 0, "series": 0, "other": 0}

    for ch in channels:
        category = ch.get("category")
        if category in counts:
            counts[category] += 1
            continue

        group = str(ch.get("group", "")).lower()
        normalized = normalize_category(group)
        counts[normalized] += 1

    return counts
