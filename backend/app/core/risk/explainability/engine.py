"""Risk Explainability & Factor Contribution Engine for RakshakGIS (Chunk M3-08).

Decomposes and audits multi-hazard composite risk computation results (M3-06)
and integrated risk classification results (M3-07).
"""

import math
from typing import Any, Dict, List, Optional, Union

from app.core.profiles import get_profile
from app.core.profiles.models import RegionProfile
from app.core.risk.classification import RiskClassificationEngine
from app.core.risk.classification.contracts import RiskClassificationResult
from app.core.risk.computation.contracts import (
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorInput,
    RiskFactorType,
)
from app.core.risk.computation.engine import REQUIRED_FACTORS, MultiHazardRiskEngine
from app.core.risk.explainability.contracts import (
    FACTOR_METADATA,
    CompositeRiskExplanation,
    FactorContributionDetail,
    FactorRanking,
    RiskClassificationSummary,
)
from app.core.risk.explainability.errors import (
    IncompatibleClassificationError,
)
from app.core.risk.normalization.contracts import NormalizationResult
from app.data.providers.contracts import ProviderProvenance


class RiskExplainabilityEngine:
    """Deterministic, auditable engine for factor contribution decomposition and risk explainability."""

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        classification_engine: Optional[RiskClassificationEngine] = None,
    ):
        """Initialize the explainability engine with a regional profile and classification engine.

        Args:
            profile: Optional regional profile to source weights and metadata (defaults to Himalayan pilot).
            classification_engine: Optional classification engine instance (defaults to profile-backed engine).
        """
        self.profile = profile if profile is not None else get_profile("himalayan_pilot")
        self.classification_engine = (
            classification_engine
            if classification_engine is not None
            else RiskClassificationEngine(profile=self.profile)
        )

    def explain(
        self,
        composite_result: CompositeRiskResult,
        classification_result: Optional[RiskClassificationResult] = None,
        classify_if_needed: bool = True,
    ) -> CompositeRiskExplanation:
        """Generate a complete, structured explanation of an already-computed composite risk result.

        Args:
            composite_result: The M3-06 CompositeRiskResult to explain.
            classification_result: Optional pre-computed M3-07 RiskClassificationResult.
            classify_if_needed: If True and classification_result is None, automatically
                                runs M3-07 RiskClassificationEngine on valid computed scores.

        Returns:
            CompositeRiskExplanation containing factor breakdowns, rankings, narrative, and audit trail.

        Raises:
            IncompatibleClassificationError: If provided classification_result does not match composite_result.
        """
        config_provenance = {
            "profile_id": self.profile.id,
            "profile_name": self.profile.name,
            "source": "RegionProfileRegistry",
            "weights": self.profile.risk_weights.model_dump(),
        }

        # 1. Handle Incomplete / Missing Factor States (Safety-Critical Invariant)
        if composite_result.status == RiskComputationStatus.INSUFFICIENT_FACTORS:
            return self._build_insufficient_explanation(
                composite_result=composite_result,
                config_provenance=config_provenance,
            )

        # 2. Handle Invalid Input States
        if composite_result.status == RiskComputationStatus.INVALID_INPUT:
            return self._build_invalid_explanation(
                composite_result=composite_result,
                config_provenance=config_provenance,
            )

        # 3. Handle Computed Result
        score = composite_result.score
        if score is None:
            raise ValueError("Computed result cannot have None score.")

        weights_dict = composite_result.weights_used
        contributions_dict = composite_result.factor_contributions
        values_dict = composite_result.factor_values_used
        raw_values_dict = composite_result.explainability.raw_values_used

        # 4. Factor Contribution Details (Canonical Order: H, F, R, S, D, V)
        factor_details: List[FactorContributionDetail] = []
        for factor in REQUIRED_FACTORS:
            meta = FACTOR_METADATA[factor]
            val = values_dict.get(factor, 0.0)
            weight = weights_dict.get(factor, 0.0)
            contrib = contributions_dict.get(factor, round(weight * val, 4))
            pct = round((contrib / score) * 100.0, 2) if score > 0.0 else 0.0
            raw_val = raw_values_dict.get(factor)

            factor_details.append(
                FactorContributionDetail(
                    factor_type=factor,
                    symbol=meta["symbol"],
                    factor_name=meta["name"],
                    description=meta["description"],
                    normalized_value=val,
                    weight=weight,
                    weighted_contribution=contrib,
                    contribution_percentage=pct,
                    is_available=True,
                    raw_value=raw_val,
                )
            )

        # 5. Ranked Contributions (Deterministic Sort: Contribution Descending, then Canonical Factor Order)
        sorted_factors = sorted(
            REQUIRED_FACTORS,
            key=lambda f: (-contributions_dict.get(f, 0.0), REQUIRED_FACTORS.index(f)),
        )

        ranked_contributions: List[FactorRanking] = []
        for rank_idx, factor in enumerate(sorted_factors, start=1):
            meta = FACTOR_METADATA[factor]
            contrib = contributions_dict.get(factor, 0.0)
            pct = round((contrib / score) * 100.0, 2) if score > 0.0 else 0.0
            ranked_contributions.append(
                FactorRanking(
                    rank=rank_idx,
                    factor_type=factor,
                    symbol=meta["symbol"],
                    factor_name=meta["name"],
                    weighted_contribution=contrib,
                    contribution_percentage=pct,
                )
            )

        # Dominant factor is the #1 ranked contributor if overall risk > 0
        dominant_factor: Optional[RiskFactorType] = (
            sorted_factors[0] if score > 0.0 and contributions_dict.get(sorted_factors[0], 0.0) > 0.0 else None
        )

        # 6. Classification Integration (M3-07)
        classification_summary: Optional[RiskClassificationSummary] = None
        if classification_result is not None:
            # Validate mathematical consistency with provided classification
            if not math.isclose(classification_result.score, score, abs_tol=1e-4):
                raise IncompatibleClassificationError(
                    f"Classification score ({classification_result.score}) does not match "
                    f"composite risk score ({score})."
                )
            if (
                classification_result.village_id is not None
                and composite_result.village_id is not None
                and classification_result.village_id != composite_result.village_id
            ):
                raise IncompatibleClassificationError(
                    f"Classification village_id ('{classification_result.village_id}') does not match "
                    f"composite result village_id ('{composite_result.village_id}')."
                )
            classification_summary = RiskClassificationSummary(
                band=classification_result.band,
                band_name=classification_result.explainability.band_name,
                interval_notation=classification_result.explainability.interval_notation,
                audit_trail=classification_result.explainability.audit_trail,
            )
        elif classify_if_needed:
            # Safely invoke M3-07 engine without duplicating classification logic
            res = self.classification_engine.classify(score, village_id=composite_result.village_id)
            classification_summary = RiskClassificationSummary(
                band=res.band,
                band_name=res.explainability.band_name,
                interval_notation=res.explainability.interval_notation,
                audit_trail=res.explainability.audit_trail,
            )

        # 7. Deterministic Narrative Synthesis
        formula = composite_result.explainability.formula_derivation
        narrative = self._synthesize_narrative(
            village_id=composite_result.village_id,
            score=score,
            classification_summary=classification_summary,
            dominant_factor=dominant_factor,
            factor_details=factor_details,
            formula=formula,
        )

        audit_trail = (
            f"{composite_result.explainability.audit_trail} | "
            f"Band: {classification_summary.band_name if classification_summary else 'UNCLASSIFIED'} | "
            f"Dominant: {dominant_factor.value if dominant_factor else 'NONE'}"
        )

        return CompositeRiskExplanation(
            village_id=composite_result.village_id,
            status=RiskComputationStatus.COMPUTED,
            score=score,
            is_computable=True,
            formula=formula,
            weights_used=weights_dict,
            factor_contributions=factor_details,
            ranked_contributions=ranked_contributions,
            dominant_factor=dominant_factor,
            missing_factors=[],
            classification=classification_summary,
            narrative_explanation=narrative,
            audit_trail=audit_trail,
            configuration_provenance=config_provenance,
            provenance=composite_result.provenance,
        )

    def explain_computation(
        self,
        factors: Union[
            Dict[Union[RiskFactorType, str], Union[float, int, RiskFactorInput, NormalizationResult, None]],
            List[RiskFactorInput],
        ],
        village_id: Optional[str] = None,
        classify: bool = True,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> CompositeRiskExplanation:
        """Convenience method: runs M3-06 computation engine then explains the result.

        Args:
            factors: Input factors consumed by MultiHazardRiskEngine.
            village_id: Optional entity/village identifier.
            classify: Whether to automatically classify the risk score with M3-07.
            provenance: Optional provider provenance metadata.

        Returns:
            CompositeRiskExplanation envelope.
        """
        risk_engine = MultiHazardRiskEngine(profile=self.profile)
        comp_res = risk_engine.compute_risk(
            factors=factors,
            village_id=village_id,
            provenance=provenance,
        )
        return self.explain(composite_result=comp_res, classify_if_needed=classify)

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _build_insufficient_explanation(
        self,
        composite_result: CompositeRiskResult,
        config_provenance: Dict[str, Any],
    ) -> CompositeRiskExplanation:
        """Construct structured explanation for INSUFFICIENT_FACTORS ensuring score is None."""
        missing = list(composite_result.missing_factors)
        weights_dict = composite_result.weights_used

        factor_details: List[FactorContributionDetail] = []
        for factor in REQUIRED_FACTORS:
            meta = FACTOR_METADATA[factor]
            is_avail = factor not in missing
            weight = weights_dict.get(factor, 0.0)

            factor_details.append(
                FactorContributionDetail(
                    factor_type=factor,
                    symbol=meta["symbol"],
                    factor_name=meta["name"],
                    description=meta["description"],
                    normalized_value=None,
                    weight=weight,
                    weighted_contribution=None,
                    contribution_percentage=None,
                    is_available=is_avail,
                    raw_value=None,
                )
            )

        missing_labels = [f"{FACTOR_METADATA[f]['name']} ({FACTOR_METADATA[f]['symbol']})" for f in missing]
        entity_name = f"Village '{composite_result.village_id}'" if composite_result.village_id else "Assessed entity"
        narrative = (
            f"Assessment Incomplete: Multi-hazard composite risk could not be computed for {entity_name} "
            f"due to missing or unmonitored factor data for: {', '.join(missing_labels)}. "
            f"Safety Guard: In accordance with disaster safety protocols, unobserved factors are NEVER "
            f"silently coerced to zero risk."
        )

        return CompositeRiskExplanation(
            village_id=composite_result.village_id,
            status=RiskComputationStatus.INSUFFICIENT_FACTORS,
            score=None,
            is_computable=False,
            formula=composite_result.explainability.formula_derivation,
            weights_used=weights_dict,
            factor_contributions=factor_details,
            ranked_contributions=[],
            dominant_factor=None,
            missing_factors=missing,
            classification=None,
            narrative_explanation=narrative,
            audit_trail=composite_result.explainability.audit_trail,
            configuration_provenance=config_provenance,
            provenance=composite_result.provenance,
        )

    def _build_invalid_explanation(
        self,
        composite_result: CompositeRiskResult,
        config_provenance: Dict[str, Any],
    ) -> CompositeRiskExplanation:
        """Construct structured explanation for INVALID_INPUT ensuring score is None."""
        weights_dict = composite_result.weights_used
        factor_details: List[FactorContributionDetail] = []
        for factor in REQUIRED_FACTORS:
            meta = FACTOR_METADATA[factor]
            factor_details.append(
                FactorContributionDetail(
                    factor_type=factor,
                    symbol=meta["symbol"],
                    factor_name=meta["name"],
                    description=meta["description"],
                    normalized_value=None,
                    weight=weights_dict.get(factor, 0.0),
                    weighted_contribution=None,
                    contribution_percentage=None,
                    is_available=False,
                    raw_value=None,
                )
            )

        reason = composite_result.diagnostic_message or "Unknown numerical validation failure"
        narrative = (
            f"Assessment Rejected: Composite risk calculation rejected due to invalid numerical input: {reason}. "
            f"Safety Guard: Non-finite numbers (NaN, infinity) and out-of-domain values are strictly rejected."
        )

        return CompositeRiskExplanation(
            village_id=composite_result.village_id,
            status=RiskComputationStatus.INVALID_INPUT,
            score=None,
            is_computable=False,
            formula=composite_result.explainability.formula_derivation,
            weights_used=weights_dict,
            factor_contributions=factor_details,
            ranked_contributions=[],
            dominant_factor=None,
            missing_factors=[],
            classification=None,
            narrative_explanation=narrative,
            audit_trail=composite_result.explainability.audit_trail,
            configuration_provenance=config_provenance,
            provenance=composite_result.provenance,
        )

    def _synthesize_narrative(
        self,
        village_id: Optional[str],
        score: float,
        classification_summary: Optional[RiskClassificationSummary],
        dominant_factor: Optional[RiskFactorType],
        factor_details: List[FactorContributionDetail],
        formula: str,
    ) -> str:
        """Synthesize a deterministic, transparent explanation narrative."""
        entity = f"Village '{village_id}'" if village_id else "Assessed entity"
        band_clause = (
            f"classified as {classification_summary.band_name} ({classification_summary.interval_notation})"
            if classification_summary
            else "unclassified"
        )

        lines: List[str] = [
            f"{entity} has an evaluated multi-hazard composite risk score of {score:.2f} / 100.00 ({band_clause})."
        ]

        if dominant_factor is not None:
            dom_meta = FACTOR_METADATA[dominant_factor]
            dom_detail = next(d for d in factor_details if d.factor_type == dominant_factor)
            contrib = dom_detail.weighted_contribution or 0.0
            pct = dom_detail.contribution_percentage or 0.0
            lines.append(
                f"Primary hazard/vulnerability driver is {dom_meta['name']} ({dom_meta['symbol']}) "
                f"with a normalized factor of {dom_detail.normalized_value:.1f}, contributing {contrib:.2f} points "
                f"({pct:.1f}% of total risk)."
            )
        elif score == 0.0:
            lines.append("All hazard and vulnerability factors are at minimal baseline (0.00 points).")

        # Compact breakdown of all 6 factors
        breakdown_items = [
            f"{d.symbol}={d.weighted_contribution:.2f} (val={d.normalized_value:.1f}, w={d.weight:.2f})"
            for d in factor_details
            if d.weighted_contribution is not None and d.normalized_value is not None
        ]
        if breakdown_items:
            lines.append(f"Factor breakdown: {', '.join(breakdown_items)}.")

        lines.append(f"Applied formula: {formula}.")
        return " ".join(lines)
