"""API v1 router for permanent and dynamic red zones (Chunk M3-10 / M5-07)."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.risk import RedZone
from app.schemas.common import PaginatedResponse, PaginationMetadata, ResponseEnvelope
from app.schemas.red_zones import RedZoneRead

red_zones_router = APIRouter()


@red_zones_router.get(
    "",
    response_model=PaginatedResponse[RedZoneRead],
    summary="List demarcated red zones",
    description="Retrieve paginated high-risk perimeter MultiPolygons with spatial filtering.",
)
def list_red_zones(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    zone_type: Optional[str] = Query(None, description="Filter by zone danger type"),
    danger_level: Optional[str] = Query(None, description="Filter by danger severity level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """Retrieve demarcated red zones matching filter criteria."""
    query = db.query(RedZone)

    if zone_type is not None:
        query = query.filter(RedZone.zone_type == zone_type.lower().strip())

    if danger_level is not None:
        query = query.filter(RedZone.danger_level == danger_level.lower().strip())

    if is_active is not None:
        query = query.filter(RedZone.is_active == is_active)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    records = (
        query.order_by(RedZone.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        meta = r.metadata_json or {}
        items.append(
            RedZoneRead(
                id=r.id,
                name=r.name,
                zone_type=r.zone_type,
                danger_level=r.danger_level,
                geometry=r.geometry,
                area_sq_km=r.area_sq_km,
                is_active=r.is_active,
                declared_by_officer_id=r.declared_by_officer_id,
                declared_at=r.declared_at,
                contributing_village_ids=meta.get("contributing_village_ids", []),
                explainability=meta.get("explainability"),
            )
        )

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


@red_zones_router.get(
    "/{id}",
    response_model=ResponseEnvelope[RedZoneRead],
    summary="Get red zone details by ID",
    description="Retrieve single red zone perimeter and analytical justification.",
)
def get_red_zone(
    id: int = Path(..., ge=1, description="Red zone primary key ID"),
    db: Session = Depends(get_db),
):
    """Retrieve single red zone by ID."""
    zone = db.query(RedZone).filter(RedZone.id == id).first()
    if not zone:
        raise NotFoundError(message=f"Red Zone with ID {id} was not found.")

    meta = zone.metadata_json or {}
    data = RedZoneRead(
        id=zone.id,
        name=zone.name,
        zone_type=zone.zone_type,
        danger_level=zone.danger_level,
        geometry=zone.geometry,
        area_sq_km=zone.area_sq_km,
        is_active=zone.is_active,
        declared_by_officer_id=zone.declared_by_officer_id,
        declared_at=zone.declared_at,
        contributing_village_ids=meta.get("contributing_village_ids", []),
        explainability=meta.get("explainability"),
    )

    return ResponseEnvelope(success=True, data=data)
