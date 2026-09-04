"""Risk Normalization Engine package for RakshakGIS."""

from app.core.risk.normalization.contracts import (
    CategoricalSeverityPolicy,
    FactorCategory,
    LinearRangeConfig,
    NormalizationExplainability,
    NormalizationMethod,
    NormalizationResult,
    NormalizationStatus,
    PiecewiseThresholdConfig,
)
from app.core.risk.normalization.engine import RiskNormalizationEngine
from app.core.risk.normalization.errors import (
    InvalidInputError,
    NormalizationConfigError,
    NormalizationError,
    UnsupportedFactorError,
)
from app.core.risk.normalization.methods import (
    categorical_severity_normalize,
    linear_normalize,
    piecewise_threshold_normalize,
)

__all__ = [
    "CategoricalSeverityPolicy",
    "FactorCategory",
    "InvalidInputError",
    "LinearRangeConfig",
    "NormalizationConfigError",
    "NormalizationError",
    "NormalizationExplainability",
    "NormalizationMethod",
    "NormalizationResult",
    "NormalizationStatus",
    "PiecewiseThresholdConfig",
    "RiskNormalizationEngine",
    "UnsupportedFactorError",
    "categorical_severity_normalize",
    "linear_normalize",
    "piecewise_threshold_normalize",
]
