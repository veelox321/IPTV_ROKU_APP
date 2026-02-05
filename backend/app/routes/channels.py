"""
API routes for IPTV channel operations.

Endpoints:
- POST   /login
- GET    /channels
- POST   /refresh
- GET    /status
- GET    /stats
- GET    /groups
- GET    /health
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import requests

from backend.app.models import (
    ChannelListResponse,
    CredentialsIn,
    StatsResponse,
    StatusResponse,
)
from backend.app.services import auth, cache, iptv
from backend.app.config import get_settings

LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["channels"])


# ============================================================================
# AUTH
# ============================================================================

@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""
    auth.set_credentials(credentials)
    LOGGER.info("Login accepted for host=%s", credentials.host)
    return {"status": "ok"}


# ============================================================================
# CHANNELS
# ============================================================================

@router.get("/channels", response_model=ChannelListResponse)
def get_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    category: str | None = Query(None, min_length=1),
    group: str | None = Query(None, min_length=1),
) -> ChannelListResponse:
    """
    Return paginated channels from cache.

    Filtering is applied BEFORE pagination.
    Streaming-safe: no full list slicing.
    """

    LOGGER.info(
        "Channels request page=%s page_size=%s search=%s category=%s group=%s",
        page,
        page_size,
        search,
        category,
        group,
    )
    cached = cache.load_cache()
    if not cached:
        LOGGER.info("Channels requested but cache is missing")
        return ChannelListResponse(
            channels=[],
            cached=False,
            total=0,
            page=page,
            page_size=page_size,
        )

    channels: Iterable[dict] = cached.get("channels", [])

    search_l = search.lower() if search else None
    category_l = category.lower() if category else None
    group_l = group.lower() if group else None
    if category_l and category_l not in iptv.ALLOWED_CATEGORIES:
        LOGGER.info("Invalid category filter provided: %s", category)
        return ChannelListResponse(
            channels=[],
            cached=True,
            total=0,
            page=page,
            page_size=page_size,
        )

    def matches(ch: dict) -> bool:
        if search_l and search_l not in ch.get("name", "").lower():
            return False
        if category_l and ch.get("category", "other").lower() != category_l:
            return False
        if group_l and group_l not in ch.get("group", "").lower():
            return False
        return True

    offset = (page - 1) * page_size
    items: list[dict] = []
    total = 0

    for ch in channels:
        if not matches(ch):
            continue

        if offset <= total < offset + page_size:
            items.append(ch)

        total += 1

    return ChannelListResponse(
        channels=items,
        cached=True,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# REFRESH (BACKGROUND)
# ============================================================================

def _refresh_job(credentials: CredentialsIn) -> None:
    """Background task: fetch, parse and cache IPTV playlist."""
    started_at = time.monotonic()
    LOGGER.info(
        "Background refresh started pid=%s thread=%s host=%s",
        os.getpid(),
        threading.current_thread().name,
        credentials.host,
    )

    try:
        fetch_started = time.monotonic()
        try:
            playlist = iptv.fetch_m3u(credentials)
        except Exception as exc:
            cache.set_last_error(str(exc))
            LOGGER.exception("Background refresh failed during fetch")
            return
        fetch_elapsed = time.monotonic() - fetch_started
        preview = playlist[:200].replace("\n", "\\n")
        LOGGER.info(
            "Fetch complete bytes=%s elapsed=%.2fs preview=%s",
            len(playlist.encode("utf-8")),
            fetch_elapsed,
            preview,
        )
        LOGGER.info("First 20 lines of playlist:\n%s", "\n".join(playlist.split("\n")[:20]))
        parse_started = time.monotonic()
        try:
            channels = iptv.parse_m3u(playlist)
        except Exception as exc:
            cache.set_last_error(str(exc))
            LOGGER.exception("Background refresh failed during parse")
            return
        parse_elapsed = time.monotonic() - parse_started
        sample = [
            {
                "name": ch.get("name"),
                "category": ch.get("category"),
                "group": ch.get("group"),
            }
            for ch in channels[:3]
        ]
        LOGGER.info(
            "Parse complete channels=%d elapsed=%.2fs sample=%s",
            len(channels),
            parse_elapsed,
            sample,
        )

        save_started = time.monotonic()
        try:
            cache.save_cache(credentials.host, channels)
            cache.set_last_error(None)
        except Exception as exc:
            cache.set_last_error(str(exc))
            LOGGER.exception("Background refresh failed during save")
            return
        save_elapsed = time.monotonic() - save_started
        LOGGER.info("Save complete elapsed=%.2fs", save_elapsed)

    finally:
        cache.set_refreshing(False)
        total_elapsed = time.monotonic() - started_at
        LOGGER.info("Background refresh finished elapsed=%.2fs", total_elapsed)

@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks, request: Request) -> dict[str, str]:
    """Trigger a non-blocking refresh of the channel cache."""

    if not auth.has_credentials():
        LOGGER.info("Refresh requested without login")
        raise HTTPException(409, "not logged in")

    if not cache.try_set_refreshing():
        refresh_started_at = cache.get_refresh_started_at()
        LOGGER.info(
            "Refresh requested while another refresh is in progress client=%s refresh_started_at=%s",
            request.client.host if request.client else "unknown",
            refresh_started_at,
        )
        raise HTTPException(409, "already refreshing")

    credentials = auth.get_credentials()
    if credentials is None:
        cache.set_refreshing(False)
        LOGGER.info("Refresh requested but credentials missing in memory")
        raise HTTPException(409, "not logged in")

    LOGGER.info(
        "Refresh requested client=%s host=%s",
        request.client.host if request.client else "unknown",
        credentials.host,
    )
    background_tasks.add_task(_refresh_job, credentials)
    return {"status": "started"}


# ============================================================================
# STATUS / STATS
# ============================================================================

@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Return backend and cache status."""

    cached = cache.load_cache()
    refresh_metadata = cache.get_refresh_metadata(cached)

    return StatusResponse(
        logged_in=auth.has_credentials(),
        refreshing=cache.is_refreshing(),
        cache_available=cached is not None,
        last_refresh=cached.get("timestamp") if cached else None,
        channel_count=cached.get("channel_count", 0) if cached else 0,
        refresh_status=refresh_metadata["refresh_status"],
        last_error=refresh_metadata["last_error"],
        last_successful_refresh=refresh_metadata["last_successful_refresh"],
    )


def _require_debug() -> None:
    settings = get_settings()
    if not settings.debug:
        raise HTTPException(404, "Not found")


@router.get("/debug/cache")
def debug_cache(request: Request) -> dict:
    _require_debug()
    cache_path = cache.get_cache_path().resolve()
    exists = cache_path.exists()
    size_bytes = cache_path.stat().st_size if exists else None
    mtime = (
        datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc).isoformat()
        if exists
        else None
    )
    preview = None
    keys = None
    if exists:
        try:
            if size_bytes is not None and size_bytes <= 1_000_000:
                with cache_path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                keys = sorted(payload.keys())
            else:
                with cache_path.open("rb") as fh:
                    preview = fh.read(2048).decode("utf-8", errors="replace")
        except Exception:
            LOGGER.exception("Failed to read cache file for debug.")

    cached = cache.load_cache()
    refresh_metadata = cache.get_refresh_metadata(cached)
    summary = {
        "has_cache": cached is not None,
        "channel_count": cached.get("channel_count", 0) if cached else 0,
        "timestamp": cached.get("timestamp") if cached else None,
        "host": cached.get("host") if cached else None,
    }

    return {
        "cache_path": str(cache_path),
        "cache_exists": exists,
        "cache_size_bytes": size_bytes,
        "cache_mtime": mtime,
        "cache_preview": preview,
        "cache_keys": keys,
        "load_cache_summary": summary,
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "python_executable": sys.executable,
        "refreshing": cache.is_refreshing(),
        "refresh_started_at": cache.get_refresh_started_at(),
        "last_refresh_status": refresh_metadata["refresh_status"],
        "last_error": refresh_metadata["last_error"],
        "last_successful_refresh": refresh_metadata["last_successful_refresh"],
        "routes_prefix": request.scope.get("root_path"),
    }


@router.get("/debug/routes")
def debug_routes(request: Request) -> dict:
    _require_debug()
    routes = []
    for route in request.app.router.routes:
        methods = getattr(route, "methods", None)
        routes.append(
            {
                "path": route.path,
                "methods": sorted(methods) if methods else None,
                "name": route.name,
                "endpoint": getattr(route.endpoint, "__module__", None),
            }
        )
    return {"routes": routes}


@router.post("/debug/selftest")
def debug_selftest() -> dict:
    _require_debug()
    credentials = auth.get_credentials()
    if credentials is None:
        raise HTTPException(409, "not logged in")

    url = iptv.build_m3u_url(credentials)
    dns_ok = False
    tcp_ok = False
    http_status = None
    content_length = None
    error = None
    try:
        import socket

        parsed = urlparse(url)
        host = parsed.netloc or parsed.path.split("/")[0]
        socket.getaddrinfo(host, None)
        dns_ok = True
    except Exception as exc:
        error = f"dns_error: {exc}"

    response = None
    try:
        response = requests.get(
            url,
            headers=iptv.HEADERS,
            timeout=(5, 10),
            verify=get_settings().verify_ssl,
            stream=True,
            allow_redirects=True,
        )
        tcp_ok = True
        http_status = response.status_code
        content_length = response.headers.get("Content-Length")
        next(response.iter_content(chunk_size=1024), None)
    except Exception as exc:
        error = f"request_error: {exc}"
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    return {
        "dns_ok": dns_ok,
        "tcp_ok": tcp_ok,
        "http_status": http_status,
        "content_length": content_length,
        "error": error,
        "url_host": credentials.host,
    }


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    """Return aggregated channel statistics."""

    cached = cache.load_cache()
    stats = cache.get_stats(cached)
    if not cached:
        LOGGER.info("Stats requested but cache is missing")
    LOGGER.info("Computed stats: %s", stats)
    counts = stats
    return StatsResponse(
        total=counts["total"],
        tv=counts["tv"],
        movies=counts["movies"],
        series=counts["series"],
        other=counts["other"],
    )


@router.get("/groups")
def groups() -> dict:
    """Return categories and most common group titles."""

    cached = cache.load_cache()
    if not cached:
        LOGGER.info("Groups requested but cache is missing")
        return {"categories": [], "groups": {}}

    return {
        "categories": cached.get("categories", []),
        "groups": cached.get("group_counts", {}),
    }


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok"})
