"""API v1 base router registration."""

from fastapi import APIRouter

from app.api.v1.alerts import alerts_router
from app.api.v1.auth import auth_router
from app.api.v1.gis import gis_router
from app.api.v1.governance import audit_router, governance_router
from app.api.v1.red_zones import red_zones_router
from app.api.v1.regions import map_layers_router, regions_router
from app.api.v1.relocation import relocation_router
from app.api.v1.reports import reports_router
from app.api.v1.risk import risk_router
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

# Administrative Hierarchy & Regions endpoints
api_router.include_router(regions_router, prefix="/regions", tags=["Administrative Regions"])

# GIS Map Layers endpoint
api_router.include_router(map_layers_router, prefix="/map", tags=["GIS Map Layers"])

# Administrative Villages & Habitations endpoints
api_router.include_router(villages_router, prefix="/villages", tags=["Administrative Villages"])

# Multi-Hazard Risk Assessment endpoints
api_router.include_router(risk_router, prefix="/risk", tags=["Multi-Hazard Risk Assessment"])

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

# GIS Spatial Search endpoints
api_router.include_router(gis_router, prefix="/gis", tags=["GIS Spatial Search"])

# Platform Governance & Decisions endpoints
api_router.include_router(governance_router, prefix="/governance", tags=["Platform Governance"])
api_router.include_router(governance_router, prefix="/officer-decisions", tags=["Platform Governance"])

# Immutable Audit Trail endpoints
api_router.include_router(audit_router, prefix="/audit", tags=["Audit Trail"])

# Analytical Action Plan Reports endpoints
api_router.include_router(reports_router, prefix="/reports", tags=["Action Plan Reports"])

# Data Source Freshness & Telemetry endpoints
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["Data Source Telemetry"])
api_router.include_router(telemetry_router, prefix="/data-sources", tags=["Data Source Telemetry"])
api_router.include_router(telemetry_router, prefix="/data", tags=["Data Source Telemetry"])


@api_router.get("", tags=["System"])
def api_v1_root() -> dict:
    """API v1 status endpoint."""
    return {
        "status": "online",
        "api_version": "v1",
        "app": settings.PROJECT_NAME,
    }

