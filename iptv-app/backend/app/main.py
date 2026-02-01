"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.config import get_settings
from app.models import CredentialsIn
from app.routes.channels import router as channels_router
from app.services import auth

app = FastAPI(title="IPTV Backend", version="0.1.0")


@app.on_event("startup")
def load_env_credentials() -> None:
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


app.include_router(channels_router)
