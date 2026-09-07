"""API v1 Relocation Matching & Assignment router."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles, UserRole, get_current_user
from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.profiles.registry import get_profile
from app.core.relocation.matching import (
    MatchingSiteCandidate,
    RelocationMatchingEngine,
    RelocationMatchingResult,
    VillageDemandInput,
)
from app.models.geographic import Village
from app.models.governance import User
from app.models.relocation import CandidateSite, RelocationAssignment, SiteCapacity
from app.schemas.common import (
    PaginatedResponse,
    PaginationMetadata,
    ResponseEnvelope,
)
from app.schemas.relocation import (
    RelocationAssignmentBatchCreate,
    RelocationAssignmentCreate,
    RelocationAssignmentRead,
    RelocationMatchingRequest,
)

relocation_router = APIRouter()


def _resolve_matching_engine(profile_id: Optional[str]) -> RelocationMatchingEngine:
    """Resolve RelocationMatchingEngine for the specified profile without silent fallback."""
    pid = profile_id or "himalayan_pilot"
    profile = get_profile(pid)
    return RelocationMatchingEngine.from_region_profile(profile)


@relocation_router.post(
    "/recommend",
    response_model=ResponseEnvelope[RelocationMatchingResult],
    summary="Recommend relocation site matching",
    description="Calculate deterministic greedy village-to-site relocation recommendations with full explainability.",
)
@relocation_router.post(
    "/match",
    response_model=ResponseEnvelope[RelocationMatchingResult],
    summary="Evaluate deterministic relocation matching",
    description="Calculate deterministic greedy village-to-site relocation matching with full explainability. Pure evaluation (zero DB mutations).",
)
def evaluate_relocation_matching(
    match_req: RelocationMatchingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute relocation matching evaluation."""
    villages: List[VillageDemandInput] = []
    sites: List[MatchingSiteCandidate] = []

    # 1. Resolve villages
    if match_req.villages:
        villages = match_req.villages
    elif match_req.use_database_villages:
        query = (
            db.query(Village)
            .options(
                joinedload(Village.population_profile),
                joinedload(Village.relocation_priorities),
            )
            .filter(Village.is_active == True)
        )
        if match_req.district_id:
            query = query.join(Village.block).filter(Village.block.has(district_id=match_req.district_id))
        db_villages = query.all()
        villages = [VillageDemandInput.from_village_model(v) for v in db_villages]

    # 2. Resolve candidate sites
    if match_req.sites:
        sites = match_req.sites
    elif match_req.use_database_sites:
        s_query = (
            db.query(CandidateSite)
            .options(
                joinedload(CandidateSite.capacities),
                joinedload(CandidateSite.infrastructures),
            )
            .filter(CandidateSite.status != "rejected")
        )
        if match_req.district_id:
            s_query = s_query.filter(CandidateSite.district_id == match_req.district_id)
        db_sites = s_query.all()
        sites = [MatchingSiteCandidate.from_candidate_site_model(s) for s in db_sites]

    engine = _resolve_matching_engine(match_req.region_profile_id)
    result = engine.match(villages=villages, sites=sites)
    return ResponseEnvelope(success=True, data=result)


@relocation_router.post(
    "/assignments",
    response_model=ResponseEnvelope[RelocationAssignmentRead],
    status_code=status.HTTP_201_CREATED,
    summary="Persist a relocation assignment",
    description="Create and persist a village-to-site relocation assignment. Requires ADMIN or DISTRICT_OFFICER role.",
)
def create_relocation_assignment(
    assignment_in: RelocationAssignmentCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
):
    """Persist a single relocation assignment."""
    # Verify village exists
    village = db.query(Village).filter(Village.id == assignment_in.village_id).first()
    if not village:
        raise NotFoundError(f"Village with ID {assignment_in.village_id} does not exist.")

    # Verify candidate site exists
    site = db.query(CandidateSite).filter(CandidateSite.id == assignment_in.candidate_site_id).first()
    if not site:
        raise NotFoundError(f"Candidate site with ID {assignment_in.candidate_site_id} does not exist.")

    assignment = RelocationAssignment(
        village_id=assignment_in.village_id,
        candidate_site_id=assignment_in.candidate_site_id,
        assigned_households=assignment_in.assigned_households,
        assigned_population=assignment_in.assigned_population or 0,
        status=assignment_in.status or "draft",
        approved_by_officer_id=current_user.id if assignment_in.status == "approved" else None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    read_model = RelocationAssignmentRead(
        id=assignment.id,
        village_id=assignment.village_id,
        village_name=village.name,
        candidate_site_id=assignment.candidate_site_id,
        candidate_site_name=site.name,
        assigned_households=assignment.assigned_households,
        assigned_population=assignment.assigned_population,
        status=assignment.status,
        approved_by_officer_id=assignment.approved_by_officer_id,
        assigned_at=assignment.assigned_at,
        updated_at=assignment.updated_at,
    )
    return ResponseEnvelope(success=True, data=read_model)


@relocation_router.post(
    "/assignments/batch",
    response_model=ResponseEnvelope[List[RelocationAssignmentRead]],
    status_code=status.HTTP_201_CREATED,
    summary="Batch persist relocation assignments",
    description="Persist multiple relocation assignments from a matching run. Optionally commits capacity. Requires ADMIN or DISTRICT_OFFICER role.",
)
def batch_create_relocation_assignments(
    batch_in: RelocationAssignmentBatchCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
):
    """Batch-persist relocation assignments with optional capacity deduction."""
    created_reads: List[RelocationAssignmentRead] = []

    for item in batch_in.assignments:
        village = db.query(Village).filter(Village.id == item.village_id).first()
        if not village:
            raise NotFoundError(f"Village with ID {item.village_id} does not exist.")

        site = db.query(CandidateSite).filter(CandidateSite.id == item.candidate_site_id).first()
        if not site:
            raise NotFoundError(f"Candidate site with ID {item.candidate_site_id} does not exist.")

        assignment = RelocationAssignment(
            village_id=item.village_id,
            candidate_site_id=item.candidate_site_id,
            assigned_households=item.assigned_households,
            assigned_population=item.assigned_population or 0,
            status=item.status or "draft",
            approved_by_officer_id=current_user.id if item.status == "approved" else None,
        )
        db.add(assignment)

        # Optionally commit site capacity
        if batch_in.commit_site_capacity:
            for cap in site.capacities:
                cap.allocated_households = (cap.allocated_households or 0) + item.assigned_households
                cap.available_households = max(0, (cap.available_households or 0) - item.assigned_households)
                if item.assigned_population:
                    cap.allocated_population = (cap.allocated_population or 0) + item.assigned_population
                    cap.available_population = max(0, (cap.available_population or 0) - item.assigned_population)

        db.flush()
        created_reads.append(
            RelocationAssignmentRead(
                id=assignment.id,
                village_id=assignment.village_id,
                village_name=village.name,
                candidate_site_id=assignment.candidate_site_id,
                candidate_site_name=site.name,
                assigned_households=assignment.assigned_households,
                assigned_population=assignment.assigned_population,
                status=assignment.status,
                approved_by_officer_id=assignment.approved_by_officer_id,
                assigned_at=assignment.assigned_at,
                updated_at=assignment.updated_at,
            )
        )

    db.commit()
    return ResponseEnvelope(success=True, data=created_reads)


@relocation_router.get(
    "/assignments",
    response_model=PaginatedResponse[RelocationAssignmentRead],
    summary="List relocation assignments",
    description="Retrieve paginated relocation assignments with optional filters.",
)
def list_relocation_assignments(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    village_id: Optional[int] = Query(None, description="Filter by village ID"),
    candidate_site_id: Optional[int] = Query(None, description="Filter by candidate site ID"),
    status: Optional[str] = Query(None, description="Filter by assignment status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List relocation assignments."""
    query = (
        db.query(RelocationAssignment)
        .options(
            joinedload(RelocationAssignment.village),
            joinedload(RelocationAssignment.site),
        )
    )

    if village_id is not None:
        query = query.filter(RelocationAssignment.village_id == village_id)
    if candidate_site_id is not None:
        query = query.filter(RelocationAssignment.candidate_site_id == candidate_site_id)
    if status is not None:
        query = query.filter(RelocationAssignment.status == status.lower().strip())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    records = (
        query.order_by(RelocationAssignment.assigned_at.desc(), RelocationAssignment.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        RelocationAssignmentRead(
            id=r.id,
            village_id=r.village_id,
            village_name=r.village.name if r.village else None,
            candidate_site_id=r.candidate_site_id,
            candidate_site_name=r.site.name if r.site else None,
            assigned_households=r.assigned_households,
            assigned_population=r.assigned_population,
            status=r.status,
            approved_by_officer_id=r.approved_by_officer_id,
            assigned_at=r.assigned_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]

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


@relocation_router.get(
    "/assignments/{id}",
    response_model=ResponseEnvelope[RelocationAssignmentRead],
    summary="Get relocation assignment by ID",
    description="Retrieve details of a single relocation assignment by ID.",
)
def get_relocation_assignment(
    id: int = Path(..., ge=1, description="Relocation assignment ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve relocation assignment by ID."""
    assignment = (
        db.query(RelocationAssignment)
        .options(
            joinedload(RelocationAssignment.village),
            joinedload(RelocationAssignment.site),
        )
        .filter(RelocationAssignment.id == id)
        .first()
    )

    if not assignment:
        raise NotFoundError(f"Relocation assignment with ID {id} was not found.")

    read_model = RelocationAssignmentRead(
        id=assignment.id,
        village_id=assignment.village_id,
        village_name=assignment.village.name if assignment.village else None,
        candidate_site_id=assignment.candidate_site_id,
        candidate_site_name=assignment.site.name if assignment.site else None,
        assigned_households=assignment.assigned_households,
        assigned_population=assignment.assigned_population,
        status=assignment.status,
        approved_by_officer_id=assignment.approved_by_officer_id,
        assigned_at=assignment.assigned_at,
        updated_at=assignment.updated_at,
    )
    return ResponseEnvelope(success=True, data=read_model)
