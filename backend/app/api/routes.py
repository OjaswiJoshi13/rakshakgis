"""API v1 base router registration."""

from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

# Authentication & authorization endpoints
api_router.include_router(auth_router, prefix="/auth")


@api_router.get("", tags=["System"])
def api_v1_root() -> dict:
    """API v1 status endpoint."""
    return {
        "status": "online",
        "api_version": "v1",
        "app": settings.PROJECT_NAME,
    }
