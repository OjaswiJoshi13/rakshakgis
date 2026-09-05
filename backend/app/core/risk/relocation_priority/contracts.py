"""Data contracts, schemas, and result envelopes for Relocation Priority Scoring (Chunk M3-12)."""

from datetime import datetime
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.profiles.models import (
    RegionProfile,
    RelocationPriorityBand,
    RelocationPriorityCutoffs,
    RelocationPriorityWeights,
)
from app.core.risk.computation.contracts import CompositeRiskResult, RiskComputationStatus
from app.core.risk.relocation_priority.errors import (
    InvalidPriorityDataError,
    PriorityConfigError,
)
from app.core.risk.vulnerability.contracts import (
    DemographicExposureResult,
    ScoringStatus,
    SocialVulnerabilityResult,
)
from app.data.providers.contracts import ProviderProvenance


# =====================================================================
# Status & Factor Type Enums
# =====================================================================


class RelocationPriorityStatus(str, Enum):
    """Evaluation status for village relocation priority scoring."""

    SCORED = "scored"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID_INPUT = "invalid_input"


class PriorityFactorType(str, Enum):
    """The 5 authoritative factors comprising the relocation priority formula."""

    RISK = "risk"                               # Weight 0.40, Symbol R
    EXPOSURE = "exposure"                       # Weight 0.25, Symbol E
    VULNERABILITY = "vulnerability"             # Weight 0.20, Symbol V
    HISTORICAL_IMPACT = "historical_impact"     # Weight 0.10, Symbol H
    ACCESSIBILITY = "accessibility"             # Weight 0.05, Symbol A

    @property
    def symbol(self) -> str:
        mapping = {
            PriorityFactorType.RISK: "R",
            PriorityFactorType.EXPOSURE: "E",
            PriorityFactorType.VULNERABILITY: "V",
            PriorityFactorType.HISTORICAL_IMPACT: "H",
            PriorityFactorType.ACCESSIBILITY: "A",
        }
        return mapping[self]

    @property
    def display_name(self) -> str:
        mapping = {
            PriorityFactorType.RISK: "Multi-Hazard Composite Risk",
            PriorityFactorType.EXPOSURE: "Demographic Exposure",
            PriorityFactorType.VULNERABILITY: "Social Vulnerability",
            PriorityFactorType.HISTORICAL_IMPACT: "Historical Disaster Impact",
            PriorityFactorType.ACCESSIBILITY: "Evacuation Accessibility & Isolation",
        }
        return mapping[self]


# =====================================================================
# Configuration Contracts
# =====================================================================


class RelocationPriorityWeightsConfig(BaseModel):
    """Authoritative weights configuration for relocation priority scoring.

    Formula:
      Priority = 0.40*Risk + 0.25*Exposure + 0.20*Vulnerability + 0.10*HistoricalImpact + 0.05*Accessibility
    All weights must be non-negative and sum strictly to 1.0 within tolerance.
    """

    model_config = ConfigDict(frozen=True)

    risk_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    exposure_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    vulnerability_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    historical_impact_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    accessibility_weight: float = Field(default=0.05, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights(self) -> "RelocationPriorityWeightsConfig":
        weights = [
            self.risk_weight,
            self.exposure_weight,
            self.vulnerability_weight,
            self.historical_impact_weight,
            self.accessibility_weight,
        ]
        for w in weights:
            if math.isnan(w) or math.isinf(w):
                raise PriorityConfigError("Relocation priority weights cannot be NaN or infinite.")

        total = sum(weights)
        if abs(total - 1.0) > 1e-4:
            raise PriorityConfigError(
                f"Relocation priority weights must sum to 1.0 (got {total:.4f})."
            )
        return self

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "RelocationPriorityWeightsConfig":
        """Initialize configuration directly from an authoritative RegionProfile."""
        try:
            rp_weights: RelocationPriorityWeights = profile.relocation_priority_parameters.weights
            return cls(
                risk_weight=float(rp_weights.risk_weight),
                exposure_weight=float(rp_weights.exposure_weight),
                vulnerability_weight=float(rp_weights.vulnerability_weight),
                historical_impact_weight=float(rp_weights.historical_impact_weight),
                accessibility_weight=float(rp_weights.accessibility_weight),
            )
        except Exception as e:
            raise PriorityConfigError(f"Failed to resolve relocation priority weights from profile: {e}") from e


class PriorityScoreBandsConfig(BaseModel):
    """Threshold cutoffs governing classification into Relocation Priority Bands.

    Authoritative cutoffs:
    - IMMEDIATE: [80.0, 100.0]
    - SHORT-TERM: [60.0, 80.0)
    - MEDIUM-TERM: [40.0, 60.0)
    - MONITOR: [0.0, 40.0)
    """

    model_config = ConfigDict(frozen=True)

    monitor_max: float = Field(default=39.99, ge=0.0, le=100.0)
    medium_term_min: float = Field(default=40.0, ge=0.0, le=100.0)
    short_term_min: float = Field(default=60.0, ge=0.0, le=100.0)
    immediate_min: float = Field(default=80.0, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_cutoffs(self) -> "PriorityScoreBandsConfig":
        if not (self.medium_term_min < self.short_term_min < self.immediate_min):
            raise PriorityConfigError("Priority score band cutoffs must be strictly ascending: medium < short < immediate.")
        return self

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "PriorityScoreBandsConfig":
        """Initialize band cutoffs directly from an authoritative RegionProfile."""
        try:
            cutoffs: RelocationPriorityCutoffs = profile.relocation_priority_parameters.cutoffs
            return cls(
                monitor_max=float(cutoffs.monitor_max),
                medium_term_min=float(cutoffs.medium_term_min),
                short_term_min=float(cutoffs.short_term_min),
                immediate_min=float(cutoffs.immediate_min),
            )
        except Exception as e:
            raise PriorityConfigError(f"Failed to resolve relocation priority cutoffs from profile: {e}") from e


# =====================================================================
# Input Contract
# =====================================================================


class RelocationPriorityInput(BaseModel):
    """Input parameters for evaluating relocation priority for a settlement."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    village_id: Optional[str] = None
    village_name: Optional[str] = None
    risk: Optional[Union[float, int, CompositeRiskResult, Dict[str, Any]]] = None
    exposure: Optional[Union[float, int, DemographicExposureResult, Dict[str, Any]]] = None
    vulnerability: Optional[Union[float, int, SocialVulnerabilityResult, Dict[str, Any]]] = None
    historical_impact: Optional[Union[float, int, Dict[str, Any]]] = None
    accessibility: Optional[Union[float, int, Dict[str, Any], Any]] = None
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any], List[Dict[str, Any]]]] = None


# =====================================================================
# Factor Breakdown & Explainability Contracts
# =====================================================================


class PriorityFactorDetail(BaseModel):
    """Detailed mathematical and descriptive decomposition for an individual priority factor."""

    model_config = ConfigDict(frozen=True)

    factor_type: PriorityFactorType
    factor_name: str
    symbol: str
    normalized_value: Optional[float] = None
    weight: float = Field(ge=0.0, le=1.0)
    weighted_contribution: Optional[float] = None
    contribution_percentage: Optional[float] = None
    is_available: bool = True
    raw_value: Optional[Union[float, int, str]] = None
    description: str = ""

    @model_validator(mode="after")
    def validate_factor_detail(self) -> "PriorityFactorDetail":
        if self.is_available and self.normalized_value is not None:
            if math.isnan(self.normalized_value) or math.isinf(self.normalized_value):
                raise InvalidPriorityDataError(
                    f"Factor {self.factor_type.value} normalized value cannot be NaN or infinite."
                )
            if not (0.0 <= self.normalized_value <= 100.0):
                raise InvalidPriorityDataError(
                    f"Factor {self.factor_type.value} normalized value {self.normalized_value} out of range [0.0, 100.0]."
                )
        return self


class RelocationPriorityExplainability(BaseModel):
    """Complete mathematical audit trail and human-readable narrative for relocation priority scoring."""

    model_config = ConfigDict(frozen=True)

    formula: str = "0.40*Risk + 0.25*Exposure + 0.20*Vulnerability + 0.10*HistoricalImpact + 0.05*Accessibility"
    factor_breakdown: List[PriorityFactorDetail] = Field(default_factory=list)
    primary_driver: Optional[str] = None
    primary_driver_contribution: Optional[float] = None
    summary_narrative: str = ""
    decision_reason: str = ""
    profile_id: str = "custom"
    profile_name: str = "Custom Profile"
    was_clamped: bool = False
    governance_notice: str = (
        "DECISION SUPPORT ONLY: Relocation priority scores represent analytical recommendations "
        "for District Officer and Rehabilitation Committee review. This calculation does NOT "
        "constitute an evacuation order, legal mandate, or site assignment."
    )


# =====================================================================
# Result Envelope
# =====================================================================


class RelocationPriorityResult(BaseModel):
    """Authoritative result envelope for village relocation priority scoring (Chunk M3-12)."""

    model_config = ConfigDict(frozen=True)

    village_id: Optional[str] = None
    village_name: Optional[str] = None
    status: RelocationPriorityStatus
    priority_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Calculated priority score on [0.0, 100.0] scale; None if INSUFFICIENT_DATA",
    )
    priority_band: Optional[RelocationPriorityBand] = Field(
        default=None,
        description="Categorized urgency band; None if INSUFFICIENT_DATA",
    )
    factor_scores: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Normalized 0-100 values for each of the 5 factors",
    )
    factor_contributions: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Weighted contribution (weight * normalized_value) for each factor",
    )
    factor_details: List[PriorityFactorDetail] = Field(default_factory=list)
    missing_factors: List[str] = Field(default_factory=list)
    explainability: RelocationPriorityExplainability
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    is_actionable_proposal: bool = True
    is_automatic_evacuation: bool = False
    governance_notice: str = (
        "DECISION SUPPORT ONLY: Relocation priority scores represent analytical recommendations "
        "for District Officer and Rehabilitation Committee review. This calculation does NOT "
        "constitute an evacuation order, legal mandate, or site assignment."
    )

    @model_validator(mode="after")
    def validate_governance_and_status(self) -> "RelocationPriorityResult":
        # Strict governance invariant
        if self.is_automatic_evacuation:
            raise ValueError("RelocationPriorityResult cannot have is_automatic_evacuation=True (governance invariant).")

        if self.status == RelocationPriorityStatus.SCORED:
            if self.priority_score is None:
                raise ValueError("priority_score cannot be None when status is SCORED.")
            if self.priority_band is None:
                raise ValueError("priority_band cannot be None when status is SCORED.")
            if self.missing_factors:
                raise ValueError("missing_factors must be empty when status is SCORED.")
        elif self.status == RelocationPriorityStatus.INSUFFICIENT_DATA:
            if self.priority_score is not None:
                raise ValueError("priority_score must be None when status is INSUFFICIENT_DATA.")
            if self.priority_band is not None:
                raise ValueError("priority_band must be None when status is INSUFFICIENT_DATA.")
            if not self.missing_factors:
                raise ValueError("missing_factors must be non-empty when status is INSUFFICIENT_DATA.")
        return self
