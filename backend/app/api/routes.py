"""API v1 base router registration."""

from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()


@api_router.get("", tags=["System"])
def api_v1_root() -> dict:
    """API v1 status endpoint."""
    return {
        "status": "online",
        "api_version": "v1",
        "app": settings.PROJECT_NAME,
    }
