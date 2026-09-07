"""API v1 Governance Decisions and Audit Logging router."""

import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.governance import AuditLog, OfficerDecision, User
from app.schemas.common import PaginatedResponse, PaginationMetadata, ResponseEnvelope

governance_router = APIRouter()


class OfficerDecisionCreate(BaseModel):
    """Payload for submitting an officer operational decision."""

    officer_id: Optional[int] = Field(None, description="Officer user ID (defaults to demo officer if unauthenticated)")
    decision_type: str = Field(..., description="e.g. evacuation_order, site_approval, relocation_authorization, zone_declaration")
    target_entity_type: str = Field(..., description="e.g. village, candidate_site, red_zone")
    target_entity_id: int = Field(..., description="Target entity primary key")
    action_taken: str = Field(..., description="Brief action title (e.g. Authorized Relocation Plan)")
    rationale: str = Field(..., min_length=5, description="Officer analytical justification")
    overridden_recommendation: bool = Field(False, description="Whether officer chose to override algorithmic recommendation")
    decision_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")


@governance_router.get(
    "/decisions",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="List officer decisions",
    description="Retrieve paginated log of disaster management officer decisions with justifications.",
)
def list_officer_decisions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    db: Session = Depends(get_db),
):
    """Retrieve logged officer decisions."""
    query = db.query(OfficerDecision)
    if decision_type:
        query = query.filter(OfficerDecision.decision_type == decision_type)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    records = query.order_by(OfficerDecision.decided_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for d in records:
        items.append(
            {
                "id": d.id,
                "officer_id": d.officer_id,
                "officer_name": d.officer.full_name if d.officer else "District Officer",
                "decision_type": d.decision_type,
                "target_entity_type": d.target_entity_type,
                "target_entity_id": d.target_entity_id,
                "action_taken": d.action_taken,
                "rationale": d.rationale,
                "overridden_recommendation": d.overridden_recommendation,
                "metadata": d.decision_metadata_json,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
            }
        )

    return PaginatedResponse(
        success=True,
        data=items,
        pagination=PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@governance_router.post(
    "/decisions",
    response_model=ResponseEnvelope[Dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Record officer decision",
    description="Persist an authoritative officer decision with audit traceability.",
)
def record_officer_decision(
    decision_in: OfficerDecisionCreate,
    db: Session = Depends(get_db),
):
    """Persist new officer decision and write corresponding audit trail."""
    officer_id = decision_in.officer_id
    if not officer_id:
        # Fallback to demo user if available
        first_user = db.query(User).first()
        officer_id = first_user.id if first_user else 1

    dec = OfficerDecision(
        officer_id=officer_id,
        decision_type=decision_in.decision_type,
        target_entity_type=decision_in.target_entity_type,
        target_entity_id=decision_in.target_entity_id,
        action_taken=decision_in.action_taken,
        rationale=decision_in.rationale,
        overridden_recommendation=decision_in.overridden_recommendation,
        decision_metadata_json=decision_in.decision_metadata,
    )
    db.add(dec)
    db.flush()

    # Create immutable audit log entry
    audit = AuditLog(
        user_id=officer_id,
        action=f"OFFICER_DECISION_{decision_in.decision_type.upper()}",
        resource_type=decision_in.target_entity_type,
        resource_id=str(decision_in.target_entity_id),
        payload_after_json={
            "decision_id": dec.id,
            "action_taken": dec.action_taken,
            "rationale": dec.rationale,
            "overridden": dec.overridden_recommendation,
        },
    )
    db.add(audit)
    db.commit()

    return ResponseEnvelope(
        success=True,
        data={
            "id": dec.id,
            "decision_type": dec.decision_type,
            "action_taken": dec.action_taken,
            "decided_at": dec.decided_at.isoformat(),
            "status": "persisted",
        },
    )


# Standalone audit logs router
audit_router = APIRouter()


@audit_router.get(
    "/logs",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="List platform audit logs",
    description="Retrieve immutable chronological audit trail of administrative actions, simulations, and decisions.",
)
def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    action: Optional[str] = Query(None, description="Filter by action keyword"),
    db: Session = Depends(get_db),
):
    """Retrieve immutable platform audit logs."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    records = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for a in records:
        items.append(
            {
                "id": a.id,
                "user_id": a.user_id,
                "user_name": a.user.full_name if a.user else "System",
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "ip_address": a.ip_address,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "payload": a.payload_after_json,
            }
        )

    return PaginatedResponse(
        success=True,
        data=items,
        pagination=PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )
