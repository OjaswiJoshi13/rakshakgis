"""Typed schemas, enumerations, and contracts for the Risk Normalization Engine."""

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.risk.normalization.errors import NormalizationConfigError
from app.data.providers.contracts import ProviderProvenance


class FactorCategory(str, Enum):
    """Categorical factor/hazard types supported by the normalization layer."""

    RAINFALL = "rainfall"
    FLOOD = "flood"
    LANDSLIDE = "landslide"
    SEISMIC = "seismic"
    HAZARD_OBSERVATION = "hazard_observation"
    POPULATION_EXPOSURE = "population_exposure"


class NormalizationMethod(str, Enum):
    """Mathematical or algorithmic method applied to transform observations to 0-100."""

    LINEAR = "linear"
    THRESHOLD_PIECEWISE = "threshold_piecewise"
    CATEGORICAL_SEVERITY = "categorical_severity"
    DEFERRED = "deferred"


class NormalizationStatus(str, Enum):
    """Execution status of the normalization process for a given record."""

    NORMALIZED = "normalized"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    DEFERRED = "deferred"


# =====================================================================
# Configuration and Policy Contracts
# =====================================================================


class LinearRangeConfig(BaseModel):
    """Configuration for two-point linear range normalization: min -> 0, max -> 100."""

    model_config = ConfigDict(frozen=True)

    min_value: float = Field(..., description="Observation value that maps to 0.0")
    max_value: float = Field(..., description="Observation value that maps to 100.0")
    clamp_min: bool = Field(default=True, description="Whether to clamp values below min_value to 0.0")
    clamp_max: bool = Field(default=True, description="Whether to clamp values above max_value to 100.0")

    @model_validator(mode="after")
    def validate_range(self) -> "LinearRangeConfig":
        if math.isnan(self.min_value) or math.isnan(self.max_value):
            raise NormalizationConfigError("Linear range configuration bounds cannot be NaN.")
        if math.isinf(self.min_value) or math.isinf(self.max_value):
            raise NormalizationConfigError("Linear range configuration bounds cannot be infinite.")
        if self.max_value <= self.min_value:
            raise NormalizationConfigError(
                f"Invalid linear configuration range: max_value ({self.max_value}) "
                f"must be strictly greater than min_value ({self.min_value})."
            )
        return self


class PiecewiseThresholdConfig(BaseModel):
    """Configuration for piecewise linear interpolation through domain benchmark thresholds."""

    model_config = ConfigDict(frozen=True)

    benchmarks: List[Tuple[float, float]] = Field(
        ...,
        description="Ordered list of (raw_threshold_value, normalized_score) benchmark points.",
    )

    @model_validator(mode="after")
    def validate_benchmarks(self) -> "PiecewiseThresholdConfig":
        if len(self.benchmarks) < 2:
            raise NormalizationConfigError("Piecewise configuration requires at least 2 benchmark points.")

        for i, (raw_val, norm_val) in enumerate(self.benchmarks):
            if math.isnan(raw_val) or math.isnan(norm_val) or math.isinf(raw_val) or math.isinf(norm_val):
                raise NormalizationConfigError(
                    f"Piecewise benchmark at index {i} ({raw_val}, {norm_val}) contains NaN or Inf."
                )
            if not (0.0 <= norm_val <= 100.0):
                raise NormalizationConfigError(
                    f"Benchmark normalized target {norm_val} at index {i} out of bounds [0.0, 100.0]."
                )
            if i > 0:
                prev_raw, prev_norm = self.benchmarks[i - 1]
                if raw_val <= prev_raw:
                    raise NormalizationConfigError(
                        f"Piecewise benchmarks must be strictly increasing in input threshold: "
                        f"{raw_val} <= {prev_raw} at index {i}."
                    )
                if norm_val < prev_norm:
                    raise NormalizationConfigError(
                        f"Piecewise benchmarks must be monotonic non-decreasing in normalized score: "
                        f"{norm_val} < {prev_norm} at index {i}."
                    )
        return self


class CategoricalSeverityPolicy(BaseModel):
    """Policy mapping qualitative severity labels to deterministic 0.0 - 100.0 values."""

    model_config = ConfigDict(frozen=True)

    mappings: Dict[str, float] = Field(
        default_factory=lambda: {
            "low": 20.0,
            "moderate": 40.0,
            "high": 65.0,
            "very_high": 85.0,
            "critical": 100.0,
        },
        description="Case-insensitive severity label to [0.0, 100.0] numerical factor mapping.",
    )

    @model_validator(mode="after")
    def validate_mappings(self) -> "CategoricalSeverityPolicy":
        for k, v in self.mappings.items():
            if math.isnan(v) or math.isinf(v) or not (0.0 <= v <= 100.0):
                raise NormalizationConfigError(
                    f"Severity mapping for '{k}' must be a finite float in [0.0, 100.0], got {v}."
                )
        return self


# =====================================================================
# Explainability and Result Contracts
# =====================================================================


class NormalizationExplainability(BaseModel):
    """Structured explainability metadata for downstream risk auditability (M3-06 / M3-08)."""

    model_config = ConfigDict(frozen=True)

    method: NormalizationMethod
    parameters_used: Dict[str, Any] = Field(default_factory=dict)
    thresholds_applied: Optional[Dict[str, float]] = None
    input_domain_range: Optional[Tuple[float, float]] = None
    formula_description: str
    clamping_reason: Optional[str] = None


class NormalizationResult(BaseModel):
    """Strongly typed normalized factor envelope returned by the Risk Normalization Engine.

    Guarantees:
    - Every valid normalized_value satisfies: 0.0 <= normalized_value <= 100.0
    - Missing or unavailable records NEVER produce a 0.0 score (status=UNAVAILABLE, normalized_value=None).
    - Preserves raw input value, source record identity, clamping status, and provenance.
    """

    model_config = ConfigDict(frozen=True)

    record_id: Optional[str] = None
    factor_category: FactorCategory
    status: NormalizationStatus
    raw_input_value: Optional[Union[float, int, str]] = None
    normalized_value: Optional[float] = None
    was_clamped: bool = False
    is_unknown_or_unavailable: bool = False
    diagnostic_message: Optional[str] = None
    explainability: NormalizationExplainability
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None

    @model_validator(mode="after")
    def validate_contract_integrity(self) -> "NormalizationResult":
        # 1. Check normalized value bounds and finiteness
        if self.normalized_value is not None:
            if math.isnan(self.normalized_value) or math.isinf(self.normalized_value):
                raise ValueError(f"Normalized factor must not be NaN or Inf, got {self.normalized_value}")
            if not (0.0 <= self.normalized_value <= 100.0):
                raise ValueError(
                    f"Normalized factor must be in range [0.0, 100.0], got {self.normalized_value}"
                )

        # 2. Safety critical check: UNAVAILABLE or INVALID must NEVER have a numerical score
        if self.status in (NormalizationStatus.UNAVAILABLE, NormalizationStatus.INVALID):
            if self.normalized_value is not None:
                raise ValueError(
                    f"Safety violation: Status is {self.status.value} but normalized_value is {self.normalized_value}. "
                    f"Missing/unknown inputs must never be assigned a numerical score."
                )
            if self.status == NormalizationStatus.UNAVAILABLE and not self.is_unknown_or_unavailable:
                raise ValueError("Records with status UNAVAILABLE must set is_unknown_or_unavailable=True.")

        return self
