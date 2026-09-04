"""Multi-Hazard Risk Computation package for RakshakGIS."""

from app.core.risk.computation.contracts import (
    CompositeRiskExplainability,
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorInput,
    RiskFactorType,
    RiskWeightsConfig,
)
from app.core.risk.computation.engine import REQUIRED_FACTORS, MultiHazardRiskEngine
from app.core.risk.computation.errors import (
    InsufficientFactorsError,
    InvalidFactorValueError,
    RiskComputationError,
    WeightConfigurationError,
)

__all__ = [
    "CompositeRiskExplainability",
    "CompositeRiskResult",
    "InsufficientFactorsError",
    "InvalidFactorValueError",
    "MultiHazardRiskEngine",
    "REQUIRED_FACTORS",
    "RiskComputationError",
    "RiskComputationStatus",
    "RiskFactorInput",
    "RiskFactorType",
    "RiskWeightsConfig",
    "WeightConfigurationError",
]
