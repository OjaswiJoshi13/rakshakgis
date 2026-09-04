"""Multi-Hazard Composite Risk Computation Engine for RakshakGIS.

Authoritative Formula:
  Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V
Where:
  H = hazard_severity
  F = flood_exposure
  R = rainfall_intensity
  S = slope_landslide_susceptibility
  D = infrastructure_vulnerability
  V = social_vulnerability

Scope Boundary:
  Computes the continuous composite risk score in [0.0, 100.0].
  Does NOT compute risk classification bands (M3-07), Red Zones (M3-10), or relocation priority (M3-12).
"""

import math
from typing import Any, Dict, List, Optional, Union

from app.core.profiles import get_profile
from app.core.profiles.models import RegionProfile
from app.core.risk.computation.contracts import (
    CompositeRiskExplainability,
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorInput,
    RiskFactorType,
    RiskWeightsConfig,
)
from app.core.risk.computation.errors import InvalidFactorValueError
from app.core.risk.normalization.contracts import NormalizationResult
from app.data.providers.contracts import ProviderProvenance

# List of all six mandatory factor types
REQUIRED_FACTORS: List[RiskFactorType] = [
    RiskFactorType.HAZARD_SEVERITY,
    RiskFactorType.FLOOD_EXPOSURE,
    RiskFactorType.RAINFALL_INTENSITY,
    RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY,
    RiskFactorType.INFRASTRUCTURE_VULNERABILITY,
    RiskFactorType.SOCIAL_VULNERABILITY,
]


class MultiHazardRiskEngine:
    """Deterministic, region-agnostic engine that evaluates the multi-hazard composite risk formula."""

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
    ):
        """Initialize the computation engine with configured weights or active regional profile.

        Args:
            profile: Optional regional profile to source weights from (defaults to Himalayan pilot).
            weights: Optional explicit RiskWeightsConfig override.
        """
        if weights is not None:
            self.weights = weights
            self.profile = profile
        else:
            self.profile = profile if profile is not None else get_profile("himalayan_pilot")
            self.weights = RiskWeightsConfig.from_profile(self.profile)

    def compute_from_values(
        self,
        hazard_severity: Optional[float] = None,
        flood_exposure: Optional[float] = None,
        rainfall_intensity: Optional[float] = None,
        slope_landslide_susceptibility: Optional[float] = None,
        infrastructure_vulnerability: Optional[float] = None,
        social_vulnerability: Optional[float] = None,
        village_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> CompositeRiskResult:
        """Compute composite risk from raw numeric factor values or None."""
        factors_dict = {
            RiskFactorType.HAZARD_SEVERITY: hazard_severity,
            RiskFactorType.FLOOD_EXPOSURE: flood_exposure,
            RiskFactorType.RAINFALL_INTENSITY: rainfall_intensity,
            RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: slope_landslide_susceptibility,
            RiskFactorType.INFRASTRUCTURE_VULNERABILITY: infrastructure_vulnerability,
            RiskFactorType.SOCIAL_VULNERABILITY: social_vulnerability,
        }
        return self.compute_risk(factors=factors_dict, village_id=village_id, provenance=provenance)

    def compute_risk(
        self,
        factors: Union[
            Dict[Union[RiskFactorType, str], Union[float, int, RiskFactorInput, NormalizationResult, None]],
            List[RiskFactorInput],
        ],
        village_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> CompositeRiskResult:
        """Compute multi-hazard composite risk score from normalized factors.

        Args:
            factors: Map or list of factor inputs (supports numeric floats, RiskFactorInput, or NormalizationResult).
            village_id: Optional identifier of the assessed village.
            provenance: Optional provider provenance metadata.

        Returns:
            CompositeRiskResult with score, factor contributions, and audit explainability.
        """
        parsed_inputs: Dict[RiskFactorType, RiskFactorInput] = {}
        missing_factors: List[RiskFactorType] = []
        invalid_reasons: List[str] = []

        # 1. Normalize input representation into a Dict[RiskFactorType, RiskFactorInput]
        if isinstance(factors, list):
            for item in factors:
                if isinstance(item, RiskFactorInput):
                    parsed_inputs[item.factor_type] = item
        elif isinstance(factors, dict):
            for k, val in factors.items():
                factor_type = self._resolve_factor_type(k)
                if factor_type is None:
                    continue

                if isinstance(val, RiskFactorInput):
                    parsed_inputs[factor_type] = val
                elif isinstance(val, NormalizationResult):
                    parsed_inputs[factor_type] = RiskFactorInput.from_normalization_result(
                        factor_type=factor_type,
                        result=val,
                    )
                elif val is None:
                    parsed_inputs[factor_type] = RiskFactorInput.from_value(
                        factor_type=factor_type,
                        value=None,
                    )
                elif isinstance(val, (int, float)):
                    try:
                        parsed_inputs[factor_type] = RiskFactorInput.from_value(
                            factor_type=factor_type,
                            value=float(val),
                        )
                    except InvalidFactorValueError as e:
                        invalid_reasons.append(str(e))
                else:
                    invalid_reasons.append(
                        f"Unsupported value type for {factor_type.value}: {type(val).__name__}"
                    )

        # 2. Check for invalid inputs (e.g. NaN, infinity, or out-of-domain numbers)
        if invalid_reasons:
            return self._build_invalid_result(
                village_id=village_id,
                reason="; ".join(invalid_reasons),
                provenance=provenance,
            )

        # 3. Identify missing or unavailable factors among the mandatory 6 factors
        for req_factor in REQUIRED_FACTORS:
            factor_input = parsed_inputs.get(req_factor)
            if factor_input is None or not factor_input.is_available or factor_input.normalized_value is None:
                missing_factors.append(req_factor)

        # 4. Safety-Critical Missing Check: Never coerce missing factors to zero
        if missing_factors:
            missing_names = [f.value for f in missing_factors]
            diagnostic_msg = (
                f"Cannot compute composite risk score: required factor(s) missing or unavailable: {missing_names}. "
                f"Safety guard: Missing or unmonitored factors are never silently coerced to zero risk."
            )
            return self._build_insufficient_result(
                village_id=village_id,
                missing_factors=missing_factors,
                diagnostic_message=diagnostic_msg,
                provenance=provenance,
            )

        # 5. Compute the Authoritative Weighted Composite Risk Score
        weights_dict = self.weights.as_dict()
        contributions: Dict[RiskFactorType, float] = {}
        factor_values: Dict[RiskFactorType, float] = {}
        raw_values: Dict[RiskFactorType, Optional[Union[float, int, str]]] = {}
        audit_snippets: List[str] = []

        total_risk = 0.0

        for req_factor in REQUIRED_FACTORS:
            inp = parsed_inputs[req_factor]
            val = inp.normalized_value  # Guaranteed float in [0.0, 100.0]
            w = weights_dict[req_factor]

            contrib = round(w * val, 4)
            contributions[req_factor] = contrib
            factor_values[req_factor] = val
            raw_values[req_factor] = inp.raw_value

            total_risk += w * val
            audit_snippets.append(f"{req_factor.symbol}({val:.1f}*{w:.2f}={contrib:.2f})")

        # Invariant: final score clamped strictly to [0.0, 100.0]
        final_score = round(max(0.0, min(100.0, total_risk)), 4)

        derivation_formula = (
            f"Risk = {self.weights.hazard_severity:.2f}*H + {self.weights.flood_exposure:.2f}*F + "
            f"{self.weights.rainfall_intensity:.2f}*R + {self.weights.slope_landslide_susceptibility:.2f}*S + "
            f"{self.weights.infrastructure_vulnerability:.2f}*D + {self.weights.social_vulnerability:.2f}*V"
        )
        audit_trail = f"Risk score = {final_score:.4f} derived from: {' + '.join(audit_snippets)}"

        explainability = CompositeRiskExplainability(
            formula_derivation=derivation_formula,
            weights=weights_dict,
            contributions=contributions,
            normalized_factors_used=factor_values,
            raw_values_used=raw_values,
            audit_trail=audit_trail,
        )

        return CompositeRiskResult(
            village_id=village_id,
            score=final_score,
            status=RiskComputationStatus.COMPUTED,
            factor_contributions=contributions,
            factor_values_used=factor_values,
            weights_used=weights_dict,
            missing_factors=[],
            diagnostic_message=None,
            explainability=explainability,
            provenance=provenance,
        )

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _resolve_factor_type(self, key: Union[RiskFactorType, str]) -> Optional[RiskFactorType]:
        """Resolve a factor type from an enum, exact name, or single-letter symbol."""
        if isinstance(key, RiskFactorType):
            return key

        if not isinstance(key, str):
            return None

        clean_key = key.strip().lower()

        symbol_map = {
            "h": RiskFactorType.HAZARD_SEVERITY,
            "f": RiskFactorType.FLOOD_EXPOSURE,
            "r": RiskFactorType.RAINFALL_INTENSITY,
            "s": RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY,
            "d": RiskFactorType.INFRASTRUCTURE_VULNERABILITY,
            "v": RiskFactorType.SOCIAL_VULNERABILITY,
        }
        if clean_key in symbol_map:
            return symbol_map[clean_key]

        name_map = {f.value: f for f in RiskFactorType}
        if clean_key in name_map:
            return name_map[clean_key]

        # Convenience aliases matching M3-01 / domain terminology
        alias_map = {
            "hazard": RiskFactorType.HAZARD_SEVERITY,
            "flood": RiskFactorType.FLOOD_EXPOSURE,
            "rainfall": RiskFactorType.RAINFALL_INTENSITY,
            "slope": RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY,
            "landslide": RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY,
            "seismic": RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY,
            "infrastructure": RiskFactorType.INFRASTRUCTURE_VULNERABILITY,
            "demographic": RiskFactorType.INFRASTRUCTURE_VULNERABILITY,
            "vulnerability": RiskFactorType.SOCIAL_VULNERABILITY,
            "social": RiskFactorType.SOCIAL_VULNERABILITY,
        }
        return alias_map.get(clean_key)

    def _build_insufficient_result(
        self,
        village_id: Optional[str],
        missing_factors: List[RiskFactorType],
        diagnostic_message: str,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]],
    ) -> CompositeRiskResult:
        """Construct structured INSUFFICIENT_FACTORS result ensuring score is strictly None."""
        weights_dict = self.weights.as_dict()
        explainability = CompositeRiskExplainability(
            formula_derivation="Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V",
            weights=weights_dict,
            contributions={},
            normalized_factors_used={},
            audit_trail=f"Computation aborted: missing required factors {[f.value for f in missing_factors]}",
        )
        return CompositeRiskResult(
            village_id=village_id,
            score=None,
            status=RiskComputationStatus.INSUFFICIENT_FACTORS,
            factor_contributions={},
            factor_values_used={},
            weights_used=weights_dict,
            missing_factors=missing_factors,
            diagnostic_message=diagnostic_message,
            explainability=explainability,
            provenance=provenance,
        )

    def _build_invalid_result(
        self,
        village_id: Optional[str],
        reason: str,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]],
    ) -> CompositeRiskResult:
        """Construct structured INVALID_INPUT result ensuring score is strictly None."""
        weights_dict = self.weights.as_dict()
        explainability = CompositeRiskExplainability(
            formula_derivation="Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V",
            weights=weights_dict,
            contributions={},
            normalized_factors_used={},
            audit_trail=f"Computation rejected: {reason}",
        )
        return CompositeRiskResult(
            village_id=village_id,
            score=None,
            status=RiskComputationStatus.INVALID_INPUT,
            factor_contributions={},
            factor_values_used={},
            weights_used=weights_dict,
            missing_factors=[],
            diagnostic_message=reason,
            explainability=explainability,
            provenance=provenance,
        )
