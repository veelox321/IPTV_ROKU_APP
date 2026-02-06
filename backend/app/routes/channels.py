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
import uuid
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import requests

from backend.app.config import get_settings
from backend.app.models import (
    ChannelListResponse,
    ContentRowsResponse,
    CredentialsIn,
    StatsResponse,
    StatusResponse,
)
from backend.app.services import accounts, auth, cache, iptv
from backend.app.services import roku_content

LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["channels"])


# ============================================================================
# AUTH
# ============================================================================

@router.post("/login")
def login(credentials: CredentialsIn) -> dict[str, str]:
    """Store IPTV credentials in memory."""
    auth.set_credentials(credentials)
    try:
        accounts.save_credentials(credentials)
    except Exception:
        LOGGER.exception("[ACCOUNT] Failed to persist credentials from /login")
    LOGGER.info("Login accepted for host=%s", credentials.host)
    return {"status": "ok"}


@router.post("/account")
def save_account(credentials: CredentialsIn) -> dict[str, str]:
    """Persist IPTV credentials and activate them immediately."""
    try:
        accounts.save_credentials(credentials)
    except Exception:
        LOGGER.exception("[ACCOUNT] Failed to save credentials")
        raise HTTPException(500, "failed to save credentials")
    auth.set_credentials(credentials)
    LOGGER.info("[ACCOUNT] Active account set host=%s", credentials.host)
    return {"status": "ok"}


@router.get("/account")
def get_account() -> dict[str, str | bool | None]:
    """Return account status and configured host (without password)."""
    active = auth.get_credentials()
    stored = accounts.load_credentials()
    host = (active or stored).host if (active or stored) else None
    return {
        "connected": active is not None,
        "host": host,
    }


@router.delete("/account")
def delete_account() -> dict[str, str]:
    """Clear persisted credentials and disconnect."""
    accounts.clear_credentials()
    auth.clear_credentials()
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

def _refresh_job(credentials: CredentialsIn, request_id: str) -> None:
    """Background task: fetch, parse and cache IPTV playlist."""
    LOGGER.info(
        "[REFRESH] Background refresh started request_id=%s host=%s",
        request_id,
        credentials.host,
    )

    stop_heartbeat = threading.Event()
    def heartbeat_loop() -> None:
        while not stop_heartbeat.is_set():
            cache.set_refresh_heartbeat_at()
            stop_heartbeat.wait(5)

    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    try:
        cache.set_refresh_heartbeat_at()
        LOGGER.info(
            "[REFRESH] Using stored credentials request_id=%s host=%s",
            request_id,
            credentials.host,
        )
        playlist = iptv.fetch_m3u(credentials, request_id=request_id)
        cache.set_refresh_heartbeat_at()
        channels = iptv.parse_m3u(playlist, request_id=request_id)
        cache.set_refresh_heartbeat_at()

        LOGGER.info(
            "[REFRESH] Parsed %d channels request_id=%s",
            len(channels),
            request_id,
        )
        cache.save_cache(credentials.host, channels)
        cache.set_refresh_heartbeat_at()
        cache.set_last_error(None)

    except Exception as exc:
        cache.set_last_error(str(exc))
        LOGGER.exception(
            "[REFRESH] Background refresh failed request_id=%s",
            request_id,
        )

    finally:
        stop_heartbeat.set()
        cache.set_refreshing(False)
        LOGGER.info(
            "[REFRESH] Background refresh finished request_id=%s",
            request_id,
        )


@router.post("/refresh")
def refresh_channels(background_tasks: BackgroundTasks, request: Request) -> dict[str, str | bool | None]:
    """Trigger a non-blocking refresh of the channel cache."""

    client_host = request.client.host if request.client else "unknown"
    LOGGER.info("[REFRESH] Refresh requested client=%s", client_host)

    if not auth.has_credentials():
        LOGGER.info("[REFRESH] Refresh requested without active account")
        raise HTTPException(409, "not logged in")

    if not cache.try_set_refreshing():
        LOGGER.info("[REFRESH] Refresh requested while another refresh is in progress")
        return {
            "status": "already_refreshing",
            "refreshing": True,
            "refresh_started_at": cache.get_refresh_started_at(),
            "refresh_heartbeat_at": cache.get_refresh_heartbeat_at(),
        }

    credentials = auth.get_credentials()
    if credentials is None:
        cache.set_refreshing(False)
        LOGGER.info("[REFRESH] Refresh requested but credentials missing in memory")
        raise HTTPException(409, "not logged in")

    request_id = str(uuid.uuid4())
    LOGGER.info(
        "[REFRESH] Using stored credentials request_id=%s host=%s timeout=20s",
        request_id,
        credentials.host,
    )
    background_tasks.add_task(_refresh_job, credentials, request_id)
    return {
        "status": "started",
        "refreshing": True,
        "refresh_started_at": cache.get_refresh_started_at(),
        "refresh_heartbeat_at": cache.get_refresh_heartbeat_at(),
    }


# ============================================================================
# STATUS / STATS
# ============================================================================

@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Return backend and cache status."""

    cached = cache.load_cache()
    refresh_metadata = cache.get_refresh_metadata(cached)
    refresh_started_at = cache.get_refresh_started_at()
    refresh_heartbeat_at = cache.get_refresh_heartbeat_at()
    refresh_elapsed_seconds = None
    refresh_heartbeat_age_seconds = None
    refresh_state = "idle"

    if refresh_started_at:
        try:
            started = datetime.fromisoformat(refresh_started_at)
            now = datetime.now(timezone.utc)
            refresh_elapsed_seconds = max(0, int((now - started).total_seconds()))
        except Exception:
            refresh_elapsed_seconds = None
    if refresh_heartbeat_at:
        try:
            heartbeat = datetime.fromisoformat(refresh_heartbeat_at)
            now = datetime.now(timezone.utc)
            refresh_heartbeat_age_seconds = max(0, int((now - heartbeat).total_seconds()))
        except Exception:
            refresh_heartbeat_age_seconds = None

    if refresh_metadata["refresh_status"] == "failed":
        refresh_state = "failed"
    elif cache.is_refreshing():
        if refresh_heartbeat_age_seconds is not None and refresh_heartbeat_age_seconds > 15:
            refresh_state = "stuck"
        elif refresh_elapsed_seconds is None or refresh_elapsed_seconds < 2:
            refresh_state = "pending"
        else:
            refresh_state = "alive"
    else:
        refresh_state = "idle"

    return StatusResponse(
        logged_in=auth.has_credentials(),
        refreshing=cache.is_refreshing(),
        cache_available=cached is not None,
        last_refresh=cached.get("timestamp") if cached else None,
        channel_count=cached.get("channel_count", 0) if cached else 0,
        refresh_started_at=refresh_started_at,
        refresh_elapsed_seconds=refresh_elapsed_seconds,
        refresh_heartbeat_at=refresh_heartbeat_at,
        refresh_heartbeat_age_seconds=refresh_heartbeat_age_seconds,
        refresh_state=refresh_state,
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
# ROKU UI
# ============================================================================


@router.get("/roku/content", response_model=ContentRowsResponse)
def roku_content_rows(category: str = Query("tv", min_length=1)) -> ContentRowsResponse:
    """Return Roku-ready content rows for a given category."""

    cached = cache.load_cache()
    channels = cached.get("channels", []) if cached else []
    rows = roku_content.build_rows(channels, category)
    return ContentRowsResponse(
        category=iptv.coerce_category(category, ""),
        rows=rows,
        total_rows=len(rows),
    )


@router.get("/roku/status")
def roku_status() -> dict:
    """Return status metrics for Roku Status tab."""

    cached = cache.load_cache()
    refresh_metadata = cache.get_refresh_metadata(cached)
    return roku_content.build_status_payload(
        cached,
        refresh_metadata=refresh_metadata,
        refreshing=cache.is_refreshing(),
        refresh_started_at=cache.get_refresh_started_at(),
    )


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok"})
