"""Risk Explainability & Factor Contribution Package (Chunk M3-08)."""

from app.core.risk.explainability.contracts import (
    FACTOR_METADATA,
    CompositeRiskExplanation,
    FactorContributionDetail,
    FactorRanking,
    RiskClassificationSummary,
)
from app.core.risk.explainability.engine import RiskExplainabilityEngine
from app.core.risk.explainability.errors import (
    IncompatibleClassificationError,
    RiskExplainabilityError,
    UncomputableExplanationError,
)

__all__ = [
    "CompositeRiskExplanation",
    "FACTOR_METADATA",
    "FactorContributionDetail",
    "FactorRanking",
    "IncompatibleClassificationError",
    "RiskClassificationSummary",
    "RiskExplainabilityEngine",
    "RiskExplainabilityError",
    "UncomputableExplanationError",
]
