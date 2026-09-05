"""Typed schemas and contracts for Risk Explainability & Factor Contribution (Chunk M3-08)."""

import math
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.profiles.models import RiskBand
from app.core.risk.computation.contracts import (
    RiskComputationStatus,
    RiskFactorType,
)
from app.core.risk.explainability.errors import UncomputableExplanationError
from app.data.providers.contracts import ProviderProvenance


# Canonical descriptive metadata mapping for all six composite factors
FACTOR_METADATA: Dict[RiskFactorType, Dict[str, str]] = {
    RiskFactorType.HAZARD_SEVERITY: {
        "symbol": "H",
        "name": "Hazard Severity",
        "description": "Landslide and slope instability severity",
    },
    RiskFactorType.FLOOD_EXPOSURE: {
        "symbol": "F",
        "name": "Flood Exposure",
        "description": "Hydrological flood and inundation exposure",
    },
    RiskFactorType.RAINFALL_INTENSITY: {
        "symbol": "R",
        "name": "Rainfall Intensity",
        "description": "24-hour precipitation exceedance factor",
    },
    RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: {
        "symbol": "S",
        "name": "Slope / Landslide Susceptibility",
        "description": "Geophysical slope gradient and seismic susceptibility",
    },
    RiskFactorType.INFRASTRUCTURE_VULNERABILITY: {
        "symbol": "D",
        "name": "Infrastructure Vulnerability",
        "description": "Physical infrastructure damage vulnerability and demographic exposure",
    },
    RiskFactorType.SOCIAL_VULNERABILITY: {
        "symbol": "V",
        "name": "Social Vulnerability",
        "description": "Socioeconomic sensitivity and vulnerable demographic share",
    },
}


class FactorContributionDetail(BaseModel):
    """Detailed mathematical and descriptive decomposition for a single risk factor."""

    model_config = ConfigDict(frozen=True)

    factor_type: RiskFactorType
    symbol: str
    factor_name: str
    description: str
    normalized_value: Optional[float] = None
    weight: float = Field(ge=0.0, le=1.0)
    weighted_contribution: Optional[float] = None
    contribution_percentage: Optional[float] = None
    is_available: bool = True
    raw_value: Optional[Union[float, int, str]] = None

    @model_validator(mode="after")
    def validate_factor_contribution(self) -> "FactorContributionDetail":
        if self.is_available:
            if self.normalized_value is not None:
                if math.isnan(self.normalized_value) or math.isinf(self.normalized_value):
                    raise ValueError(
                        f"Factor {self.factor_type.value} normalized value cannot be NaN or infinite."
                    )
                if not (0.0 <= self.normalized_value <= 100.0):
                    raise ValueError(
                        f"Factor {self.factor_type.value} normalized value {self.normalized_value} "
                        f"out of valid range [0.0, 100.0]."
                    )
            if self.weighted_contribution is not None:
                if math.isnan(self.weighted_contribution) or math.isinf(self.weighted_contribution):
                    raise ValueError(
                        f"Factor {self.factor_type.value} weighted contribution cannot be NaN or infinite."
                    )
            if self.contribution_percentage is not None:
                if math.isnan(self.contribution_percentage) or math.isinf(self.contribution_percentage):
                    raise ValueError(
                        f"Factor {self.factor_type.value} contribution percentage cannot be NaN or infinite."
                    )
                if not (-1e-4 <= self.contribution_percentage <= 100.0001):
                    raise ValueError(
                        f"Factor {self.factor_type.value} contribution percentage {self.contribution_percentage} "
                        f"out of valid range [0.0, 100.0]."
                    )
        else:
            if self.normalized_value is not None:
                raise ValueError(
                    f"Factor {self.factor_type.value} is marked is_available=False but has normalized_value={self.normalized_value}."
                )
            if self.weighted_contribution is not None:
                raise ValueError(
                    f"Factor {self.factor_type.value} is marked is_available=False but has weighted_contribution={self.weighted_contribution}."
                )
            if self.contribution_percentage is not None:
                raise ValueError(
                    f"Factor {self.factor_type.value} is marked is_available=False but has contribution_percentage={self.contribution_percentage}."
                )
        return self


class FactorRanking(BaseModel):
    """Ranked factor contribution entry for identifying primary disaster risk drivers."""

    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1, le=6, description="Rank order (1 = highest contributor)")
    factor_type: RiskFactorType
    symbol: str
    factor_name: str
    weighted_contribution: float
    contribution_percentage: Optional[float] = None


class RiskClassificationSummary(BaseModel):
    """Summary of M3-07 categorical classification integrated into the explanation."""

    model_config = ConfigDict(frozen=True)

    band: RiskBand
    band_name: str
    interval_notation: str
    audit_trail: Optional[str] = None


class CompositeRiskExplanation(BaseModel):
    """Comprehensive, strongly typed, and auditable risk explanation envelope for M3-08.

    Answers:
    - What factors contributed to the risk score?
    - What normalized value did each factor have?
    - What weight was applied to each factor?
    - What weighted contribution did each factor make?
    - What percentage of the overall risk does each factor represent?
    - What was the final composite risk score?
    - Which risk band was assigned (when classification is available)?
    - What formula/configuration was used?
    - Can the explanation be reproduced deterministically from the backend result?
    """

    model_config = ConfigDict(frozen=True)

    village_id: Optional[str] = None
    status: RiskComputationStatus
    score: Optional[float] = None
    is_computable: bool
    formula: str
    weights_used: Dict[RiskFactorType, float]
    factor_contributions: List[FactorContributionDetail]
    ranked_contributions: List[FactorRanking] = Field(default_factory=list)
    dominant_factor: Optional[RiskFactorType] = None
    missing_factors: List[RiskFactorType] = Field(default_factory=list)
    classification: Optional[RiskClassificationSummary] = None
    narrative_explanation: str
    audit_trail: str
    configuration_provenance: Optional[Dict[str, Any]] = None
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None

    @model_validator(mode="after")
    def validate_explanation_envelope(self) -> "CompositeRiskExplanation":
        if self.status == RiskComputationStatus.COMPUTED:
            if not self.is_computable:
                raise ValueError("Status is COMPUTED but is_computable is False.")
            if self.score is None:
                raise ValueError("Computed risk explanation must have a non-null numeric score.")
            if math.isnan(self.score) or math.isinf(self.score):
                raise ValueError(f"Computed risk explanation score cannot be NaN or infinite: {self.score}.")
            if not (0.0 <= self.score <= 100.0):
                raise ValueError(f"Computed risk explanation score must be in [0.0, 100.0], got {self.score}.")
            if self.missing_factors:
                raise ValueError(f"Computed risk explanation cannot have missing factors: {self.missing_factors}.")
        elif self.status in (RiskComputationStatus.INSUFFICIENT_FACTORS, RiskComputationStatus.INVALID_INPUT):
            if self.is_computable:
                raise ValueError(f"Status is {self.status.value} but is_computable is True.")
            if self.score is not None:
                raise ValueError(
                    f"Safety violation: Status is {self.status.value} but score is {self.score}. "
                    f"Incomplete or invalid risk explanations must never emit a numeric score."
                )
            if self.status == RiskComputationStatus.INSUFFICIENT_FACTORS and not self.missing_factors:
                raise ValueError("Status is INSUFFICIENT_FACTORS but missing_factors list is empty.")
        return self
