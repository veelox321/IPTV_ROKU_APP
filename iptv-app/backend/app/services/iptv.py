"""
IPTV service
------------
- Fetch channels via Xtream Codes M3U API
- Handle self-signed SSL
- Handle unstable IPTV servers
- Use realistic IPTV headers
- Retry safely
- NEVER crash FastAPI (raise controlled errors)
"""

import logging
import re
from typing import Any, Iterable

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import CredentialsIn

# --------------------------------------------------
# Disable SSL warnings (required for IPTV providers)
# --------------------------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --------------------------------------------------
# IPTV-like HTTP headers (CRITICAL)
# --------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}



# --------------------------------------------------
# Requests session with retry strategy
# --------------------------------------------------
def _build_session() -> requests.Session:
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


_SESSION = _build_session()


LOGGER = logging.getLogger(__name__)

_EXTINF_RE = re.compile(r'#EXTINF:-?\d+\s*(.*)', re.IGNORECASE)
_GROUP_RE = re.compile(r'group-title="([^"]+)"', re.IGNORECASE)


def _normalize_category(group: str, name: str) -> str:
    """Map group/name hints into a normalized category."""

    haystack = f"{group} {name}".lower()
    if any(keyword in haystack for keyword in ("movie", "cinema", "film", "vod")):
        return "movies"
    if any(keyword in haystack for keyword in ("series", "tv show", "shows")):
        return "series"
    if any(keyword in haystack for keyword in ("live", "tv", "news", "sport")):
        return "tv"
    return "other"


def _parse_m3u(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Parse M3U playlist lines into normalized channel dictionaries."""

    channels: list[dict[str, Any]] = []
    current_meta: dict[str, str] = {}
    line_index = 0

    for raw_line in lines:
        line_index += 1
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            match = _EXTINF_RE.match(line)
            metadata = match.group(1) if match else ""
            group_match = _GROUP_RE.search(metadata)
            group = group_match.group(1).strip() if group_match else "Other"
            name = metadata.split(",")[-1].strip() if "," in metadata else ""
            if not name:
                name = f"Unknown Channel {line_index}"
                LOGGER.debug("Missing channel name at line %s.", line_index)
            current_meta = {"name": name, "group": group}
            continue
        if line.startswith("#"):
            continue
        url = line
        if not current_meta:
            name = f"Unknown Channel {line_index}"
            group = "Other"
            LOGGER.warning(
                "Stream URL without EXTINF metadata at line %s; using defaults.",
                line_index,
            )
        else:
            name = current_meta["name"]
            group = current_meta["group"]
        channels.append(
            {
                "name": name,
                "group": group,
                "category": _normalize_category(group, name),
                "url": url,
            }
        )
        current_meta = {}

    if current_meta:
        LOGGER.warning("Dangling EXTINF metadata without URL at end of file.")
    return channels


def fetch_channels(credentials: CredentialsIn, verify_ssl: bool) -> list[dict[str, Any]]:
    """
    Fetch live channels from IPTV provider using Xtream Codes M3U API.

    Args:
        credentials: IPTV credential model
        verify_ssl: bool (False for most IPTV providers)

    Returns:
        List of normalized channel dicts

    Raises:
        RuntimeError: controlled error for FastAPI layer
    """

    host = credentials.host
    username = credentials.username
    password = credentials.password

    if not host or not username or not password:
        raise RuntimeError("Incomplete IPTV credentials")

    params = {
        "username": username,
        "password": password,
        "type": "m3u_plus",
        "output": "ts",
    }
    endpoint = f"{host.rstrip('/')}/get.php"

    try:
        LOGGER.debug("IPTV fetch start: endpoint=%s", endpoint)
        response = _SESSION.get(
            endpoint,
            params=params,
            headers=HEADERS,
            timeout=30,
            verify=verify_ssl,
            allow_redirects=True,
        )
        LOGGER.debug("IPTV response status: %s", response.status_code)


    except requests.exceptions.SSLError:
        raise RuntimeError("SSL verification failed (self-signed certificate)")

    except requests.exceptions.ConnectionError:
        raise RuntimeError("IPTV server closed the connection")

    except requests.exceptions.Timeout:
        raise RuntimeError("IPTV request timed out")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"IPTV request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected IPTV error: {e}")

    if response.status_code != 200:
        raise RuntimeError(
            f"IPTV server returned HTTP {response.status_code}"
        )

    playlist_text = response.text
    if not playlist_text:
        raise RuntimeError("Empty playlist returned by IPTV provider")

    channels = _parse_m3u(playlist_text.splitlines())

    if not channels:
        raise RuntimeError("No channels returned by IPTV provider")

    LOGGER.debug("IPTV channels parsed: count=%s", len(channels))
    return channels
