"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.models import CredentialsIn
from app.routes.channels import router as channels_router
from app.services import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load credentials from environment if provided."""

    settings = get_settings()
    if settings.iptv_host and settings.iptv_username and settings.iptv_password:
        auth.set_credentials(
            CredentialsIn(
                host=settings.iptv_host,
                username=settings.iptv_username,
                password=settings.iptv_password,
            )
        )
    yield

app = FastAPI(title="IPTV Backend", version="0.1.0", lifespan=lifespan)

app.include_router(channels_router)
