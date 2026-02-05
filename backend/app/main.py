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
from backend.app.services import auth
from backend.app.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configure logging and load credentials from environment if provided.
    """

    settings = get_settings()
    configure_logging(settings.debug)

    LOGGER.info("Application startup")

    try:
        creds = auth.load_env_credentials()
        if creds is not None:
            LOGGER.info("Environment credentials loaded")
    except Exception:
        LOGGER.exception("Failed to load environment credentials")

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
# CORS (OBLIGATOIRE pour Streamlit / UI / navigateur)
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # dev only
    allow_credentials=True,
    allow_methods=["*"],          # inclut OPTIONS
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

app.include_router(channels_router)

# -----------------------------------------------------------------------------
# Middleware de logging HTTP (debug only)
# -----------------------------------------------------------------------------

@app.middleware("http")
async def log_routes(request: Request, call_next):
    """
    Log route entry/exit when debug is enabled.
    """

    settings = get_settings()
    if not settings.debug:
        return await call_next(request)

    LOGGER.debug("→ %s %s", request.method, request.url.path)
    start_time = time.monotonic()

    response = await call_next(request)

    duration_ms = (time.monotonic() - start_time) * 1000
    LOGGER.debug(
        "← %s %s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# -----------------------------------------------------------------------------
# Health check (utile pour debug, Docker, Roku, etc.)
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}
