"""API v1 router for administrative villages (GIS Habitations)."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.geographic import Village, Block
from app.schemas.common import PaginatedResponse, PaginationMetadata, ResponseEnvelope
from app.schemas.villages import VillageDetailRead, VillageRead

villages_router = APIRouter()


@villages_router.get(
    "",
    response_model=PaginatedResponse[VillageRead],
    summary="List administrative villages",
    description="Retrieve paginated settlement habitations with PostGIS Point location and optional filters.",
)
def list_villages(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    district_id: Optional[int] = Query(None, description="Filter by parent district ID"),
    block_id: Optional[int] = Query(None, description="Filter by administrative block ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Case-insensitive name search query"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated habitations matching filter criteria."""
    query = db.query(Village)

    if block_id is not None:
        query = query.filter(Village.block_id == block_id)

    if district_id is not None:
        query = query.join(Village.block).filter(Block.district_id == district_id)

    if is_active is not None:
        query = query.filter(Village.is_active == is_active)

    if search is not None and search.strip():
        query = query.filter(Village.name.ilike(f"%{search.strip()}%"))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    records = (
        query.order_by(Village.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [VillageRead.model_validate(v) for v in records]
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


@villages_router.get(
    "/{id}",
    response_model=ResponseEnvelope[VillageDetailRead],
    summary="Get village details by ID",
    description="Retrieve full settlement profile including demographics, vulnerability, and hazards.",
)
def get_village(
    id: int = Path(..., ge=1, description="Village primary key ID"),
    db: Session = Depends(get_db),
):
    """Retrieve single village by ID."""
    village = (
        db.query(Village)
        .options(
            joinedload(Village.population_profile),
            joinedload(Village.vulnerability_profile),
            joinedload(Village.risk_scores),
        )
        .filter(Village.id == id)
        .first()
    )

    if not village:
        raise NotFoundError(message=f"Village with ID {id} was not found.")

    meta = getattr(village, "metadata_json", {}) or {}
    pop_prof = village.population_profile
    vuln_prof = village.vulnerability_profile

    demographics = {
        "elderly_count": pop_prof.elderly_count,
        "children_count": pop_prof.children_count,
        "disabled_count": pop_prof.disabled_count,
        "livestock_count": pop_prof.livestock_count,
    } if pop_prof else None

    vulnerability = {
        "social_vulnerability_index": vuln_prof.social_vulnerability_index,
        "economic_vulnerability_index": vuln_prof.economic_vulnerability_index,
        "structural_vulnerability_index": vuln_prof.structural_vulnerability_index,
        "road_connectivity_index": vuln_prof.road_connectivity_index,
        "composite_vulnerability_score": vuln_prof.composite_vulnerability_score,
    } if vuln_prof else None

    hazards = {
        "elevation_m": village.elevation_m,
        "slope_deg": village.slope_deg,
    }

    detail = VillageDetailRead(
        id=village.id,
        name=village.name,
        census_code=village.census_code,
        block_id=village.block_id,
        location=village.location,
        boundary=village.boundary,
        elevation_m=village.elevation_m,
        slope_deg=village.slope_deg,
        is_active=village.is_active,
        population=pop_prof.total_population if pop_prof else None,
        households=pop_prof.households if pop_prof else None,
        demographics=demographics,
        vulnerability=vulnerability,
        hazards=hazards,
        metadata_json=meta,
    )

    return ResponseEnvelope(success=True, data=detail)
