"""API v1 Regions & GIS Map Layers router."""

import json
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Path, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.profiles import get_profile, list_profiles
from app.core.regions import resolve_region_scope, apply_region_scope_to_village_query
from app.data.providers.contracts import ProviderQuery, SourceCategory
from app.data.providers.usgs_earthquake import USGSEarthquakeProvider
from app.models.geographic import Block, District, Region, Village
from app.models.hazards import HazardObservation
from app.models.relocation import CandidateSite, Route
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
    layer_type: Optional[str] = Query(None, description="Filter specific layer: villages, village_boundaries, red_zones, sites, hazards, earthquakes_ncs, earthquakes_usgs, routes, osm_roads"),
    region_id: Optional[str] = Query(None, description="Filter by region code or numeric ID"),
    db: Session = Depends(get_db),
):
    """Retrieve GeoJSON map layers for interactive MapLibre visualization."""
    layers: Dict[str, Any] = {}
    scope = resolve_region_scope(db, region_id)

    # 1. Villages Centroid Points Layer
    if layer_type in (None, "villages"):
        v_query = db.query(Village).options(
            joinedload(Village.population_profile),
            joinedload(Village.risk_scores),
        )
        v_query = apply_region_scope_to_village_query(v_query, scope)

        v_records = v_query.all()
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
                        "provenance": "REAL / OFFICIAL — Census 2011 & Survey of India Centroid",
                    },
                }
            )
        layers["villages"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    # 2. Village Boundaries Layer (Real Survey of India Cadastral Polygons)
    if layer_type in (None, "village_boundaries"):
        vb_query = db.query(Village).options(
            joinedload(Village.population_profile),
            joinedload(Village.risk_scores),
        )
        vb_query = apply_region_scope_to_village_query(vb_query, scope, is_boundary=True)

        vb_records = vb_query.all()
        vb_features = []
        for v in vb_records:
            try:
                geom = mapping(to_shape(v.boundary))
                current_risk = next((r for r in v.risk_scores if r.is_current), None)
                vb_features.append(
                    {
                        "type": "Feature",
                        "id": f"boundary-{v.id}",
                        "geometry": geom,
                        "properties": {
                            "id": v.id,
                            "boundary_id": f"boundary-{v.id}",
                            "entity_type": "village_boundary",
                            "name": v.name,
                            "census_code": v.census_code,
                            "elevation_m": v.elevation_m,
                            "slope_deg": v.slope_deg,
                            "population": v.population_profile.total_population if v.population_profile else None,
                            "households": v.population_profile.households if v.population_profile else None,
                            "risk_score": current_risk.score if current_risk else None,
                            "risk_band": current_risk.band if current_risk else "MODERATE",
                            "provenance": "REAL / OFFICIAL — Survey of India (Boundary Cadastral Polygon)",
                        },
                    }
                )
            except Exception:
                continue
        layers["village_boundaries"] = {
            "type": "FeatureCollection",
            "features": vb_features,
        }

    # 3. Red Zones Layer
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
                        "provenance": "DERIVED / DEMONSTRATION — Permanent & Dynamic Red Zone Spatial Engine",
                    },
                }
            )
        layers["red_zones"] = {
            "type": "FeatureCollection",
            "features": features,
        }

    # 4. Candidate Relocation Sites Layer
    if layer_type in (None, "sites", "candidate_sites"):
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
                        "provenance": "SYNTHETIC / PROPOSED — Candidate Relocation Site",
                    },
                }
            )
        layers["sites"] = {
            "type": "FeatureCollection",
            "features": features,
        }
        layers["candidate_sites"] = layers["sites"]

    # 5. NCS Historical Earthquakes Layer (150 Real Events)
    if layer_type in (None, "earthquakes_ncs", "hazards"):
        haz_records = db.query(HazardObservation).order_by(HazardObservation.observed_at.desc()).all()
        ncs_features = []
        for h in haz_records:
            if not h.location:
                continue
            geom = mapping(to_shape(h.location))
            ncs_features.append(
                {
                    "type": "Feature",
                    "id": f"ncs-{h.id}",
                    "geometry": geom,
                    "properties": {
                        "id": h.id,
                        "event_id": f"NCS-{h.id}",
                        "entity_type": "earthquake_ncs",
                        "hazard_type": h.hazard_type,
                        "magnitude": h.intensity_value,
                        "intensity_unit": h.intensity_unit or "Richter",
                        "depth_km": 10.0,
                        "observed_at": h.observed_at.isoformat() if h.observed_at else None,
                        "severity": h.severity,
                        "description": h.description or f"NCS Earthquake M{h.intensity_value}",
                        "source": "National Centre for Seismology (NCS), Ministry of Earth Sciences",
                        "provenance": "REAL / OFFICIAL — National Centre for Seismology MoES (1991–2024)",
                    },
                }
            )
        layers["earthquakes_ncs"] = {
            "type": "FeatureCollection",
            "features": ncs_features,
        }
        layers["hazards"] = {
            "type": "FeatureCollection",
            "features": ncs_features,
        }

    # 6. USGS Live Real-Time Earthquakes Layer
    if layer_type in (None, "earthquakes_usgs"):
        usgs_features = []
        try:
            provider = USGSEarthquakeProvider(timeout_sec=4.0)
            query = ProviderQuery(
                category=SourceCategory.HAZARD_OBSERVATION,
                region_id=region_id or "himalayan_pilot",
                district_code="chamoli",
            )
            resp = provider.fetch_data(query)
            for rec in resp.records:
                usgs_features.append(
                    {
                        "type": "Feature",
                        "id": f"usgs-{rec.record_id}",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [rec.location_coordinates[0], rec.location_coordinates[1]],
                        },
                        "properties": {
                            "id": f"usgs-{rec.record_id}",
                            "event_id": rec.record_id,
                            "entity_type": "earthquake_usgs",
                            "magnitude": rec.intensity_value,
                            "depth_km": 10.0,
                            "observed_at": rec.observed_at,
                            "severity": rec.severity,
                            "description": rec.description or f"USGS Live Seismic Event M{rec.intensity_value}",
                            "source": "USGS Earthquake Hazards Program (Live FDSN Feed)",
                            "provenance": "LIVE — USGS Real-Time Feed",
                        },
                    }
                )
        except Exception as exc:
            import logging
            logging.getLogger("rakshakgis.map").warning("USGS live earthquake feed unavailable: %s", exc)

        layers["earthquakes_usgs"] = {
            "type": "FeatureCollection",
            "features": usgs_features,
        }

    # 7. Evacuation Routes Layer
    if layer_type in (None, "routes"):
        routes_records = db.query(Route).all()
        route_features = []
        for r in routes_records:
            if not r.path:
                continue
            geom = mapping(to_shape(r.path))
            route_features.append(
                {
                    "type": "Feature",
                    "id": r.id,
                    "geometry": geom,
                    "properties": {
                        "id": r.id,
                        "name": r.name,
                        "route_type": r.route_type,
                        "distance_km": r.distance_km,
                        "estimated_travel_time_min": r.estimated_travel_time_min,
                        "is_blocked": False,
                        "provenance": "SYNTHETIC / DERIVED — Evacuation Corridors",
                    },
                }
            )
        layers["routes"] = {
            "type": "FeatureCollection",
            "features": route_features,
        }

    # 8. OpenStreetMap Regional Road Network Layer
    if layer_type in (None, "osm_roads"):
        osm_path = os.path.join("data", "processed", "osm", "chamoli_roads.geojson")
        if os.path.exists(osm_path):
            try:
                with open(osm_path, "r", encoding="utf-8") as f:
                    layers["osm_roads"] = json.load(f)
            except Exception:
                layers["osm_roads"] = {"type": "FeatureCollection", "features": []}
        else:
            layers["osm_roads"] = {"type": "FeatureCollection", "features": []}

    # 9. Geographic Bounding Box for Viewport Auto-fit (Chamoli District)
    layers["bounds"] = [[79.15, 30.0], [80.15, 30.9]]

    # 10. Truthful Layer Provenance Metadata
    layers["layer_provenance"] = {
        "village_boundaries": "REAL / OFFICIAL — Survey of India (Boundary Cadastral Polygon)",
        "villages": "REAL / OFFICIAL — Census 2011 & Survey of India Centroid",
        "earthquakes_ncs": "REAL / OFFICIAL — National Centre for Seismology MoES (1991–2024)",
        "earthquakes_usgs": "LIVE — USGS Real-Time Feed",
        "sites": "SYNTHETIC / PROPOSED — Candidate Relocation Site",
        "candidate_sites": "SYNTHETIC / PROPOSED — Candidate Relocation Site",
        "routes": "SYNTHETIC / DERIVED — Evacuation Corridors",
        "red_zones": "DERIVED / DEMONSTRATION — Permanent & Dynamic Red Zone Spatial Engine",
        "osm_roads": "DERIVED / OFFLINE — OpenStreetMap Road Network Extract",
    }

    return ResponseEnvelope(success=True, data=layers)
