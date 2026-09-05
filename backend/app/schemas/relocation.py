"""Pydantic request and response schemas for Relocation Matching & Assignments API (Chunk M4-04)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.relocation.matching.contracts import (
    MatchingSiteCandidate,
    RelocationMatchingResult,
    VillageDemandInput,
)


class RelocationMatchingRequest(BaseModel):
    """Request payload for evaluating relocation matching."""

    villages: Optional[List[VillageDemandInput]] = Field(
        None, description="List of villages to match; if omitted or empty and use_database_villages=True, loaded from DB."
    )
    sites: Optional[List[MatchingSiteCandidate]] = Field(
        None, description="List of candidate sites to match against; if omitted and use_database_sites=True, loaded from DB."
    )
    use_database_villages: bool = Field(
        default=False, description="If True, loads prioritized villages from database when villages list is empty."
    )
    use_database_sites: bool = Field(
        default=False, description="If True, loads candidate sites from database when sites list is empty."
    )
    region_profile_id: Optional[str] = Field(
        default="himalayan_pilot", description="Regional configuration profile identifier."
    )
    district_id: Optional[int] = Field(
        default=None, description="Optional district filter when querying database records."
    )


class RelocationAssignmentCreate(BaseModel):
    """Payload to persist a relocation assignment."""

    village_id: int = Field(..., ge=1, description="Database ID of the affected village")
    candidate_site_id: int = Field(..., ge=1, description="Database ID of the assigned candidate site")
    assigned_households: int = Field(..., ge=0, description="Allocated households")
    assigned_population: Optional[int] = Field(None, ge=0, description="Allocated population count")
    status: Optional[str] = Field("draft", description="Assignment status: draft, approved, in_transit, completed, cancelled")


class RelocationAssignmentBatchCreate(BaseModel):
    """Payload to batch-persist relocation assignments from a matching run."""

    assignments: List[RelocationAssignmentCreate] = Field(..., min_length=1)
    commit_site_capacity: bool = Field(
        default=False,
        description="If True, increments site_capacities.allocated_households and decrements available_households in DB.",
    )


class RelocationAssignmentRead(BaseModel):
    """Response schema for a persisted relocation assignment."""

    id: Optional[int] = None
    village_id: int
    village_name: Optional[str] = None
    candidate_site_id: int
    candidate_site_name: Optional[str] = None
    assigned_households: int
    assigned_population: int
    status: str
    approved_by_officer_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
