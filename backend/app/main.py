"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request

from backend.app.config import get_settings
from backend.app.routes.channels import router as channels_router
from backend.app.services import auth
from backend.app.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure logging and load credentials from environment if provided."""

    settings = get_settings()
    configure_logging(settings.debug)
    LOGGER.debug("Application startup.")
    if auth.load_env_credentials() is not None:
        LOGGER.debug("Environment credentials detected and available.")
    yield


app = FastAPI(title="IPTV Backend", version="0.1.0", lifespan=lifespan)

app.include_router(channels_router)


@app.middleware("http")
async def log_routes(request: Request, call_next):
    """Log route entry/exit when debug is enabled."""

    settings = get_settings()
    if not settings.debug:
        return await call_next(request)

    LOGGER.debug("Route entry: %s %s", request.method, request.url.path)
    start_time = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start_time) * 1000
    LOGGER.debug(
        "Route exit: %s %s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
