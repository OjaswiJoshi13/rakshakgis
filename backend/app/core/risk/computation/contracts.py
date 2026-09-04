"""Typed schemas, enumerations, and contracts for the Multi-Hazard Risk Computation Engine."""

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.profiles.models import CompositeRiskWeights, RegionProfile
from app.core.risk.computation.errors import InvalidFactorValueError, WeightConfigurationError
from app.core.risk.normalization.contracts import NormalizationResult, NormalizationStatus
from app.data.providers.contracts import ProviderProvenance


class RiskFactorType(str, Enum):
    """Authoritative six hazard and vulnerability factors defined for multi-hazard risk scoring."""

    HAZARD_SEVERITY = "hazard_severity"                         # H (weight 0.30)
    FLOOD_EXPOSURE = "flood_exposure"                           # F (weight 0.20)
    RAINFALL_INTENSITY = "rainfall_intensity"                   # R (weight 0.15)
    SLOPE_LANDSLIDE_SUSCEPTIBILITY = "slope_landslide_susceptibility"  # S (weight 0.15)
    INFRASTRUCTURE_VULNERABILITY = "infrastructure_vulnerability"      # D (weight 0.10)
    SOCIAL_VULNERABILITY = "social_vulnerability"               # V (weight 0.10)

    @property
    def symbol(self) -> str:
        """Single-letter mathematical formula notation."""
        mapping = {
            RiskFactorType.HAZARD_SEVERITY: "H",
            RiskFactorType.FLOOD_EXPOSURE: "F",
            RiskFactorType.RAINFALL_INTENSITY: "R",
            RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: "S",
            RiskFactorType.INFRASTRUCTURE_VULNERABILITY: "D",
            RiskFactorType.SOCIAL_VULNERABILITY: "V",
        }
        return mapping[self]


class RiskComputationStatus(str, Enum):
    """Execution status of the composite multi-hazard risk computation."""

    COMPUTED = "computed"
    INSUFFICIENT_FACTORS = "insufficient_factors"
    INVALID_INPUT = "invalid_input"


# =====================================================================
# Configuration Contracts
# =====================================================================


class RiskWeightsConfig(BaseModel):
    """Authoritative weights configuration for multi-hazard risk computation.

    Formula:
      Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V
    All weights must be non-negative and sum strictly to 1.0 within tolerance.
    """

    model_config = ConfigDict(frozen=True)

    hazard_severity: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for H")
    flood_exposure: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for F")
    rainfall_intensity: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for R")
    slope_landslide_susceptibility: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for S")
    infrastructure_vulnerability: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for D")
    social_vulnerability: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for V")

    @property
    def w_h(self) -> float:
        return self.hazard_severity

    @property
    def w_f(self) -> float:
        return self.flood_exposure

    @property
    def w_r(self) -> float:
        return self.rainfall_intensity

    @property
    def w_s(self) -> float:
        return self.slope_landslide_susceptibility

    @property
    def w_d(self) -> float:
        return self.infrastructure_vulnerability

    @property
    def w_v(self) -> float:
        return self.social_vulnerability

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "RiskWeightsConfig":
        total = (
            self.hazard_severity
            + self.flood_exposure
            + self.rainfall_intensity
            + self.slope_landslide_susceptibility
            + self.infrastructure_vulnerability
            + self.social_vulnerability
        )
        if not math.isclose(total, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise WeightConfigurationError(
                f"Multi-hazard risk weights must sum to 1.0, got {total:.6f}."
            )
        return self

    def as_dict(self) -> Dict[RiskFactorType, float]:
        """Return factor type to weight dictionary."""
        return {
            RiskFactorType.HAZARD_SEVERITY: self.hazard_severity,
            RiskFactorType.FLOOD_EXPOSURE: self.flood_exposure,
            RiskFactorType.RAINFALL_INTENSITY: self.rainfall_intensity,
            RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: self.slope_landslide_susceptibility,
            RiskFactorType.INFRASTRUCTURE_VULNERABILITY: self.infrastructure_vulnerability,
            RiskFactorType.SOCIAL_VULNERABILITY: self.social_vulnerability,
        }

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "RiskWeightsConfig":
        """Initialize weights from an M3-01 RegionProfile without duplicating configuration."""
        pw: CompositeRiskWeights = profile.risk_weights
        return cls(
            hazard_severity=pw.hazard_weight,
            flood_exposure=pw.flood_weight,
            rainfall_intensity=pw.rainfall_weight,
            slope_landslide_susceptibility=pw.seismic_weight,
            infrastructure_vulnerability=pw.demographic_weight,
            social_vulnerability=pw.vulnerability_weight,
        )


# =====================================================================
# Factor Input Contract
# =====================================================================


class RiskFactorInput(BaseModel):
    """Input encapsulation for a single factor consumed by the multi-hazard risk engine."""

    model_config = ConfigDict(frozen=True)

    factor_type: RiskFactorType
    normalized_value: Optional[float] = None
    is_available: bool = True
    raw_value: Optional[Union[float, int, str]] = None
    source_record_id: Optional[str] = None
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_normalized_factor(self) -> "RiskFactorInput":
        if self.normalized_value is not None:
            if math.isnan(self.normalized_value) or math.isinf(self.normalized_value):
                raise InvalidFactorValueError(
                    f"Factor {self.factor_type.value} normalized value cannot be NaN or infinite."
                )
            if not (0.0 <= self.normalized_value <= 100.0):
                raise InvalidFactorValueError(
                    f"Factor {self.factor_type.value} normalized value {self.normalized_value} "
                    f"out of valid range [0.0, 100.0]."
                )
        if not self.is_available and self.normalized_value is not None:
            raise InvalidFactorValueError(
                f"Factor {self.factor_type.value} is marked is_available=False but has normalized_value={self.normalized_value}. "
                f"Unavailable factors must have normalized_value=None."
            )
        return self

    @classmethod
    def from_value(
        cls,
        factor_type: RiskFactorType,
        value: Optional[float],
        raw_value: Optional[Union[float, int, str]] = None,
        source_record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "RiskFactorInput":
        """Construct factor input from a numeric value or None."""
        if value is None:
            return cls(
                factor_type=factor_type,
                normalized_value=None,
                is_available=False,
                raw_value=raw_value,
                source_record_id=source_record_id,
                provenance=provenance,
                metadata=metadata,
            )
        return cls(
            factor_type=factor_type,
            normalized_value=float(value),
            is_available=True,
            raw_value=raw_value if raw_value is not None else value,
            source_record_id=source_record_id,
            provenance=provenance,
            metadata=metadata,
        )

    @classmethod
    def from_normalization_result(
        cls,
        factor_type: RiskFactorType,
        result: NormalizationResult,
    ) -> "RiskFactorInput":
        """Construct factor input directly from an M3-05 NormalizationResult."""
        is_avail = (
            result.status == NormalizationStatus.NORMALIZED
            and result.normalized_value is not None
            and not result.is_unknown_or_unavailable
        )
        return cls(
            factor_type=factor_type,
            normalized_value=result.normalized_value if is_avail else None,
            is_available=is_avail,
            raw_value=result.raw_input_value,
            source_record_id=result.record_id,
            provenance=result.provenance,
            metadata={
                "status": result.status.value,
                "was_clamped": result.was_clamped,
                "method": result.explainability.method.value,
                "parameters_used": result.explainability.parameters_used,
            },
        )


# =====================================================================
# Explainability and Result Envelope
# =====================================================================


class CompositeRiskExplainability(BaseModel):
    """Auditable mathematical derivation and contribution breakdown for M3-06."""

    model_config = ConfigDict(frozen=True)

    formula_derivation: str
    weights: Dict[RiskFactorType, float]
    contributions: Dict[RiskFactorType, float]
    normalized_factors_used: Dict[RiskFactorType, float]
    raw_values_used: Dict[RiskFactorType, Optional[Union[float, int, str]]] = Field(default_factory=dict)
    audit_trail: str


class CompositeRiskResult(BaseModel):
    """Strongly typed result envelope returned by the Multi-Hazard Risk Computation Engine.

    Guarantees:
    - When status == COMPUTED: 0.0 <= score <= 100.0, and sum of contributions equals score.
    - When status == INSUFFICIENT_FACTORS: score is strictly None (missing factor is NEVER coerced to zero).
    - Exposes factor contributions, weights, formula derivation, and missing factors for explainability.
    """

    model_config = ConfigDict(frozen=True)

    village_id: Optional[str] = None
    score: Optional[float] = None
    status: RiskComputationStatus
    factor_contributions: Dict[RiskFactorType, float] = Field(default_factory=dict)
    factor_values_used: Dict[RiskFactorType, float] = Field(default_factory=dict)
    weights_used: Dict[RiskFactorType, float] = Field(default_factory=dict)
    missing_factors: List[RiskFactorType] = Field(default_factory=list)
    diagnostic_message: Optional[str] = None
    explainability: CompositeRiskExplainability
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None

    @model_validator(mode="after")
    def validate_composite_contract(self) -> "CompositeRiskResult":
        if self.status == RiskComputationStatus.COMPUTED:
            if self.score is None:
                raise ValueError("Computed composite risk result must include a non-null numeric score.")
            if math.isnan(self.score) or math.isinf(self.score):
                raise ValueError(f"Computed composite risk score cannot be NaN or Inf, got {self.score}.")
            if not (0.0 <= self.score <= 100.0):
                raise ValueError(f"Computed composite risk score must be in [0.0, 100.0], got {self.score}.")
            if self.missing_factors:
                raise ValueError(
                    f"Computed risk cannot have missing factors: {self.missing_factors}."
                )
        elif self.status in (RiskComputationStatus.INSUFFICIENT_FACTORS, RiskComputationStatus.INVALID_INPUT):
            if self.score is not None:
                raise ValueError(
                    f"Safety violation: Status is {self.status.value} but score is {self.score}. "
                    f"Incomplete or invalid risk computations must never emit a numerical score."
                )
        return self
