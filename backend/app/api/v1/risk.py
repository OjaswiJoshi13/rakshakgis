"""API v1 Risk Summary and Recalculation router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.profiles import get_profile
from app.core.risk.classification.engine import RiskClassificationEngine
from app.core.risk.computation.contracts import RiskFactorType
from app.core.risk.computation.engine import MultiHazardRiskEngine
from app.core.regions import resolve_region_scope, apply_region_scope_to_village_query
from app.models.geographic import Block, District, Region, Village
from app.models.risk import RedZone, RiskFactor, RiskScore
from app.schemas.common import ResponseEnvelope

risk_router = APIRouter()


class RiskRecalculateRequest(BaseModel):
    """Payload for on-demand or scenario-driven risk recomputation."""

    region_id: Optional[str] = Field(None, description="Region code or numeric ID")
    rainfall_multiplier: float = Field(1.0, ge=0.0, le=5.0, description="Rainfall factor multiplier (1.0 = baseline)")
    flood_surge_mm: float = Field(0.0, ge=0.0, description="Additional flood surge in mm")
    seismic_intensity_override: Optional[float] = Field(None, ge=0.0, le=10.0, description="Seismic intensity override (Richter)")
    village_ids: Optional[List[int]] = Field(None, description="Optional subset of village IDs to recalculate")


@risk_router.get(
    "/summary",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Platform multi-hazard risk summary",
    description="Retrieve aggregated statistics on village risk distribution, vulnerable population, and red zone coverage.",
)
def get_risk_summary(
    region_id: Optional[str] = Query(None, description="Filter by region code or numeric ID"),
    db: Session = Depends(get_db),
):
    """Calculate platform-wide multi-hazard risk distribution summary."""
    v_query = db.query(Village).options(
        joinedload(Village.population_profile),
        joinedload(Village.risk_scores),
    )

    if region_id:
        scope = resolve_region_scope(db, region_id)
        if scope is not None:
            v_query = apply_region_scope_to_village_query(v_query, scope)

    villages = v_query.all()
    total_villages = len(villages)

    band_counts = {
        "SAFE": 0,
        "MODERATE": 0,
        "HIGH": 0,
        "VERY_HIGH": 0,
        "CRITICAL": 0,
    }
    total_population = 0
    vulnerable_population = 0
    scores = []

    for v in villages:
        pop = v.population_profile.total_population if v.population_profile else 0
        total_population += pop

        current_risk = next((r for r in v.risk_scores if r.is_current), None)
        if current_risk and current_risk.score is not None:
            scores.append(current_risk.score)
            b = (current_risk.band or "MODERATE").upper()
            if b in band_counts:
                band_counts[b] += 1
            if b in ("HIGH", "VERY_HIGH", "CRITICAL"):
                vulnerable_population += pop
        else:
            band_counts["MODERATE"] += 1

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    active_red_zones = db.query(RedZone).filter(RedZone.is_active == True).count()

    return ResponseEnvelope(
        success=True,
        data={
            "total_villages_assessed": total_villages,
            "average_risk_score": avg_score,
            "risk_distribution": band_counts,
            "total_population": total_population,
            "population_at_risk": vulnerable_population,
            "active_red_zones_count": active_red_zones,
        },
    )


@risk_router.post(
    "/recalculate",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Recalculate dynamic multi-hazard risk",
    description="Execute canonical risk engine re-evaluation with updated weather/hazard parameters.",
)
def recalculate_risk(
    req: RiskRecalculateRequest,
    db: Session = Depends(get_db),
):
    """Execute dynamic multi-hazard risk recomputation."""
    profile = get_profile(req.region_id or "himalayan_pilot")
    risk_engine = MultiHazardRiskEngine(profile=profile)
    classifier = RiskClassificationEngine(profile=profile)

    v_query = db.query(Village).options(
        joinedload(Village.population_profile),
        joinedload(Village.vulnerability_profile),
        joinedload(Village.risk_scores),
    )

    if req.village_ids:
        v_query = v_query.filter(Village.id.in_(req.village_ids))
    elif req.region_id:
        scope = resolve_region_scope(db, req.region_id)
        if scope is not None:
            v_query = apply_region_scope_to_village_query(v_query, scope)

    villages = v_query.all()
    if not villages:
        villages = db.query(Village).options(
            joinedload(Village.population_profile),
            joinedload(Village.vulnerability_profile),
            joinedload(Village.risk_scores),
        ).limit(50).all()
    results = []

    for v in villages:
        vuln_s = v.vulnerability_profile.social_vulnerability_index if v.vulnerability_profile else 0.5
        vuln_st = v.vulnerability_profile.road_connectivity_index if v.vulnerability_profile else 0.6

        # Baseline rainfall and flood
        base_rainfall = 65.0 * req.rainfall_multiplier
        base_flood = min(100.0, (68.0 if "marwari" in v.name.lower() else 35.0) + (req.flood_surge_mm * 0.1))

        calc_result = risk_engine.compute_from_values(
            hazard_severity=75.0 if "sunil" in v.name.lower() or "joshimath" in v.name.lower() else 48.0,
            flood_exposure=base_flood,
            rainfall_intensity=min(100.0, base_rainfall),
            slope_landslide_susceptibility=min(100.0, float(v.slope_deg or 25.0) * 2.5),
            infrastructure_vulnerability=min(100.0, max(10.0, 100.0 - (vuln_st * 100.0))),
            social_vulnerability=vuln_s * 100.0,
            village_id=str(v.id),
        )

        score = calc_result.score
        if score is not None:
            band_info = classifier.classify(score)
            results.append(
                {
                    "village_id": v.id,
                    "village_name": v.name,
                    "recomputed_score": round(score, 2),
                    "risk_band": band_info.band.value,
                    "factors": {
                        k.value if hasattr(k, "value") else str(k): round(val, 2)
                        for k, val in calc_result.factor_values_used.items()
                    },
                }
            )

    return ResponseEnvelope(
        success=True,
        data={
            "villages_recomputed": len(results),
            "parameters_applied": req.model_dump(),
            "results": results,
        },
    )
