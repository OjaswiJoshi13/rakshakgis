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
    region_id: Optional[str] = Query(None, description="Filter by region identifier or code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Case-insensitive name search query"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated habitations matching filter criteria."""
    from app.core.config import get_settings
    from app.models.geographic import District, Region

    query = db.query(Village)

    if region_id is not None:
        if region_id.isdigit():
            query = query.join(Village.block).join(Block.district).filter(District.region_id == int(region_id))
        else:
            query = query.join(Village.block).join(Block.district).join(District.region).filter(Region.code == region_id)
    elif district_id is None and block_id is None:
        if get_settings().DATA_MODE.lower() == "demo":
            # Isolate demo dataset in DEMO mode to preserve deterministic SIH demo behavior
            query = query.join(Village.block).filter(Block.code == "joshimath")

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


@villages_router.get(
    "/{id}/risk",
    response_model=ResponseEnvelope[dict],
    summary="Get village risk assessment",
    description="Retrieve current calculated multi-hazard risk score, risk band, and factor breakdown.",
)
def get_village_risk(
    id: int = Path(..., ge=1, description="Village primary key ID"),
    db: Session = Depends(get_db),
):
    """Retrieve current risk score and factor decomposition."""
    village = db.query(Village).options(joinedload(Village.risk_scores)).filter(Village.id == id).first()
    if not village:
        raise NotFoundError(message=f"Village with ID {id} was not found.")

    from app.models.risk import RiskFactor, RiskScore
    current_risk = db.query(RiskScore).filter(RiskScore.village_id == id, RiskScore.is_current == True).first()
    if not current_risk:
        current_risk = db.query(RiskScore).filter(RiskScore.village_id == id).order_by(RiskScore.calculated_at.desc()).first()

    factors = []
    if current_risk:
        factor_records = db.query(RiskFactor).filter(RiskFactor.risk_score_id == current_risk.id).all()
        factors = [
            {
                "factor_name": f.factor_name,
                "weight": f.weight,
                "normalized_score": f.normalized_score,
            }
            for f in factor_records
        ]

    return ResponseEnvelope(
        success=True,
        data={
            "village_id": village.id,
            "village_name": village.name,
            "has_risk_assessment": current_risk is not None,
            "risk_score": current_risk.score if current_risk else None,
            "risk_band": current_risk.band if current_risk else None,
            "hazard_subscore": current_risk.hazard_subscore if current_risk else None,
            "exposure_subscore": current_risk.exposure_subscore if current_risk else None,
            "vulnerability_subscore": current_risk.vulnerability_subscore if current_risk else None,
            "calculated_at": current_risk.calculated_at.isoformat() if current_risk and current_risk.calculated_at else None,
            "factors": factors,
        },
    )


@villages_router.get(
    "/{id}/analysis",
    response_model=ResponseEnvelope[dict],
    summary="Get comprehensive village disaster analysis",
    description="Retrieve consolidated demographics, vulnerability, multi-hazard risk, red zone demarcation, and seismic telemetry.",
)
def get_village_analysis(
    id: int = Path(..., ge=1, description="Village primary key ID"),
    db: Session = Depends(get_db),
):
    """Consolidated analytical dossier for disaster response authority decision-making."""
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

    from app.models.risk import RedZone, RiskFactor, RiskScore
    from app.models.hazards import HazardObservation

    current_risk = db.query(RiskScore).filter(RiskScore.village_id == id, RiskScore.is_current == True).first()
    if not current_risk:
        current_risk = db.query(RiskScore).filter(RiskScore.village_id == id).order_by(RiskScore.calculated_at.desc()).first()

    factors = []
    if current_risk:
        factor_records = db.query(RiskFactor).filter(RiskFactor.risk_score_id == current_risk.id).all()
        factors = [
            {
                "factor_name": f.factor_name,
                "weight": f.weight,
                "normalized_score": f.normalized_score,
            }
            for f in factor_records
        ]

    # Red zone status
    active_red_zone = db.query(RedZone).filter(RedZone.is_active == True).first()
    # Check if village name matches red zone
    is_in_red_zone = False
    red_zone_info = None
    if active_red_zone:
        rz_match = db.query(RedZone).filter(
            RedZone.is_active == True,
            RedZone.name.ilike(f"%{village.name}%"),
        ).first()
        if rz_match:
            is_in_red_zone = True
            red_zone_info = {
                "id": rz_match.id,
                "name": rz_match.name,
                "zone_type": rz_match.zone_type,
                "danger_level": rz_match.danger_level,
                "area_sq_km": rz_match.area_sq_km,
            }

    pop_prof = village.population_profile
    vuln_prof = village.vulnerability_profile

    # Recent hazard observations
    hazards = (
        db.query(HazardObservation)
        .order_by(HazardObservation.observed_at.desc())
        .limit(5)
        .all()
    )
    recent_hazards = [
        {
            "id": h.id,
            "hazard_type": h.hazard_type,
            "severity": h.severity,
            "intensity_value": h.intensity_value,
            "intensity_unit": h.intensity_unit,
            "description": h.description,
            "observed_at": h.observed_at.isoformat() if h.observed_at else None,
        }
        for h in hazards
    ]

    return ResponseEnvelope(
        success=True,
        data={
            "village": {
                "id": village.id,
                "name": village.name,
                "census_code": village.census_code,
                "elevation_m": village.elevation_m,
                "slope_deg": village.slope_deg,
                "is_active": village.is_active,
            },
            "population": {
                "total": pop_prof.total_population if pop_prof else None,
                "households": pop_prof.households if pop_prof else None,
                "elderly": pop_prof.elderly_count if pop_prof else None,
                "children": pop_prof.children_count if pop_prof else None,
                "disabled": pop_prof.disabled_count if pop_prof else None,
                "livestock": pop_prof.livestock_count if pop_prof else None,
            },
            "vulnerability": {
                "social_index": vuln_prof.social_vulnerability_index if vuln_prof else None,
                "economic_index": vuln_prof.economic_vulnerability_index if vuln_prof else None,
                "structural_index": vuln_prof.structural_vulnerability_index if vuln_prof else None,
                "road_connectivity_index": vuln_prof.road_connectivity_index if vuln_prof else None,
                "composite_score": vuln_prof.composite_vulnerability_score if vuln_prof else None,
            },
            "risk": {
                "score": current_risk.score if current_risk else None,
                "band": current_risk.band if current_risk else None,
                "hazard_subscore": current_risk.hazard_subscore if current_risk else None,
                "exposure_subscore": current_risk.exposure_subscore if current_risk else None,
                "vulnerability_subscore": current_risk.vulnerability_subscore if current_risk else None,
                "factors": factors,
            },
            "red_zone": {
                "is_in_red_zone": is_in_red_zone,
                "details": red_zone_info,
            },
            "recent_hazards": recent_hazards,
        },
    )

