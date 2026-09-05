"""Public interfaces and schemas for the Multi-Criteria Site Suitability Engine."""

from app.core.relocation.suitability.contracts import (
    ConstraintEvaluation,
    CriterionScoreResult,
    CriterionType,
    HardConstraintType,
    SiteSuitabilityInput,
    SiteSuitabilityResult,
    SuitabilityDecision,
    SuitabilityThresholdsConfig,
    SuitabilityWeightsConfig,
)
from app.core.relocation.suitability.engine import SiteSuitabilityEngine
from app.core.relocation.suitability.errors import (
    HardConstraintError,
    InvalidSiteDataError,
    MissingCriticalAttributeError,
    SiteSuitabilityError,
    SuitabilityConfigError,
)

__all__ = [
    "CriterionType",
    "SuitabilityDecision",
    "HardConstraintType",
    "ConstraintEvaluation",
    "CriterionScoreResult",
    "SuitabilityWeightsConfig",
    "SuitabilityThresholdsConfig",
    "SiteSuitabilityInput",
    "SiteSuitabilityResult",
    "SiteSuitabilityEngine",
    "SiteSuitabilityError",
    "InvalidSiteDataError",
    "MissingCriticalAttributeError",
    "SuitabilityConfigError",
    "HardConstraintError",
]
