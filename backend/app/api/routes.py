"""API v1 base router registration."""

from fastapi import APIRouter

from app.api.v1.alerts import alerts_router
from app.api.v1.auth import auth_router
from app.api.v1.red_zones import red_zones_router
from app.api.v1.relocation import relocation_router
from app.api.v1.routing import routing_router
from app.api.v1.scenarios import scenarios_router
from app.api.v1.sites import sites_router
from app.api.v1.telemetry import telemetry_router
from app.api.v1.villages import villages_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

# Authentication & authorization endpoints
api_router.include_router(auth_router, prefix="/auth")

# Administrative Villages & Habitations endpoints
api_router.include_router(villages_router, prefix="/villages", tags=["Administrative Villages"])

# Demarcated Red Zones endpoints
api_router.include_router(red_zones_router, prefix="/red-zones", tags=["Red Zones"])

# Real-Time Alerts endpoints
api_router.include_router(alerts_router, prefix="/alerts", tags=["Real-Time Alerts"])

# Candidate Relocation Sites endpoints
api_router.include_router(sites_router, prefix="/sites", tags=["Candidate Relocation Sites"])

# Relocation Matching & Assignment endpoints
api_router.include_router(relocation_router, prefix="/relocation", tags=["Relocation Matching"])

# Evacuation & Access Routing endpoints
api_router.include_router(routing_router, prefix="/routes", tags=["Evacuation & Access Routing"])

# Scenario Simulator endpoints
api_router.include_router(scenarios_router, prefix="/scenarios", tags=["Scenario Simulator"])

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

