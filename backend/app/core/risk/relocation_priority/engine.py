"""Core Relocation Priority Scoring Engine for RakshakGIS (Chunk M3-12).

Authoritative Formula:
  Relocation Priority = 0.40*Risk + 0.25*Exposure + 0.20*Vulnerability + 0.10*HistoricalImpact + 0.05*Accessibility

Authoritative Priority Bands:
  [80.0, 100.0] -> IMMEDIATE
  [60.0, 80.0)  -> SHORT_TERM
  [40.0, 60.0)  -> MEDIUM_TERM
  [0.0, 40.0)   -> MONITOR

Scope & Governance Boundaries:
  - Decision support recommendation for District Officer & Rehabilitation Committee review.
  - Zero automatic evacuation orders (is_automatic_evacuation = False strictly enforced).
  - Missing factor data is NEVER assumed safe, defaulted to 0, or silently classified as MONITOR.
  - 100% deterministic algorithms; zero LLMs.
"""

from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from app.core.profiles import get_profile
from app.core.profiles.models import (
    RegionProfile,
    RegionProfileId,
    RelocationPriorityBand,
)
from app.core.risk.computation.contracts import CompositeRiskResult, RiskComputationStatus
from app.core.risk.relocation_priority.contracts import (
    PriorityFactorDetail,
    PriorityFactorType,
    PriorityScoreBandsConfig,
    RelocationPriorityExplainability,
    RelocationPriorityInput,
    RelocationPriorityResult,
    RelocationPriorityStatus,
    RelocationPriorityWeightsConfig,
)
from app.core.risk.relocation_priority.errors import (
    InsufficientPriorityDataError,
    InvalidPriorityDataError,
)
from app.core.risk.vulnerability.contracts import (
    DemographicExposureResult,
    ScoringStatus,
    SocialVulnerabilityResult,
)
from app.data.providers.contracts import ProviderProvenance


class RelocationPriorityEngine:
    """Deterministic, profile-driven engine evaluating settlement relocation urgency."""

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        weights_config: Optional[RelocationPriorityWeightsConfig] = None,
        bands_config: Optional[PriorityScoreBandsConfig] = None,
    ) -> None:
        """Initialize engine with configured weights and band cutoffs from profile or overrides."""
        if profile is not None:
            self.profile = profile
        else:
            self.profile = get_profile(RegionProfileId.HIMALAYAN_PILOT)

        self.weights_config = (
            weights_config
            if weights_config is not None
            else RelocationPriorityWeightsConfig.from_profile(self.profile)
        )
        self.bands_config = (
            bands_config
            if bands_config is not None
            else PriorityScoreBandsConfig.from_profile(self.profile)
        )

    @classmethod
    def from_profile(
        cls,
        profile: Union[RegionProfile, str, RegionProfileId],
        *,
        weights_config: Optional[RelocationPriorityWeightsConfig] = None,
        bands_config: Optional[PriorityScoreBandsConfig] = None,
    ) -> "RelocationPriorityEngine":
        """Factory initializing the engine directly from an active RegionProfile."""
        resolved_profile: RegionProfile
        if isinstance(profile, RegionProfile):
            resolved_profile = profile
        elif isinstance(profile, RegionProfileId):
            resolved_profile = get_profile(profile)
        elif isinstance(profile, str):
            resolved_profile = get_profile(profile)
        else:
            raise TypeError(f"Expected RegionProfile, RegionProfileId, or str; got {type(profile).__name__}")

        return cls(
            profile=resolved_profile,
            weights_config=weights_config,
            bands_config=bands_config,
        )

    # =========================================================================
    # Single Village Evaluation
    # =========================================================================

    def evaluate(
        self,
        *,
        village_id: Optional[str] = None,
        village_name: Optional[str] = None,
        risk: Optional[Union[float, int, CompositeRiskResult, Dict[str, Any]]] = None,
        exposure: Optional[Union[float, int, DemographicExposureResult, Dict[str, Any]]] = None,
        vulnerability: Optional[Union[float, int, SocialVulnerabilityResult, Dict[str, Any]]] = None,
        historical_impact: Optional[Union[float, int, Dict[str, Any]]] = None,
        accessibility: Optional[Union[float, int, Dict[str, Any], Any]] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any], List[Dict[str, Any]]]] = None,
        strict: bool = False,
    ) -> RelocationPriorityResult:
        """Evaluate relocation priority for a settlement across the 5 authoritative factors.

        Args:
            village_id: Optional unique identifier for the village/settlement.
            village_name: Optional human-readable settlement name.
            risk: Composite risk score or CompositeRiskResult (weight 0.40).
            exposure: Demographic exposure score or DemographicExposureResult (weight 0.25).
            vulnerability: Social vulnerability score or SocialVulnerabilityResult (weight 0.20).
            historical_impact: Historical disaster impact score (weight 0.10).
            accessibility: Evacuation difficulty / isolation score (weight 0.05).
            provenance: Provider provenance or data source audit records.
            strict: If True, missing required factors raise InsufficientPriorityDataError.

        Returns:
            RelocationPriorityResult containing priority score, band, and explainability breakdown.

        Raises:
            InvalidPriorityDataError: If any factor is NaN, infinite, or outside [0.0, 100.0].
            InsufficientPriorityDataError: Under strict=True when any factor is missing.
        """
        extracted_provenance: List[Dict[str, Any]] = []

        if provenance:
            if isinstance(provenance, ProviderProvenance):
                extracted_provenance.append(provenance.model_dump())
            elif isinstance(provenance, dict):
                extracted_provenance.append(provenance)
            elif isinstance(provenance, list):
                for p in provenance:
                    if isinstance(p, ProviderProvenance):
                        extracted_provenance.append(p.model_dump())
                    elif isinstance(p, dict):
                        extracted_provenance.append(p)

        # 1. Extract and validate each of the 5 factors
        v_risk, p_risk = self._coerce_factor_value(risk, "risk", CompositeRiskResult)
        if p_risk:
            extracted_provenance.extend(p_risk)

        v_exp, p_exp = self._coerce_factor_value(exposure, "exposure", DemographicExposureResult)
        if p_exp:
            extracted_provenance.extend(p_exp)

        v_vuln, p_vuln = self._coerce_factor_value(vulnerability, "vulnerability", SocialVulnerabilityResult)
        if p_vuln:
            extracted_provenance.extend(p_vuln)

        v_hist, p_hist = self._coerce_factor_value(historical_impact, "historical_impact", None)
        if p_hist:
            extracted_provenance.extend(p_hist)

        v_acc, p_acc = self._coerce_factor_value(accessibility, "accessibility", None)
        if p_acc:
            extracted_provenance.extend(p_acc)

        factor_values: Dict[PriorityFactorType, Optional[float]] = {
            PriorityFactorType.RISK: v_risk,
            PriorityFactorType.EXPOSURE: v_exp,
            PriorityFactorType.VULNERABILITY: v_vuln,
            PriorityFactorType.HISTORICAL_IMPACT: v_hist,
            PriorityFactorType.ACCESSIBILITY: v_acc,
        }

        # 2. Check for missing factors (Safety-critical: never default to 0.0 or safe)
        missing_factors: List[str] = [
            ftype.value for ftype, val in factor_values.items() if val is None
        ]

        factor_scores_dict: Dict[str, Optional[float]] = {
            ftype.value: val for ftype, val in factor_values.items()
        }

        if missing_factors:
            if strict:
                raise InsufficientPriorityDataError(
                    f"Missing required relocation priority factor(s): {', '.join(missing_factors)}. "
                    f"Under strict policy, all 5 factors must be available.",
                    missing_fields=missing_factors,
                )

            # Build insufficient data explainability
            factor_details = self._build_factor_details(factor_values, score=None)
            explainability = RelocationPriorityExplainability(
                formula=self._get_formula_string(),
                factor_breakdown=factor_details,
                primary_driver=None,
                primary_driver_contribution=None,
                summary_narrative=(
                    f"Settlement '{village_name or village_id or 'UNKNOWN'}' has incomplete data for relocation priority "
                    f"scoring. Missing factors: {', '.join(missing_factors)}."
                ),
                decision_reason=(
                    f"INSUFFICIENT_DATA: Evaluation cannot proceed safely because required factor(s) "
                    f"[{', '.join(missing_factors)}] are missing or uncomputed."
                ),
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                was_clamped=False,
            )

            return RelocationPriorityResult(
                village_id=village_id,
                village_name=village_name,
                status=RelocationPriorityStatus.INSUFFICIENT_DATA,
                priority_score=None,
                priority_band=None,
                factor_scores=factor_scores_dict,
                factor_contributions={k: None for k in factor_scores_dict},
                factor_details=factor_details,
                missing_factors=missing_factors,
                explainability=explainability,
                provenance=extracted_provenance,
                assessed_at=datetime.utcnow(),
                is_actionable_proposal=False,
                is_automatic_evacuation=False,
            )

        # 3. Deterministic formula calculation:
        # Priority = w_risk*Risk + w_exp*Exposure + w_vuln*Vulnerability + w_hist*Historical + w_acc*Accessibility
        w = self.weights_config
        c_risk = w.risk_weight * float(v_risk)
        c_exp = w.exposure_weight * float(v_exp)
        c_vuln = w.vulnerability_weight * float(v_vuln)
        c_hist = w.historical_impact_weight * float(v_hist)
        c_acc = w.accessibility_weight * float(v_acc)

        raw_score = c_risk + c_exp + c_vuln + c_hist + c_acc

        # Deterministic clamping to [0.0, 100.0]
        final_score = max(0.0, min(100.0, raw_score))
        was_clamped = not math.isclose(raw_score, final_score, abs_tol=1e-6)

        factor_contributions: Dict[str, Optional[float]] = {
            PriorityFactorType.RISK.value: round(c_risk, 4),
            PriorityFactorType.EXPOSURE.value: round(c_exp, 4),
            PriorityFactorType.VULNERABILITY.value: round(c_vuln, 4),
            PriorityFactorType.HISTORICAL_IMPACT.value: round(c_hist, 4),
            PriorityFactorType.ACCESSIBILITY.value: round(c_acc, 4),
        }

        # 4. Priority band classification
        band = self._classify_band(final_score)

        # 5. Explainability and factor contribution breakdown
        factor_details = self._build_factor_details(factor_values, score=final_score)

        # Determine primary driver if score > 0 and a positive contribution exists
        positive_factors = [
            f for f in factor_details
            if f.weighted_contribution is not None and f.weighted_contribution > 0.0
        ]
        if final_score > 0.0 and positive_factors:
            primary_factor = max(positive_factors, key=lambda x: x.weighted_contribution or 0.0)
            primary_driver_name = primary_factor.factor_name
            primary_driver_val = primary_factor.weighted_contribution
            driver_narrative = (
                f"Primary urgency driver: {primary_driver_name} contributing {primary_driver_val:.2f} points."
            )
        else:
            primary_driver_name = None
            primary_driver_val = None
            driver_narrative = "No urgency drivers active (zero score across all evaluated factors)."

        summary_narrative = (
            f"Settlement '{village_name or village_id or 'Village'}' scored {final_score:.2f}/100, "
            f"classifying as '{band.value.upper()}'. "
            f"{driver_narrative}"
        )

        decision_reason = (
            f"SCORED: Relocation Priority Score = {final_score:.2f} classified as {band.value.upper()} "
            f"under {getattr(self.profile.metadata, 'name', 'Regional')} cutoffs. "
            f"Requires review by District Officer."
        )

        explainability = RelocationPriorityExplainability(
            formula=self._get_formula_string(),
            factor_breakdown=factor_details,
            primary_driver=primary_driver_name,
            primary_driver_contribution=primary_driver_val,
            summary_narrative=summary_narrative,
            decision_reason=decision_reason,
            profile_id=getattr(self.profile, "id", "custom"),
            profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
            if hasattr(self.profile, "metadata")
            else "Custom Profile",
            was_clamped=was_clamped,
        )

        return RelocationPriorityResult(
            village_id=village_id,
            village_name=village_name,
            status=RelocationPriorityStatus.SCORED,
            priority_score=round(final_score, 4),
            priority_band=band,
            factor_scores=factor_scores_dict,
            factor_contributions=factor_contributions,
            factor_details=factor_details,
            missing_factors=[],
            explainability=explainability,
            provenance=extracted_provenance,
            assessed_at=datetime.utcnow(),
            is_actionable_proposal=True,
            is_automatic_evacuation=False,
        )

    def evaluate_factors(
        self,
        factors: RelocationPriorityInput,
        *,
        strict: bool = False,
    ) -> RelocationPriorityResult:
        """Evaluate relocation priority using a typed RelocationPriorityInput object."""
        return self.evaluate(
            village_id=factors.village_id,
            village_name=factors.village_name,
            risk=factors.risk,
            exposure=factors.exposure,
            vulnerability=factors.vulnerability,
            historical_impact=factors.historical_impact,
            accessibility=factors.accessibility,
            provenance=factors.provenance,
            strict=strict,
        )

    def evaluate_batch(
        self,
        items: Sequence[Union[RelocationPriorityInput, Dict[str, Any]]],
        *,
        strict: bool = False,
    ) -> List[RelocationPriorityResult]:
        """Evaluate a batch of settlement priority records in sequence."""
        results: List[RelocationPriorityResult] = []
        for item in items:
            if isinstance(item, RelocationPriorityInput):
                results.append(self.evaluate_factors(item, strict=strict))
            elif isinstance(item, dict):
                results.append(self.evaluate(**item, strict=strict))
            else:
                raise TypeError(f"Unsupported batch item type: {type(item).__name__}")
        return results

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _coerce_factor_value(
        self,
        val: Any,
        factor_name: str,
        expected_type: Optional[type] = None,
    ) -> Tuple[Optional[float], List[Dict[str, Any]]]:
        """Extract and validate a factor score to [0.0, 100.0] scale, extracting any provenance."""
        if val is None:
            return None, []

        provenance_list: List[Dict[str, Any]] = []

        # Boolean is subclass of int in Python; explicitly reject
        if isinstance(val, bool):
            raise InvalidPriorityDataError(
                f"Invalid factor '{factor_name}' value type 'bool': boolean cannot be used as a numerical score."
            )

        # CompositeRiskResult
        if isinstance(val, CompositeRiskResult):
            if val.status != RiskComputationStatus.COMPUTED or val.score is None:
                return None, []
            raw = val.score
            if val.provenance:
                p = val.provenance
                if isinstance(p, list):
                    for item in p:
                        provenance_list.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
                else:
                    provenance_list.append(p.model_dump() if hasattr(p, "model_dump") else dict(p))
            return self._validate_numerical_range(raw, factor_name), provenance_list

        # DemographicExposureResult
        if isinstance(val, DemographicExposureResult):
            if val.status != ScoringStatus.SCORED or val.normalized_value is None:
                return None, []
            raw = val.normalized_value
            if val.provenance:
                p = val.provenance
                if isinstance(p, list):
                    for item in p:
                        provenance_list.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
                else:
                    provenance_list.append(p.model_dump() if hasattr(p, "model_dump") else dict(p))
            return self._validate_numerical_range(raw, factor_name), provenance_list

        # SocialVulnerabilityResult
        if isinstance(val, SocialVulnerabilityResult):
            if val.status != ScoringStatus.SCORED or val.normalized_value is None:
                return None, []
            raw = val.normalized_value
            if val.provenance:
                p = val.provenance
                if isinstance(p, list):
                    for item in p:
                        provenance_list.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
                else:
                    provenance_list.append(p.model_dump() if hasattr(p, "model_dump") else dict(p))
            return self._validate_numerical_range(raw, factor_name), provenance_list

        # Numeric scalar (int / float)
        if isinstance(val, (int, float)):
            return self._validate_numerical_range(float(val), factor_name), provenance_list

        # Dictionary representation
        if isinstance(val, dict):
            # Check for direct keys
            target = (
                val.get("score")
                if "score" in val
                else val.get("normalized_value")
                if "normalized_value" in val
                else val.get("value")
            )
            if target is None:
                return None, []
            if isinstance(target, bool):
                raise InvalidPriorityDataError(
                    f"Invalid factor '{factor_name}' value type 'bool' inside dict."
                )
            if "provenance" in val and val["provenance"]:
                p = val["provenance"]
                if isinstance(p, list):
                    provenance_list.extend(p)
                elif isinstance(p, dict):
                    provenance_list.append(p)
            return self._validate_numerical_range(float(target), factor_name), provenance_list

        # Object with normalized_value or score attribute
        if hasattr(val, "normalized_value") and getattr(val, "normalized_value") is not None:
            raw = getattr(val, "normalized_value")
            return self._validate_numerical_range(float(raw), factor_name), provenance_list

        if hasattr(val, "score") and getattr(val, "score") is not None:
            raw = getattr(val, "score")
            return self._validate_numerical_range(float(raw), factor_name), provenance_list

        raise InvalidPriorityDataError(
            f"Unsupported factor '{factor_name}' input type '{type(val).__name__}'. "
            f"Expected float, int, result envelope, or dictionary."
        )

    def _validate_numerical_range(self, val: float, factor_name: str) -> float:
        """Validate that a factor score is finite and bounded strictly to [0.0, 100.0]."""
        if math.isnan(val) or math.isinf(val):
            raise InvalidPriorityDataError(
                f"Factor '{factor_name}' value cannot be NaN or infinite (got {val})."
            )
        if not (0.0 <= val <= 100.0):
            raise InvalidPriorityDataError(
                f"Factor '{factor_name}' value {val} is outside valid range [0.0, 100.0]. "
                f"Safety guard: invalid factor scores are strictly rejected and never coerced."
            )
        return float(val)

    def _classify_band(self, score: float) -> RelocationPriorityBand:
        """Classify a 0-100 priority score into its authoritative RelocationPriorityBand."""
        cfg = self.bands_config
        if score >= cfg.immediate_min:
            return RelocationPriorityBand.IMMEDIATE
        elif score >= cfg.short_term_min:
            return RelocationPriorityBand.SHORT_TERM
        elif score >= cfg.medium_term_min:
            return RelocationPriorityBand.MEDIUM_TERM
        else:
            return RelocationPriorityBand.MONITOR

    def _build_factor_details(
        self,
        factor_values: Dict[PriorityFactorType, Optional[float]],
        score: Optional[float],
    ) -> List[PriorityFactorDetail]:
        """Build structured factor breakdown with weighted contributions and percentages."""
        w = self.weights_config
        weight_map = {
            PriorityFactorType.RISK: w.risk_weight,
            PriorityFactorType.EXPOSURE: w.exposure_weight,
            PriorityFactorType.VULNERABILITY: w.vulnerability_weight,
            PriorityFactorType.HISTORICAL_IMPACT: w.historical_impact_weight,
            PriorityFactorType.ACCESSIBILITY: w.accessibility_weight,
        }
        desc_map = {
            PriorityFactorType.RISK: "Multi-hazard composite risk (0.30H+0.20F+0.15R+0.15S+0.10D+0.10V)",
            PriorityFactorType.EXPOSURE: "Demographic exposure and high-risk sensitive population density",
            PriorityFactorType.VULNERABILITY: "Social and socioeconomic vulnerability index",
            PriorityFactorType.HISTORICAL_IMPACT: "Historical disaster frequency and past landslide impact",
            PriorityFactorType.ACCESSIBILITY: "Evacuation difficulty, road isolation, and winter cutoff risk",
        }

        details: List[PriorityFactorDetail] = []
        for ftype in (
            PriorityFactorType.RISK,
            PriorityFactorType.EXPOSURE,
            PriorityFactorType.VULNERABILITY,
            PriorityFactorType.HISTORICAL_IMPACT,
            PriorityFactorType.ACCESSIBILITY,
        ):
            val = factor_values.get(ftype)
            weight = weight_map[ftype]
            if val is not None:
                weighted_contrib = round(weight * val, 4)
                pct = (
                    round((weighted_contrib / score) * 100.0, 2)
                    if score is not None and score > 0.0
                    else 0.0
                )
                details.append(
                    PriorityFactorDetail(
                        factor_type=ftype,
                        factor_name=ftype.display_name,
                        symbol=ftype.symbol,
                        normalized_value=val,
                        weight=weight,
                        weighted_contribution=weighted_contrib,
                        contribution_percentage=pct,
                        is_available=True,
                        raw_value=val,
                        description=desc_map[ftype],
                    )
                )
            else:
                details.append(
                    PriorityFactorDetail(
                        factor_type=ftype,
                        factor_name=ftype.display_name,
                        symbol=ftype.symbol,
                        normalized_value=None,
                        weight=weight,
                        weighted_contribution=None,
                        contribution_percentage=None,
                        is_available=False,
                        raw_value=None,
                        description=desc_map[ftype],
                    )
                )

        return details

    def _get_formula_string(self) -> str:
        """Return human-readable formula string using configured weights."""
        w = self.weights_config
        return (
            f"RelocationPriority = {w.risk_weight:.2f}*Risk + {w.exposure_weight:.2f}*Exposure + "
            f"{w.vulnerability_weight:.2f}*Vulnerability + {w.historical_impact_weight:.2f}*HistoricalImpact + "
            f"{w.accessibility_weight:.2f}*Accessibility"
        )
