#!/usr/bin/env python3
"""
Probe IPTV provider header combinations for get_live_streams.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from typing import Any, Dict, List, Optional

import requests


DEFAULT_TIMEOUT_SECONDS = 15


def mask_value(value: Optional[str], show: int = 2) -> str:
    if not value:
        return "***"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}***"


def build_header_sets() -> List[Dict[str, Any]]:
    """Return a list of header configurations to try."""
    chrome_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
    firefox_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) "
        "Gecko/20100101 Firefox/123.0"
    )
    safari_ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
    )

    return [
        {
            "name": "default_requests_headers",
            "headers": None,
        },
        {
            "name": "minimal_accept_json",
            "headers": {
                "Accept": "application/json, text/plain, */*",
            },
        },
        {
            "name": "chrome_like",
            "headers": {
                "User-Agent": chrome_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-CH-UA": '"Chromium";v="123", "Not:A-Brand";v="8"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
            },
        },
        {
            "name": "firefox_like",
            "headers": {
                "User-Agent": firefox_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        },
        {
            "name": "safari_like",
            "headers": {
                "User-Agent": safari_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-us",
                "Connection": "keep-alive",
            },
        },
        {
            "name": "smarters_pro",
            "headers": {
                "User-Agent": "SmartersPro/1.0 (Android)",
                "Accept": "application/json",
                "Connection": "keep-alive",
            },
        },
        {
            "name": "tivimate",
            "headers": {
                "User-Agent": "TiviMate/4.6.1 (Android TV)",
                "Accept": "application/json",
                "Connection": "keep-alive",
            },
        },
        {
            "name": "vlc",
            "headers": {
                "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
                "Accept": "*/*",
                "Connection": "close",
            },
        },
        {
            "name": "android_webview",
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 12; Pixel 5) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Mobile Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": "https://example.com/",
            },
        },
        {
            "name": "referer_only",
            "headers": {
                "User-Agent": chrome_ua,
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://example.com/portal",
            },
        },
        {
            "name": "referrer_header",
            "headers": {
                "User-Agent": chrome_ua,
                "Accept": "application/json, text/plain, */*",
                "Referrer": "https://example.com/portal",
            },
        },
        {
            "name": "no_accept_language",
            "headers": {
                "User-Agent": chrome_ua,
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive",
            },
        },
        {
            "name": "close_connection",
            "headers": {
                "User-Agent": firefox_ua,
                "Accept": "application/json, text/plain, */*",
                "Connection": "close",
            },
        },
    ]


def normalize_base_url(host: str, scheme: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"{scheme}://{host}".rstrip("/")


def run_probe(
    endpoint: str,
    params: Dict[str, str],
    header_sets: List[Dict[str, Any]],
    verify_ssl: bool,
    timeout_seconds: int,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for header_set in header_sets:
        name = header_set["name"]
        headers = header_set["headers"]
        timestamp = dt.datetime.utcnow().isoformat() + "Z"
        attempt: Dict[str, Any] = {
            "timestamp": timestamp,
            "name": name,
            "headers": headers or "<default requests headers>",
            "status_code": None,
            "success": False,
            "error_type": None,
            "error_message": None,
            "elapsed_ms": None,
            "response_text": None,
        }

        start_time = time.monotonic()
        try:
            response = requests.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=timeout_seconds,
                verify=verify_ssl,
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            attempt["status_code"] = response.status_code
            attempt["success"] = response.ok
            attempt["elapsed_ms"] = elapsed_ms
            attempt["response_text"] = response.text
        except requests.exceptions.RequestException as exc:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            attempt["elapsed_ms"] = elapsed_ms
            attempt["error_type"] = type(exc).__name__
            attempt["error_message"] = str(exc)

        results.append(attempt)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe header combinations against IPTV get_live_streams endpoint."
    )
    parser.add_argument("--host", required=True, help="IPTV provider host or base URL")
    parser.add_argument("--username", required=True, help="IPTV username")
    parser.add_argument("--password", required=True, help="IPTV password")
    parser.add_argument(
        "--scheme",
        default="https",
        choices=["http", "https"],
        help="Scheme to use if host is not a full URL",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for each request in seconds",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        default=True,
        help="Enable SSL verification (default)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        dest="verify_ssl",
        action="store_false",
        help="Disable SSL verification",
    )
    parser.add_argument(
        "--output",
        default="iptv_header_probe_results.json",
        help="Output JSON file path",
    )

    args = parser.parse_args()

    base_url = normalize_base_url(args.host, args.scheme)
    endpoint = f"{base_url}/player_api.php"

    params = {
        "username": args.username,
        "password": args.password,
        "action": "get_live_streams",
    }

    header_sets = build_header_sets()

    masked_params = {
        "username": mask_value(args.username),
        "password": mask_value(args.password),
        "action": "get_live_streams",
    }

    results = run_probe(
        endpoint=endpoint,
        params=params,
        header_sets=header_sets,
        verify_ssl=args.verify_ssl,
        timeout_seconds=args.timeout,
    )

    payload = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "params": masked_params,
        "verify_ssl": args.verify_ssl,
        "timeout_seconds": args.timeout,
        "results": results,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    print(f"Wrote results to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())