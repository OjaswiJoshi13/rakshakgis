"""Risk engine and risk modeling module for RakshakGIS.

Note: M3-05 provides the Risk Normalization Engine only.
Multi-hazard composite risk calculation is deferred to M3-06.
"""

from app.core.risk.normalization import (
    CategoricalSeverityPolicy,
    FactorCategory,
    LinearRangeConfig,
    NormalizationError,
    NormalizationExplainability,
    NormalizationMethod,
    NormalizationResult,
    NormalizationStatus,
    PiecewiseThresholdConfig,
    RiskNormalizationEngine,
)

__all__ = [
    "CategoricalSeverityPolicy",
    "FactorCategory",
    "LinearRangeConfig",
    "NormalizationError",
    "NormalizationExplainability",
    "NormalizationMethod",
    "NormalizationResult",
    "NormalizationStatus",
    "PiecewiseThresholdConfig",
    "RiskNormalizationEngine",
]
