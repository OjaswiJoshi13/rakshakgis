"""API v1 Candidate Relocation Sites router."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from geoalchemy2.elements import WKTElement

from app.core.database import get_db
from app.core.exceptions import NotFoundError, BadRequestError
from app.api.deps import require_roles, UserRole
from app.models.governance import User
from app.models.geographic import District
from app.models.relocation import CandidateSite
from app.core.profiles.registry import get_profile
from app.core.relocation.suitability import (
    SiteSuitabilityEngine,
    SiteSuitabilityInput,
    SiteSuitabilityResult,
)
from app.schemas.common import (
    ResponseEnvelope,
    PaginatedResponse,
    PaginationMetadata,
)
from app.schemas.sites import (
    CandidateSiteRead,
    CandidateSiteDetailRead,
    CandidateSiteCreate,
    CandidateSiteUpdate,
    SiteEvaluationRequest,
)

sites_router = APIRouter()



def _geojson_point_to_wkt(point_schema) -> WKTElement:
    """Convert GeoJSONPoint schema to PostGIS WKTElement POINT (SRID 4326)."""
    lon, lat = point_schema.coordinates
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def _geojson_polygon_to_wkt(polygon_schema) -> WKTElement:
    """Convert GeoJSONPolygon schema to PostGIS WKTElement POLYGON (SRID 4326)."""
    rings_wkt = []
    for ring in polygon_schema.coordinates:
        pts_wkt = ", ".join(f"{pt[0]} {pt[1]}" for pt in ring)
        rings_wkt.append(f"({pts_wkt})")
    polygon_str = f"POLYGON({', '.join(rings_wkt)})"
    return WKTElement(polygon_str, srid=4326)


@sites_router.get(
    "",
    response_model=PaginatedResponse[CandidateSiteRead],
    summary="List candidate relocation sites",
    description="Retrieve paginated candidate safe sites with optional domain filters.",
)
def list_candidate_sites(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (proposed, approved, rejected, active)"
    ),
    min_elevation_m: Optional[float] = Query(None, description="Minimum elevation in meters"),
    max_elevation_m: Optional[float] = Query(None, description="Maximum elevation in meters"),
    min_area_sq_m: Optional[float] = Query(None, description="Minimum area in sq meters"),
    max_area_sq_m: Optional[float] = Query(None, description="Maximum area in sq meters"),
    search: Optional[str] = Query(None, description="Case-insensitive name search query"),
    db: Session = Depends(get_db),
):
    """Retrieve list of candidate sites matching criteria."""
    query = db.query(CandidateSite)

    if district_id is not None:
        query = query.filter(CandidateSite.district_id == district_id)

    if status_filter is not None:
        query = query.filter(CandidateSite.status == status_filter.lower().strip())

    if min_elevation_m is not None:
        query = query.filter(CandidateSite.elevation_m >= min_elevation_m)

    if max_elevation_m is not None:
        query = query.filter(CandidateSite.elevation_m <= max_elevation_m)

    if min_area_sq_m is not None:
        query = query.filter(CandidateSite.area_sq_m >= min_area_sq_m)

    if max_area_sq_m is not None:
        query = query.filter(CandidateSite.area_sq_m <= max_area_sq_m)

    if search is not None and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(CandidateSite.name.ilike(search_pattern))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    sites = (
        query.order_by(CandidateSite.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [CandidateSiteRead.model_validate(site) for site in sites]
    pagination = PaginationMetadata(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(
        success=True,
        data=items,
        pagination=pagination,
    )


@sites_router.get(
    "/{id}",
    response_model=ResponseEnvelope[CandidateSiteDetailRead],
    summary="Get candidate relocation site details",
    description="Retrieve detailed site information including capacities and infrastructure by ID.",
)
def get_candidate_site(
    id: int = Path(..., ge=1, description="Candidate site ID"),
    db: Session = Depends(get_db),
):
    """Retrieve detailed candidate site by ID."""
    site = (
        db.query(CandidateSite)
        .options(
            joinedload(CandidateSite.capacities),
            joinedload(CandidateSite.infrastructures),
        )
        .filter(CandidateSite.id == id)
        .first()
    )

    if not site:
        raise NotFoundError(message=f"Candidate site with ID {id} was not found.")

    data = CandidateSiteDetailRead.model_validate(site)
    return ResponseEnvelope(success=True, data=data)


@sites_router.post(
    "",
    response_model=ResponseEnvelope[CandidateSiteDetailRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate relocation site",
    description="Create a new candidate relocation site. Requires ADMIN or DISTRICT_OFFICER role.",
)
def create_candidate_site(
    site_in: CandidateSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)
    ),
):
    """Create new candidate relocation site."""
    # Verify district exists (HTTP 404 NotFoundError if district doesn't exist)
    district = db.query(District).filter(District.id == site_in.district_id).first()
    if not district:
        raise NotFoundError(message=f"District with ID {site_in.district_id} was not found.")

    wkt_location = _geojson_point_to_wkt(site_in.location)
    wkt_boundary = (
        _geojson_polygon_to_wkt(site_in.boundary) if site_in.boundary else None
    )

    db_site = CandidateSite(
        name=site_in.name,
        district_id=site_in.district_id,
        location=wkt_location,
        boundary=wkt_boundary,
        area_sq_m=site_in.area_sq_m,
        terrain_slope_deg=site_in.terrain_slope_deg,
        elevation_m=site_in.elevation_m,
        status=site_in.status or "proposed",
    )

    db.add(db_site)
    db.commit()
    db.refresh(db_site)

    # Re-query with relationship loading
    site = (
        db.query(CandidateSite)
        .options(
            joinedload(CandidateSite.capacities),
            joinedload(CandidateSite.infrastructures),
        )
        .filter(CandidateSite.id == db_site.id)
        .first()
    )

    data = CandidateSiteDetailRead.model_validate(site)
    return ResponseEnvelope(success=True, data=data)


@sites_router.patch(
    "/{id}",
    response_model=ResponseEnvelope[CandidateSiteDetailRead],
    summary="Update candidate relocation site",
    description="Partially update candidate relocation site attributes. Requires ADMIN or DISTRICT_OFFICER role.",
)
def update_candidate_site(
    id: int = Path(..., ge=1, description="Candidate site ID"),
    site_in: CandidateSiteUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)
    ),
):
    """Update existing candidate site by ID."""
    site = db.query(CandidateSite).filter(CandidateSite.id == id).first()
    if not site:
        raise NotFoundError(message=f"Candidate site with ID {id} was not found.")

    update_data = site_in.model_dump(exclude_unset=True)

    if "district_id" in update_data and update_data["district_id"] is not None:
        district = (
            db.query(District)
            .filter(District.id == update_data["district_id"])
            .first()
        )
        if not district:
            raise NotFoundError(message=f"District with ID {update_data['district_id']} was not found.")
        site.district_id = update_data["district_id"]

    if "name" in update_data and update_data["name"] is not None:
        site.name = update_data["name"]

    if "location" in update_data and update_data["location"] is not None:
        site.location = _geojson_point_to_wkt(site_in.location)

    if "boundary" in update_data:
        if site_in.boundary is not None:
            site.boundary = _geojson_polygon_to_wkt(site_in.boundary)
        else:
            site.boundary = None

    if "area_sq_m" in update_data:
        site.area_sq_m = update_data["area_sq_m"]

    if "terrain_slope_deg" in update_data:
        site.terrain_slope_deg = update_data["terrain_slope_deg"]

    if "elevation_m" in update_data:
        site.elevation_m = update_data["elevation_m"]

    if "status" in update_data and update_data["status"] is not None:
        site.status = update_data["status"]

    db.commit()

    # Re-query with relationships loaded
    updated_site = (
        db.query(CandidateSite)
        .options(
            joinedload(CandidateSite.capacities),
            joinedload(CandidateSite.infrastructures),
        )
        .filter(CandidateSite.id == id)
        .first()
    )

    data = CandidateSiteDetailRead.model_validate(updated_site)
    return ResponseEnvelope(success=True, data=data)


@sites_router.delete(
    "/{id}",
    response_model=ResponseEnvelope[dict],
    summary="Delete candidate relocation site",
    description="Delete a candidate relocation site. Requires ADMIN or DISTRICT_OFFICER role.",
)
def delete_candidate_site(
    id: int = Path(..., ge=1, description="Candidate site ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)
    ),
):
    """Delete candidate relocation site by ID."""
    site = db.query(CandidateSite).filter(CandidateSite.id == id).first()
    if not site:
        raise NotFoundError(message=f"Candidate site with ID {id} was not found.")

    try:
        db.delete(site)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BadRequestError(
            message=f"Cannot delete candidate site {id} because dependent records exist."
        ) from exc

    return ResponseEnvelope(
        success=True,
        data={"id": id, "deleted": True},
    )


def _resolve_suitability_engine(profile_id: Optional[str]) -> SiteSuitabilityEngine:
    """Resolve SiteSuitabilityEngine configured for the specified profile without silent fallback."""
    if not profile_id:
        return SiteSuitabilityEngine()
    profile = get_profile(profile_id)
    return SiteSuitabilityEngine.from_region_profile(profile)


@sites_router.post(
    "/evaluate",
    response_model=ResponseEnvelope[SiteSuitabilityResult],
    summary="Evaluate candidate site suitability from payload",
    description="Evaluate multi-criteria suitability and hard constraints for candidate site data provided in the request body.",
)
def evaluate_site_payload(
    site_input: SiteSuitabilityInput,
    region_profile_id: Optional[str] = Query(
        "himalayan_pilot", description="Regional configuration profile ID"
    ),
):
    """Evaluate candidate site suitability directly from payload attributes."""
    engine = _resolve_suitability_engine(region_profile_id)
    result = engine.evaluate(site_input)
    return ResponseEnvelope(success=True, data=result)


@sites_router.post(
    "/{id}/evaluate",
    response_model=ResponseEnvelope[SiteSuitabilityResult],
    summary="Evaluate candidate relocation site suitability by ID",
    description="Evaluate multi-criteria suitability and hard constraints for a candidate relocation site stored in the database.",
)
def evaluate_candidate_site(
    id: int = Path(..., ge=1, description="Candidate site ID"),
    eval_req: Optional[SiteEvaluationRequest] = None,
    db: Session = Depends(get_db),
):
    """Evaluate stored candidate site suitability by ID."""
    site = (
        db.query(CandidateSite)
        .options(
            joinedload(CandidateSite.capacities),
            joinedload(CandidateSite.infrastructures),
        )
        .filter(CandidateSite.id == id)
        .first()
    )

    if not site:
        raise NotFoundError(message=f"Candidate site with ID {id} was not found.")

    site_input = SiteSuitabilityInput.from_candidate_site_model(site)

    profile_id = (
        eval_req.region_profile_id
        if eval_req and eval_req.region_profile_id
        else "himalayan_pilot"
    )
    engine = _resolve_suitability_engine(profile_id)

    # Apply overrides if provided in request
    if eval_req and eval_req.overrides:
        for k, v in eval_req.overrides.items():
            if hasattr(site_input, k):
                setattr(site_input, k, v)

    result = engine.evaluate(site_input)

    # Persist score if requested
    if eval_req and eval_req.persist_score:
        site.suitability_score = result.overall_score
        db.commit()

    return ResponseEnvelope(success=True, data=result)


@sites_router.get(
    "/{id}/suitability",
    response_model=ResponseEnvelope[SiteSuitabilityResult],
    summary="Get candidate site suitability evaluation by ID",
    description="Retrieve the multi-criteria suitability evaluation result for a candidate site by ID.",
)
def get_candidate_site_suitability(
    id: int = Path(..., ge=1, description="Candidate site ID"),
    region_profile_id: Optional[str] = Query(
        "himalayan_pilot", description="Regional configuration profile ID"
    ),
    db: Session = Depends(get_db),
):
    """Compute and retrieve suitability result for candidate site by ID."""
    site = (
        db.query(CandidateSite)
        .options(
            joinedload(CandidateSite.capacities),
            joinedload(CandidateSite.infrastructures),
        )
        .filter(CandidateSite.id == id)
        .first()
    )

    if not site:
        raise NotFoundError(message=f"Candidate site with ID {id} was not found.")

    site_input = SiteSuitabilityInput.from_candidate_site_model(site)
    engine = _resolve_suitability_engine(region_profile_id)
    result = engine.evaluate(site_input)
    return ResponseEnvelope(success=True, data=result)
