"""API v1 Action Plan and Analytical Reports generator router."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.geographic import Village
from app.models.governance import OfficerDecision
from app.models.relocation import CandidateSite, RelocationAssignment
from app.models.risk import RedZone, RiskScore
from app.schemas.common import ResponseEnvelope

reports_router = APIRouter()


@reports_router.get(
    "/{type}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Generate disaster response reports",
    description="Generate structured audit reports: action_plan, risk_assessment, site_dossier, or audit_report.",
)
def generate_report(
    type: str = Path(..., description="Report type: action_plan, risk_assessment, site_dossier, audit_report"),
    region_id: Optional[str] = Query(None, description="Region code or numeric ID"),
    db: Session = Depends(get_db),
):
    """Generate structured analytical disaster management report."""
    report_type = type.lower().strip()
    generated_at = datetime.now(timezone.utc).isoformat()

    if report_type == "action_plan":
        # Evacuation and relocation action plan
        villages = (
            db.query(Village)
            .options(
                joinedload(Village.population_profile),
                joinedload(Village.risk_scores),
            )
            .limit(50)
            .all()
        )
        high_risk = []
        for v in villages:
            curr = next((r for r in v.risk_scores if r.is_current), None)
            if curr and curr.band in ("HIGH", "VERY_HIGH", "CRITICAL"):
                high_risk.append(
                    {
                        "village_id": v.id,
                        "name": v.name,
                        "risk_score": curr.score,
                        "risk_band": curr.band,
                        "population": v.population_profile.total_population if v.population_profile else None,
                        "households": v.population_profile.households if v.population_profile else None,
                    }
                )

        assignments = db.query(RelocationAssignment).limit(20).all()
        reloc_summary = [
            {
                "assignment_id": a.id,
                "village_id": a.village_id,
                "site_id": a.site_id,
                "allocated_households": a.allocated_households,
                "allocated_population": a.allocated_population,
                "status": a.status,
            }
            for a in assignments
        ]

        return ResponseEnvelope(
            success=True,
            data={
                "report_title": "District Disaster Evacuation & Relocation Action Plan",
                "report_type": "action_plan",
                "generated_at": generated_at,
                "authoritative_status": "OFFICIAL_RECORD",
                "high_risk_villages_count": len(high_risk),
                "high_risk_habitations": high_risk,
                "active_relocation_assignments": reloc_summary,
                "recommended_actions": [
                    "Immediate evacuation orders for villages categorized under CRITICAL risk band.",
                    "Provision emergency transit shelters at designated Candidate Sites.",
                    "Deploy seismic and hydrological field telemetry for continuous early warning monitoring.",
                ],
            },
        )

    elif report_type == "risk_assessment":
        villages = db.query(Village).options(joinedload(Village.risk_scores)).all()
        bands = {"SAFE": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0, "CRITICAL": 0}
        for v in villages:
            curr = next((r for r in v.risk_scores if r.is_current), None)
            b = (curr.band if curr else "MODERATE").upper()
            if b in bands:
                bands[b] += 1

        return ResponseEnvelope(
            success=True,
            data={
                "report_title": "Multi-Hazard Risk Assessment and Vulnerability Dossier",
                "report_type": "risk_assessment",
                "generated_at": generated_at,
                "total_villages_evaluated": len(villages),
                "risk_distribution": bands,
                "methodology": "Multi-hazard composite risk calculation based on normalized hazard severity, slope, flood, and vulnerability factors.",
            },
        )

    elif report_type == "site_dossier":
        sites = db.query(CandidateSite).options(joinedload(CandidateSite.capacities)).all()
        site_summaries = []
        for s in sites:
            cap = s.capacities[0] if s.capacities else None
            site_summaries.append(
                {
                    "site_id": s.id,
                    "name": s.name,
                    "suitability_score": s.suitability_score,
                    "housing_capacity": cap.max_households if cap else None,
                    "total_capacity": cap.max_population if cap else None,
                    "current_occupancy": cap.allocated_population if cap else 0,
                    "status": s.status,
                }
            )

        return ResponseEnvelope(
            success=True,
            data={
                "report_title": "Candidate Relocation Sites Carrying Capacity Dossier",
                "report_type": "site_dossier",
                "generated_at": generated_at,
                "total_candidate_sites": len(sites),
                "sites": site_summaries,
            },
        )

    elif report_type == "audit_report":
        decisions = db.query(OfficerDecision).order_by(OfficerDecision.decided_at.desc()).limit(50).all()
        dec_list = [
            {
                "id": d.id,
                "decision_type": d.decision_type,
                "target_entity": f"{d.target_entity_type} #{d.target_entity_id}",
                "action_taken": d.action_taken,
                "rationale": d.rationale,
                "overridden_recommendation": d.overridden_recommendation,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
            }
            for d in decisions
        ]

        return ResponseEnvelope(
            success=True,
            data={
                "report_title": "Platform Governance and Officer Decision Audit Trail",
                "report_type": "audit_report",
                "generated_at": generated_at,
                "total_decisions_logged": len(decisions),
                "audit_records": dec_list,
            },
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown report type '{type}'. Valid types: action_plan, risk_assessment, site_dossier, audit_report",
        )
