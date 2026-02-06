"""
FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.routes.channels import router as channels_router
from backend.app.services import accounts, auth
from backend.app.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure logging and log registered routes."""

    settings = get_settings()
    configure_logging(settings.debug)
    LOGGER.debug("Application startup.")
    LOGGER.info(
        "Config summary debug=%s cache_dir=%s cache_ttl_seconds=%s verify_ssl=%s credentials_file=%s",
        settings.debug,
        settings.cache_dir,
        settings.cache_ttl_seconds,
        settings.verify_ssl,
        settings.credentials_file,
    )
    try:
        credentials = accounts.load_credentials()
        if credentials:
            auth.set_credentials(credentials)
            LOGGER.info(
                "[ACCOUNT] Auto-login successful host=%s",
                credentials.host,
            )
    except Exception:
        LOGGER.exception("[ACCOUNT] Error while loading saved credentials")
    for route in app.router.routes:
        methods = getattr(route, "methods", None)
        methods_str = ",".join(sorted(methods)) if methods else "N/A"
        endpoint = getattr(route.endpoint, "__module__", None)
        LOGGER.info(
            "Registered route: %s %s name=%s endpoint=%s",
            methods_str,
            route.path,
            route.name,
            endpoint,
        )
    yield

    LOGGER.info("Application shutdown")


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(
    title="IPTV Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS (required for UI / browser)
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],  # includes OPTIONS
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels_router)

# -----------------------------------------------------------------------------
# HTTP logging middleware (debug only)
# -----------------------------------------------------------------------------

@app.middleware("http")
async def log_routes(request: Request, call_next):
    """
    Log route entry/exit when debug is enabled.
    """

    settings = get_settings()
    if not settings.debug:
        return await call_next(request)

    LOGGER.debug("-> %s %s", request.method, request.url.path)
    start_time = time.monotonic()

    response = await call_next(request)

    duration_ms = (time.monotonic() - start_time) * 1000
    LOGGER.debug(
        "<- %s %s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# -----------------------------------------------------------------------------
# Health check (useful for debug, Docker, Roku, etc.)
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}
