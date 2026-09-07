"""API v1 Regions & GIS Map Layers router."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Path, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.profiles import get_profile, list_profiles
from app.models.geographic import Block, District, Region, Village
from app.models.hazards import HazardObservation
from app.models.relocation import CandidateSite
from app.models.risk import RedZone, RiskScore
from app.schemas.common import ResponseEnvelope

regions_router = APIRouter()


@regions_router.get(
    "",
    response_model=ResponseEnvelope[List[Dict[str, Any]]],
    summary="List available regions",
    description="Retrieve all configured geographic regions with bounding boxes, risk profiles, and village counts.",
)
def list_regions(
    db: Session = Depends(get_db),
):
    """List operational regions from database and registry."""
    regions = db.query(Region).order_by(Region.id.asc()).all()
    results = []

    for r in regions:
        # Calculate village count
        village_count = (
            db.query(Village)
            .join(Village.block)
            .join(Block.district)
            .filter(District.region_id == r.id)
            .count()
        )

        profile_meta = {}
        try:
            p = get_profile(r.code)
            profile_meta = {
                "supported_hazards": [h.value if hasattr(h, "value") else str(h) for h in getattr(p, "supported_hazards", [])],
                "risk_weights": getattr(p, "risk_weights", {}),
                "priority_thresholds": getattr(p, "priority_thresholds", {}),
            }
        except Exception:
            pass

        meta = r.metadata_json or {}
        results.append(
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "state": r.state,
                "village_count": village_count,
                "metadata": meta,
                "profile": profile_meta,
            }
        )

    return ResponseEnvelope(success=True, data=results)


@regions_router.get(
    "/{id}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Get region details by ID or code",
    description="Retrieve single region details with administrative hierarchy and hazard profile.",
)
def get_region(
    id: str = Path(..., description="Region ID or code string (e.g. uttarakhand_himalayan or 2)"),
    db: Session = Depends(get_db),
):
    """Retrieve detailed regional profile."""
    if id.isdigit():
        region = db.query(Region).filter(Region.id == int(id)).first()
    else:
        region = db.query(Region).filter(Region.code == id).first()

    if not region:
        raise NotFoundError(f"Region '{id}' not found.")

    districts = []
    for d in region.districts:
        blocks = [{"id": b.id, "code": b.code, "name": b.name} for b in d.blocks]
        districts.append(
            {
                "id": d.id,
                "code": d.code,
                "name": d.name,
                "headquarters": d.headquarters,
                "blocks": blocks,
            }
        )

    profile_data = {}
    try:
        p = get_profile(region.code)
        profile_data = {
            "supported_hazards": [h.value if hasattr(h, "value") else str(h) for h in getattr(p, "supported_hazards", [])],
            "risk_weights": getattr(p, "risk_weights", {}),
            "priority_thresholds": getattr(p, "priority_thresholds", {}),
            "site_rules": getattr(p, "site_rules", {}),
        }
    except Exception:
        pass

    return ResponseEnvelope(
        success=True,
        data={
            "id": region.id,
            "code": region.code,
            "name": region.name,
            "state": region.state,
            "districts": districts,
            "profile": profile_data,
            "metadata": region.metadata_json or {},
        },
    )


# Map Layers endpoint
map_layers_router = APIRouter()


@map_layers_router.get(
    "/layers",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Get spatial GIS layers GeoJSON",
    description="Retrieve authoritative vector GeoJSON FeatureCollections for villages, red zones, candidate sites, and hazards.",
)
def get_map_layers(
    layer_type: Optional[str] = Query(None, description="Filter specific layer: villages, red_zones, sites, hazards"),
    region_id: Optional[str] = Query(None, description="Filter by region code or numeric ID"),
    db: Session = Depends(get_db),
):
    """Retrieve GeoJSON map layers for interactive MapLibre visualization."""
    layers: Dict[str, Any] = {}

    # 1. Villages Layer
    if layer_type in (None, "villages"):
        v_query = db.query(Village).options(
            joinedload(Village.population_profile),
            joinedload(Village.risk_scores),
        )
        if region_id:
            if region_id.isdigit():
                v_query = v_query.join(Village.block).join(Block.district).filter(District.region_id == int(region_id))
            else:
                v_query = v_query.join(Village.block).join(Block.district).join(District.region).filter(Region.code == region_id)

        v_records = v_query.limit(200).all()
        features = []
        for v in v_records:
            if not v.location:
                continue
            geom = mapping(to_shape(v.location))
            current_risk = next((r for r in v.risk_scores if r.is_current), None)
            features.append(
                {
                    "type": "Feature",
                    "id": v.id,
                    "geometry": geom,
                    "properties": {
                        "id": v.id,
                        "entity_type": "village",
                        "name": v.name,
                        "census_code": v.census_code,
                        "population": v.population_profile.total_population if v.population_profile else None,
                        "risk_score": current_risk.score if current_risk else None,
                        "risk_band": current_risk.band if current_risk else "MODERATE",
                        "is_active": v.is_active,
                        "has_boundary": v.boundary is not None,
                    },
                }
            )
        layers["villages"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    # 2. Red Zones Layer
    if layer_type in (None, "red_zones"):
        rz_records = db.query(RedZone).filter(RedZone.is_active == True).all()
        features = []
        for rz in rz_records:
            if not rz.geometry:
                continue
            geom = mapping(to_shape(rz.geometry))
            features.append(
                {
                    "type": "Feature",
                    "id": rz.id,
                    "geometry": geom,
                    "properties": {
                        "id": rz.id,
                        "entity_type": "red_zone",
                        "name": rz.name,
                        "zone_type": rz.zone_type,
                        "danger_level": rz.danger_level,
                        "area_sq_km": rz.area_sq_km,
                        "is_active": rz.is_active,
                    },
                }
            )
        layers["red_zones"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    # 3. Candidate Relocation Sites Layer
    if layer_type in (None, "sites"):
        sites_records = db.query(CandidateSite).options(joinedload(CandidateSite.capacities)).all()
        features = []
        for s in sites_records:
            if not s.location:
                continue
            geom = mapping(to_shape(s.location))
            cap = s.capacities[0] if s.capacities else None
            features.append(
                {
                    "type": "Feature",
                    "id": s.id,
                    "geometry": geom,
                    "properties": {
                        "id": s.id,
                        "entity_type": "candidate_site",
                        "name": s.name,
                        "status": s.status,
                        "suitability_score": s.suitability_score,
                        "housing_capacity": cap.max_households if cap else None,
                        "total_capacity": cap.max_population if cap else None,
                        "current_occupancy": cap.allocated_population if cap else 0,
                    },
                }
            )
        layers["sites"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    # 4. Hazards Layer (NCS Seismology & active observations)
    if layer_type in (None, "hazards"):
        haz_records = db.query(HazardObservation).order_by(HazardObservation.observed_at.desc()).limit(150).all()
        features = []
        for h in haz_records:
            if not h.location:
                continue
            geom = mapping(to_shape(h.location))
            features.append(
                {
                    "type": "Feature",
                    "id": h.id,
                    "geometry": geom,
                    "properties": {
                        "id": h.id,
                        "entity_type": "hazard_observation",
                        "hazard_type": h.hazard_type,
                        "severity": h.severity,
                        "intensity_value": h.intensity_value,
                        "intensity_unit": h.intensity_unit,
                        "observed_at": h.observed_at.isoformat() if h.observed_at else None,
                        "description": h.description,
                    },
                }
            )
        layers["hazards"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    return ResponseEnvelope(success=True, data=layers)
