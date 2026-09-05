"""API v1 base router registration."""

from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.sites import sites_router
from app.api.v1.telemetry import telemetry_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

# Authentication & authorization endpoints
api_router.include_router(auth_router, prefix="/auth")

# Candidate Relocation Sites endpoints
api_router.include_router(sites_router, prefix="/sites", tags=["Candidate Relocation Sites"])

# Data Source Freshness & Telemetry endpoints
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["Data Source Telemetry"])


@api_router.get("", tags=["System"])
def api_v1_root() -> dict:
    """API v1 status endpoint."""
    return {
        "status": "online",
        "api_version": "v1",
        "app": settings.PROJECT_NAME,
    }

