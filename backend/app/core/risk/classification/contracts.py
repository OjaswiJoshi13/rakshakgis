"""Typed schemas, enumerations, and contracts for the Risk Classification & Grading Engine."""

import math
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.profiles.models import RegionProfile, RiskBand, RiskScoreBands
from app.core.risk.classification.errors import (
    ClassificationBandConfigError,
    InvalidRiskScoreError,
)
from app.core.risk.computation.contracts import CompositeRiskResult


class RiskScoreBandsConfig(BaseModel):
    """Authoritative score cutoffs for classifying continuous risk scores into categorical risk bands.

    Default Authoritative Intervals:
    - [0.0, 25.0)   -> SAFE
    - [25.0, 50.0)  -> MODERATE
    - [50.0, 70.0)  -> HIGH
    - [70.0, 85.0)  -> VERY_HIGH
    - [85.0, 100.0] -> CRITICAL
    """

    model_config = ConfigDict(frozen=True)

    safe_max: float = Field(default=25.0, ge=0.0, le=100.0, description="Upper bound for SAFE (exclusive)")
    moderate_max: float = Field(default=50.0, ge=0.0, le=100.0, description="Upper bound for MODERATE (exclusive)")
    high_max: float = Field(default=70.0, ge=0.0, le=100.0, description="Upper bound for HIGH (exclusive)")
    very_high_max: float = Field(default=85.0, ge=0.0, le=100.0, description="Upper bound for VERY_HIGH (exclusive)")
    critical_max: float = Field(default=100.0, ge=0.0, le=100.0, description="Upper bound for CRITICAL (inclusive)")

    @model_validator(mode="after")
    def validate_monotonic_cutoffs(self) -> "RiskScoreBandsConfig":
        """Validate that cutoffs are strictly increasing within (0.0, 100.0]."""
        cutoffs = [
            ("safe_max", self.safe_max),
            ("moderate_max", self.moderate_max),
            ("high_max", self.high_max),
            ("very_high_max", self.very_high_max),
            ("critical_max", self.critical_max),
        ]
        prev_val = 0.0
        for name, val in cutoffs:
            if math.isnan(val) or math.isinf(val):
                raise ClassificationBandConfigError(f"Cutoff {name} cannot be NaN or infinite.")
            if val <= prev_val:
                raise ClassificationBandConfigError(
                    f"Risk band cutoffs must be strictly increasing: {name} ({val}) <= previous ({prev_val})."
                )
            prev_val = val
        if self.critical_max != 100.0:
            raise ClassificationBandConfigError(
                f"critical_max must be 100.0 for full domain coverage, got {self.critical_max}."
            )
        return self

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "RiskScoreBandsConfig":
        """Initialize band cutoffs from an M3-01 RegionProfile."""
        pb: RiskScoreBands = profile.risk_bands
        return cls(
            safe_max=pb.safe_max,
            moderate_max=pb.moderate_max,
            high_max=pb.high_max,
            very_high_max=pb.very_high_max,
            critical_max=pb.critical_max,
        )


class RiskClassificationExplainability(BaseModel):
    """Detailed explainability metadata describing the classification derivation."""

    model_config = ConfigDict(frozen=True)

    band: RiskBand
    band_name: str
    score: float
    interval_notation: str
    lower_bound: float
    upper_bound: float
    lower_inclusive: bool
    upper_inclusive: bool
    audit_trail: str


class RiskClassificationResult(BaseModel):
    """Strongly typed result envelope returned by the Risk Classification Engine.

    Guarantees:
    - 0.0 <= score <= 100.0 (preserves original composite score without loss of precision)
    - band is the authoritative RiskBand enum (SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL)
    - explainability contains exact interval thresholds and audit metadata
    """

    model_config = ConfigDict(frozen=True)

    score: float
    band: RiskBand
    village_id: Optional[str] = None
    explainability: RiskClassificationExplainability
    composite_result: Optional[CompositeRiskResult] = None

    @model_validator(mode="after")
    def validate_classification_result(self) -> "RiskClassificationResult":
        if math.isnan(self.score) or math.isinf(self.score):
            raise InvalidRiskScoreError(f"Classified score cannot be NaN or infinite, got {self.score}.")
        if not (0.0 <= self.score <= 100.0):
            raise InvalidRiskScoreError(f"Classified score must be in range [0.0, 100.0], got {self.score}.")
        return self
