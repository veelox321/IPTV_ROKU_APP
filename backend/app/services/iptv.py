"""IPTV service for fetching and parsing M3U playlists."""

from __future__ import annotations

from typing import Any, Iterable
import logging
import re
import time
from urllib.parse import urlparse

import requests
import urllib3
from requests.adapters import HTTPAdapter

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

class IPTVFetchError(RuntimeError):
    """Raised when IPTV playlist fetch fails after retries."""


class _FetchFailure(RuntimeError):
    """Internal helper for fetch failures."""



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


def fetch_m3u(credentials: CredentialsIn, request_id: str | None = None) -> str:
    """Fetch the M3U playlist for provided credentials."""

    if not credentials.host or not credentials.username or not credentials.password:
        raise RuntimeError("Incomplete IPTV credentials")

    settings = get_settings()
    url = build_m3u_url(credentials)
    LOGGER.info("[REFRESH] M3U download start request_id=%s url=%s", request_id, url)

    session = requests.Session()
    adapter = HTTPAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    attempts = 3
    last_exc: Exception | None = None
    last_reason: str | None = None

    try:
        for attempt in range(1, attempts + 1):
            start = time.monotonic()
            try:
                response = session.get(
                    url,
                    headers=HEADERS,
                    timeout=(10, 90),
                    verify=settings.verify_ssl,
                    allow_redirects=True,
                )
                elapsed = time.monotonic() - start
                LOGGER.info(
                    "[REFRESH] attempt %s/%s response status=%s elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    response.status_code,
                    elapsed,
                    request_id,
                )
                if response.status_code != 200:
                    raise _FetchFailure(f"HTTP {response.status_code}")

                playlist_text = response.text or ""
                LOGGER.info(
                    "[REFRESH] M3U download complete: bytes=%s elapsed=%.2fs request_id=%s",
                    len(playlist_text.encode("utf-8")),
                    elapsed,
                    request_id,
                )
                if not playlist_text.strip():
                    raise _FetchFailure("empty playlist")
                return playlist_text
            except requests.exceptions.SSLError as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = "ssl_error"
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: ssl_error elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    elapsed,
                    request_id,
                )
            except requests.exceptions.Timeout as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = "timeout"
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: timeout elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    elapsed,
                    request_id,
                )
            except requests.exceptions.ConnectionError as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = "connection_error"
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: connection_error elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    elapsed,
                    request_id,
                )
            except _FetchFailure as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = str(exc)
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: %s elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    exc,
                    elapsed,
                    request_id,
                )
            except requests.exceptions.RequestException as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = "request_error"
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: request_error elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    elapsed,
                    request_id,
                )
            except Exception as exc:
                elapsed = time.monotonic() - start
                last_exc = exc
                last_reason = "unexpected_error"
                LOGGER.warning(
                    "[REFRESH] attempt %s/%s failed: unexpected_error elapsed=%.2fs request_id=%s",
                    attempt,
                    attempts,
                    elapsed,
                    request_id,
                )

            if attempt < attempts:
                backoff = 2 ** (attempt - 1)
                time.sleep(backoff)
    finally:
        session.close()

    if last_reason == "ssl_error":
        message = "SSL verification failed (self-signed certificate)"
    elif last_reason == "timeout":
        message = "IPTV request timed out"
    elif last_reason == "connection_error":
        message = "IPTV server closed the connection"
    elif last_reason:
        message = f"IPTV request failed: {last_reason}"
    else:
        message = "Failed to fetch IPTV playlist after retries"

    raise IPTVFetchError(message) from last_exc



def _safe_text(value: str | None, fallback: str) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else fallback


EXTINF_LOG_LIMIT = 10
PARSE_SAMPLE_LIMIT = 5
KNOWN_ATTR_KEYS = {
    "tvg-id",
    "tvg-name",
    "tvg-logo",
    "tvg-chno",
    "group-title",
    "group",
    "category",
    "type",
    "tvg-group",
}

def _parse_extinf_line(line: str) -> tuple[dict[str, str], str]:
    """
    Parse an EXTINF line into (attrs, display_name).

    Example:
    #EXTINF:-1 tvg-id="x" group-title="News",CNN
    """

    if not line.startswith("#EXTINF"):
        raise ValueError("Not an EXTINF line")

    # Split metadata and display name
    try:
        meta, display_name = line.split(",", 1)
    except ValueError:
        raise ValueError("EXTINF line missing display name")

    # Remove "#EXTINF:-1"
    meta = meta.replace("#EXTINF:", "", 1)
    meta = meta.replace("-1", "", 1).strip()

    attrs: dict[str, str] = {}
    for key, value in ATTR_RE.findall(meta):
        attrs[key] = value.strip()

    return attrs, display_name.strip()




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



def parse_m3u(playlist_text: str, request_id: str | None = None) -> list[dict]:
    """Parse the M3U playlist into a list of normalized channel dictionaries."""

    channels: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    extinf_logged = 0

    for raw_line in playlist_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            try:
                attrs, display_name = _parse_extinf_line(line)
            except Exception as exc:
                LOGGER.warning(
                    "[PARSE] Skipping malformed EXTINF line request_id=%s error=%s line=%s",
                    request_id,
                    exc,
                    line,
                )
                pending = None
                continue

            if extinf_logged < EXTINF_LOG_LIMIT:
                LOGGER.info(
                    "[PARSE] EXTINF raw request_id=%s line=%s",
                    request_id,
                    line,
                )
                LOGGER.info(
                    "[PARSE] EXTINF attrs request_id=%s attrs=%s display_name=%s",
                    request_id,
                    attrs,
                    display_name,
                )
                extinf_logged += 1

            group = _derive_group(attrs)
            pending = {
                "name": _safe_text(display_name, "Unknown"),
                "group": group,
                "category": normalize_category(group),
            }
            if extinf_logged <= EXTINF_LOG_LIMIT:
                LOGGER.info(
                    "[PARSE] group decision request_id=%s group=%s category=%s name=%s",
                    request_id,
                    group,
                    pending["category"],
                    display_name,
                )
            unknown_keys = sorted(set(attrs) - KNOWN_ATTR_KEYS)
            if unknown_keys:
                LOGGER.debug(
                    "[PARSE] Unknown EXTINF attrs request_id=%s keys=%s",
                    request_id,
                    unknown_keys,
                )
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

    if channels:
        sample = channels[:PARSE_SAMPLE_LIMIT]
        LOGGER.info(
            "[PARSE] Sample channels request_id=%s sample=%s",
            request_id,
            sample,
        )
        group_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        for ch in channels:
            group = str(ch.get("group") or "Unknown").strip() or "Unknown"
            group_counts[group] = group_counts.get(group, 0) + 1
            category = str(ch.get("category") or "other").strip().lower() or "other"
            category_counts[category] = category_counts.get(category, 0) + 1
        LOGGER.info(
            "[PARSE] Group distribution request_id=%s groups=%s",
            request_id,
            dict(sorted(group_counts.items(), key=lambda item: item[1], reverse=True)[:10]),
        )
        LOGGER.info(
            "[PARSE] Category distribution request_id=%s categories=%s",
            request_id,
            category_counts,
        )
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
