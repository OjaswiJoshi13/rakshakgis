"""Relocation Matching & Assignment Engine for RakshakGIS (Chunk M4-04)."""

from app.core.relocation.matching.contracts import (
    AssignmentStatus,
    CandidateEvaluationAudit,
    MatchingAlgorithmType,
    MatchingSiteCandidate,
    RejectionReasonCode,
    RelocationMatchingResult,
    VillageAssignmentResult,
    VillageDemandInput,
)
from app.core.relocation.matching.engine import RelocationMatchingEngine
from app.core.relocation.matching.errors import (
    InvalidMatchingInputError,
    MatchingConfigurationError,
    RelocationMatchingError,
    SiteCapacityExhaustedError,
)
from app.core.relocation.matching.ranking import (
    calculate_haversine_distance_km,
    compute_matching_rank_score,
    compute_proximity_score,
    sort_feasible_candidates,
)

__all__ = [
    "RelocationMatchingEngine",
    "VillageDemandInput",
    "MatchingSiteCandidate",
    "VillageAssignmentResult",
    "CandidateEvaluationAudit",
    "RelocationMatchingResult",
    "AssignmentStatus",
    "RejectionReasonCode",
    "MatchingAlgorithmType",
    "RelocationMatchingError",
    "InvalidMatchingInputError",
    "MatchingConfigurationError",
    "SiteCapacityExhaustedError",
    "calculate_haversine_distance_km",
    "compute_proximity_score",
    "compute_matching_rank_score",
    "sort_feasible_candidates",
]
