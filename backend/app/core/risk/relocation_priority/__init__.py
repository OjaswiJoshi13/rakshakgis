"""Relocation Priority Scoring package for RakshakGIS (Chunk M3-12)."""

from app.core.profiles.models import RelocationPriorityBand
from app.core.risk.relocation_priority.contracts import (
    PriorityFactorDetail,
    PriorityFactorType,
    PriorityScoreBandsConfig,
    RelocationPriorityExplainability,
    RelocationPriorityInput,
    RelocationPriorityResult,
    RelocationPriorityStatus,
    RelocationPriorityWeightsConfig,
)
from app.core.risk.relocation_priority.engine import RelocationPriorityEngine
from app.core.risk.relocation_priority.errors import (
    InsufficientPriorityDataError,
    InvalidPriorityDataError,
    PriorityConfigError,
    RelocationPriorityError,
)

__all__ = [
    # Engine
    "RelocationPriorityEngine",
    # Enums
    "RelocationPriorityStatus",
    "PriorityFactorType",
    "RelocationPriorityBand",
    # Configuration
    "RelocationPriorityWeightsConfig",
    "PriorityScoreBandsConfig",
    # Contracts & Envelopes
    "RelocationPriorityInput",
    "PriorityFactorDetail",
    "RelocationPriorityExplainability",
    "RelocationPriorityResult",
    # Exceptions
    "RelocationPriorityError",
    "InvalidPriorityDataError",
    "InsufficientPriorityDataError",
    "PriorityConfigError",
]
