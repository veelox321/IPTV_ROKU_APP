"""
IPTV service
------------
- Fetch channels via Xtream Codes API
- Handle self-signed SSL
- Handle unstable IPTV servers
- Use realistic IPTV headers
- Retry safely
- NEVER crash FastAPI (raise controlled errors)
"""

from typing import Dict, List
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


# --------------------------------------------------
# Public API
# --------------------------------------------------
def fetch_channels(credentials: Dict[str, str], verify_ssl: bool) -> List[Dict]:
    """
    Fetch live channels from IPTV provider using Xtream Codes API.

    Args:
        credentials: dict with keys {host, username, password}
        verify_ssl: bool (False for most IPTV providers)

    Returns:
        List of normalized channel dicts

    Raises:
        RuntimeError: controlled error for FastAPI layer
    """

    if not credentials:
        raise RuntimeError("No IPTV credentials provided")

    host = credentials.host
    username = credentials.username
    password = credentials.password

    if not host or not username or not password:
        raise RuntimeError("Incomplete IPTV credentials")

    endpoint = f"{host.rstrip('/')}/player_api.php"

    params = {
        "username": username,
        "password": password,
        "action": "get_live_categories",
    }

    try:
        response = _SESSION.get(
            endpoint,
            params=params,
            headers=HEADERS,
            timeout=30,
            verify=verify_ssl,   # False
            allow_redirects=True,
        )


    except requests.exceptions.SSLError:
        raise RuntimeError("SSL verification failed (self-signed certificate)")

    except requests.exceptions.ConnectionError:
        raise RuntimeError("IPTV server closed the connection")

    except requests.exceptions.Timeout:
        raise RuntimeError("IPTV request timed out")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"IPTV request failed: {e}")

    if response.status_code != 200:
        raise RuntimeError(
            f"IPTV server returned HTTP {response.status_code}"
        )

    try:
        raw_channels = response.json()
    except ValueError:
        raise RuntimeError("Invalid JSON received from IPTV server")

    if not isinstance(raw_channels, list):
        raise RuntimeError("Unexpected IPTV response format")

    # --------------------------------------------------
    # Normalize channels
    # --------------------------------------------------
    channels: List[Dict] = []

    for ch in raw_channels:
        try:
            stream_id = ch.get("stream_id")
            name = ch.get("name", "").strip()
            group = ch.get("category_name", "Unknown")

            if not stream_id or not name:
                continue

            stream_url = (
                f"{host.rstrip('/')}/live/"
                f"{username}/{password}/{stream_id}.ts"
            )

            channels.append(
                {
                    "id": stream_id,
                    "name": name,
                    "group": group,
                    "url": stream_url,
                }
            )

        except Exception:
            # Never fail on single malformed channel
            continue

    if not channels:
        raise RuntimeError("No channels returned by IPTV provider")

    return channels
