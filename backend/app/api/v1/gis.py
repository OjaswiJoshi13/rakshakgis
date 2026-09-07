"""API v1 Unified GIS Spatial Search router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.geographic import Region, Village
from app.models.relocation import CandidateSite
from app.models.risk import RedZone
from app.schemas.common import ResponseEnvelope

gis_router = APIRouter()


@gis_router.get(
    "/search",
    response_model=ResponseEnvelope[List[Dict[str, Any]]],
    summary="Unified GIS spatial search",
    description="Search villages, candidate sites, red zones, and administrative regions by keyword or code.",
)
def search_gis_entities(
    q: str = Query(..., min_length=1, description="Search keyword (name, census code, or region)"),
    types: Optional[str] = Query(None, description="Comma-separated entity types: village, site, red_zone, region"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    db: Session = Depends(get_db),
):
    """Execute multi-entity spatial keyword search."""
    search_term = f"%{q.strip()}%"
    allowed_types = [t.strip().lower() for t in types.split(",")] if types else ["village", "site", "red_zone", "region"]
    results: List[Dict[str, Any]] = []

    # 1. Search Villages
    if "village" in allowed_types and len(results) < limit:
        villages = (
            db.query(Village)
            .filter(
                (Village.name.ilike(search_term))
                | (Village.census_code.ilike(search_term))
            )
            .limit(limit - len(results))
            .all()
        )
        for v in villages:
            coords = None
            if v.location:
                pt = to_shape(v.location)
                coords = [float(pt.x), float(pt.y)]

            current_risk = next((r for r in v.risk_scores if r.is_current), None)
            results.append(
                {
                    "entity_type": "village",
                    "id": v.id,
                    "name": v.name,
                    "code": v.census_code,
                    "coordinates": coords,
                    "highlight": f"Risk: {current_risk.score if current_risk else 'N/A'} ({current_risk.band if current_risk else 'UNASSESSED'})",
                    "elevation_m": v.elevation_m,
                    "slope_deg": v.slope_deg,
                }
            )

    # 2. Search Candidate Sites
    if "site" in allowed_types and len(results) < limit:
        sites = (
            db.query(CandidateSite)
            .filter(CandidateSite.name.ilike(search_term))
            .limit(limit - len(results))
            .all()
        )
        for s in sites:
            coords = None
            if s.location:
                pt = to_shape(s.location)
                coords = [float(pt.x), float(pt.y)]
            cap = s.capacities[0] if s.capacities else None
            results.append(
                {
                    "entity_type": "candidate_site",
                    "id": s.id,
                    "name": s.name,
                    "code": f"SITE-{s.id}",
                    "coordinates": coords,
                    "highlight": f"Capacity: {cap.max_households if cap else 'N/A'} households, Suitability: {s.suitability_score or 'N/A'}",
                    "status": s.status,
                }
            )

    # 3. Search Red Zones
    if "red_zone" in allowed_types and len(results) < limit:
        rzs = (
            db.query(RedZone)
            .filter(RedZone.name.ilike(search_term))
            .limit(limit - len(results))
            .all()
        )
        for rz in rzs:
            results.append(
                {
                    "entity_type": "red_zone",
                    "id": rz.id,
                    "name": rz.name,
                    "code": f"RZ-{rz.id}",
                    "coordinates": None,
                    "highlight": f"Danger: {rz.danger_level.upper()} ({rz.zone_type})",
                    "area_sq_km": rz.area_sq_km,
                }
            )

    # 4. Search Regions
    if "region" in allowed_types and len(results) < limit:
        regs = (
            db.query(Region)
            .filter(
                (Region.name.ilike(search_term))
                | (Region.code.ilike(search_term))
            )
            .limit(limit - len(results))
            .all()
        )
        for r in regs:
            results.append(
                {
                    "entity_type": "region",
                    "id": r.id,
                    "name": r.name,
                    "code": r.code,
                    "coordinates": None,
                    "highlight": f"State: {r.state}",
                }
            )

    return ResponseEnvelope(success=True, data=results[:limit])
