"""Unit tests for Chunk M3-08: Risk Explainability & Factor Contribution.

Verifies:
1. Complete computed risk: score preserved, all 6 factors represented, contributions exact.
2. Contribution sum matches composite score within numerical tolerance.
3. Factor contribution percentage calculation and sum-to-100% consistency.
4. Single-factor active scenarios: individual weights and dominant factor identification.
5. Boundary values: all 0.0, all 100.0, intermediate thresholds (25, 50, 70, 85).
6. Deterministic factor ranking (contribution descending with canonical tie-breaking).
7. Safety-critical missing factor handling: INSUFFICIENT_FACTORS preserves score=None.
8. Invalid numerical values handling: INVALID_INPUT preserves score=None.
9. Classification integration (M3-07): band preservation, interval notation, audit trail.
10. Incompatible classification detection: mismatched score or village_id raises error.
11. Optional classification: explain without M3-07 produces classification=None.
12. Strict determinism: repeated evaluations produce bit-for-bit identical results.
13. Regional configuration provenance tracking.
14. Convenience method `explain_computation` orchestrating M3-06 + M3-08.
15. Scope boundary enforcement: zero Red Zones, vulnerability scoring, or relocation priority.
"""

import math
import pytest

from app.core.profiles import get_profile
from app.core.profiles.models import RiskBand
from app.core.risk.classification.contracts import (
    RiskClassificationExplainability,
    RiskClassificationResult,
)
from app.core.risk.classification.engine import RiskClassificationEngine
from app.core.risk.computation.contracts import (
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorType,
)
from app.core.risk.computation.engine import REQUIRED_FACTORS, MultiHazardRiskEngine
from app.core.risk.explainability.contracts import (
    FACTOR_METADATA,
    CompositeRiskExplanation,
    FactorContributionDetail,
    FactorRanking,
)
from app.core.risk.explainability.engine import RiskExplainabilityEngine
from app.core.risk.explainability.errors import (
    IncompatibleClassificationError,
    RiskExplainabilityError,
)


@pytest.fixture
def risk_engine() -> MultiHazardRiskEngine:
    return MultiHazardRiskEngine()


@pytest.fixture
def explain_engine() -> RiskExplainabilityEngine:
    return RiskExplainabilityEngine()


# =====================================================================
# 1-3. Complete Computed Risk & Factor Breakdown
# =====================================================================


def test_complete_computed_risk_explanation(risk_engine, explain_engine):
    """1. Verify full factor breakdown, preserved score, weights, and narrative for a typical village."""
    # Typical realistic village factor values
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 75.0,              # Landslide zone
        RiskFactorType.FLOOD_EXPOSURE: 40.0,               # River buffer
        RiskFactorType.RAINFALL_INTENSITY: 80.0,           # Monsoon heavy rain
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 70.0, # Steep hill
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 50.0, # Moderate masonry
        RiskFactorType.SOCIAL_VULNERABILITY: 60.0,         # Elderly / remote
    }
    # Expected composite calculation:
    # 0.30*75 + 0.20*40 + 0.15*80 + 0.15*70 + 0.10*50 + 0.10*60
    # = 22.5 + 8.0 + 12.0 + 10.5 + 5.0 + 6.0 = 64.0
    comp_result = risk_engine.compute_risk(factors=factors, village_id="VILL_CHAMOLI_001")
    assert comp_result.status == RiskComputationStatus.COMPUTED
    assert comp_result.score == 64.0

    explanation = explain_engine.explain(comp_result)

    assert isinstance(explanation, CompositeRiskExplanation)
    assert explanation.village_id == "VILL_CHAMOLI_001"
    assert explanation.status == RiskComputationStatus.COMPUTED
    assert explanation.is_computable is True
    assert explanation.score == 64.0
    assert len(explanation.factor_contributions) == 6

    # Verify all 6 factors are present in canonical order
    for idx, factor in enumerate(REQUIRED_FACTORS):
        detail = explanation.factor_contributions[idx]
        assert detail.factor_type == factor
        assert detail.symbol == FACTOR_METADATA[factor]["symbol"]
        assert detail.factor_name == FACTOR_METADATA[factor]["name"]
        assert detail.normalized_value == factors[factor]
        assert detail.is_available is True

    # Check individual contributions
    contrib_map = {d.factor_type: d.weighted_contribution for d in explanation.factor_contributions}
    assert contrib_map[RiskFactorType.HAZARD_SEVERITY] == 22.5
    assert contrib_map[RiskFactorType.FLOOD_EXPOSURE] == 8.0
    assert contrib_map[RiskFactorType.RAINFALL_INTENSITY] == 12.0
    assert contrib_map[RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY] == 10.5
    assert contrib_map[RiskFactorType.INFRASTRUCTURE_VULNERABILITY] == 5.0
    assert contrib_map[RiskFactorType.SOCIAL_VULNERABILITY] == 6.0


def test_contribution_sum_matches_composite_score(risk_engine, explain_engine):
    """2. Verify that the sum of all weighted contributions strictly equals the composite score."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 63.4,
        RiskFactorType.FLOOD_EXPOSURE: 28.7,
        RiskFactorType.RAINFALL_INTENSITY: 91.2,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 45.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 33.3,
        RiskFactorType.SOCIAL_VULNERABILITY: 55.5,
    }
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result)

    total_contrib = sum(d.weighted_contribution for d in explanation.factor_contributions)
    assert math.isclose(total_contrib, explanation.score, abs_tol=1e-4)


def test_factor_contribution_percentages_sum_to_hundred(risk_engine, explain_engine):
    """3. Verify that factor contribution percentages sum to 100.0% within rounding tolerance."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 50.0,
        RiskFactorType.FLOOD_EXPOSURE: 50.0,
        RiskFactorType.RAINFALL_INTENSITY: 50.0,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 50.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 50.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 50.0,
    }
    comp_result = risk_engine.compute_risk(factors=factors)
    assert comp_result.score == 50.0

    explanation = explain_engine.explain(comp_result)
    total_pct = sum(d.contribution_percentage for d in explanation.factor_contributions)
    assert math.isclose(total_pct, 100.0, abs_tol=0.05)


# =====================================================================
# 4. Single-Factor Dominance Tests
# =====================================================================


@pytest.mark.parametrize(
    "active_factor,weight,expected_contrib",
    [
        (RiskFactorType.HAZARD_SEVERITY, 0.30, 30.0),
        (RiskFactorType.FLOOD_EXPOSURE, 0.20, 20.0),
        (RiskFactorType.RAINFALL_INTENSITY, 0.15, 15.0),
        (RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY, 0.15, 15.0),
        (RiskFactorType.INFRASTRUCTURE_VULNERABILITY, 0.10, 10.0),
        (RiskFactorType.SOCIAL_VULNERABILITY, 0.10, 10.0),
    ],
)
def test_single_active_factor_dominance(risk_engine, explain_engine, active_factor, weight, expected_contrib):
    """4. When only one factor is non-zero (100.0), it should contribute 100% of the score and be dominant."""
    factors = {f: 0.0 for f in REQUIRED_FACTORS}
    factors[active_factor] = 100.0

    comp_result = risk_engine.compute_risk(factors=factors)
    assert comp_result.score == expected_contrib

    explanation = explain_engine.explain(comp_result)
    assert explanation.dominant_factor == active_factor

    active_detail = next(d for d in explanation.factor_contributions if d.factor_type == active_factor)
    assert active_detail.weighted_contribution == expected_contrib
    assert active_detail.contribution_percentage == 100.0
    assert active_detail.weight == weight

    # Check ranking: active factor should be rank 1
    assert explanation.ranked_contributions[0].factor_type == active_factor
    assert explanation.ranked_contributions[0].rank == 1


# =====================================================================
# 5. Boundary Values
# =====================================================================


def test_all_zero_boundary(risk_engine, explain_engine):
    """5a. All factors at 0.0 produces score=0.0, contributions=0.0, dominant_factor=None, SAFE band."""
    factors = {f: 0.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    assert comp_result.score == 0.0

    explanation = explain_engine.explain(comp_result)
    assert explanation.score == 0.0
    assert explanation.dominant_factor is None
    for d in explanation.factor_contributions:
        assert d.weighted_contribution == 0.0
        assert d.contribution_percentage == 0.0

    assert explanation.classification is not None
    assert explanation.classification.band == RiskBand.SAFE
    assert "minimal baseline" in explanation.narrative_explanation


def test_all_hundred_boundary(risk_engine, explain_engine):
    """5b. All factors at 100.0 produces score=100.0, exact weight contributions, CRITICAL band."""
    factors = {f: 100.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    assert comp_result.score == 100.0

    explanation = explain_engine.explain(comp_result)
    assert explanation.score == 100.0
    assert explanation.dominant_factor == RiskFactorType.HAZARD_SEVERITY
    assert explanation.classification is not None
    assert explanation.classification.band == RiskBand.CRITICAL

    contrib_map = {d.factor_type: d.weighted_contribution for d in explanation.factor_contributions}
    assert contrib_map[RiskFactorType.HAZARD_SEVERITY] == 30.0
    assert contrib_map[RiskFactorType.FLOOD_EXPOSURE] == 20.0
    assert contrib_map[RiskFactorType.RAINFALL_INTENSITY] == 15.0
    assert contrib_map[RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY] == 15.0
    assert contrib_map[RiskFactorType.INFRASTRUCTURE_VULNERABILITY] == 10.0
    assert contrib_map[RiskFactorType.SOCIAL_VULNERABILITY] == 10.0


@pytest.mark.parametrize("boundary_val", [25.0, 50.0, 70.0, 85.0])
def test_uniform_factor_boundaries(risk_engine, explain_engine, boundary_val):
    """5c. Uniform factor values at band boundaries produce exact scores matching boundary."""
    factors = {f: boundary_val for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    assert math.isclose(comp_result.score, boundary_val, abs_tol=1e-4)

    explanation = explain_engine.explain(comp_result)
    assert math.isclose(explanation.score, boundary_val, abs_tol=1e-4)


# =====================================================================
# 6. Factor Ranking & Deterministic Tie-Breaking
# =====================================================================


def test_ranking_descending_order(risk_engine, explain_engine):
    """6a. Ranked contributions are sorted strictly in descending order of contribution."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 20.0,              # 0.30*20 = 6.0
        RiskFactorType.FLOOD_EXPOSURE: 50.0,               # 0.20*50 = 10.0
        RiskFactorType.RAINFALL_INTENSITY: 80.0,           # 0.15*80 = 12.0 (Top)
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 40.0, # 0.15*40 = 6.0
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 10.0, # 0.10*10 = 1.0
        RiskFactorType.SOCIAL_VULNERABILITY: 30.0,         # 0.10*30 = 3.0
    }
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result)

    ranks = explanation.ranked_contributions
    assert len(ranks) == 6
    assert ranks[0].factor_type == RiskFactorType.RAINFALL_INTENSITY
    assert ranks[0].weighted_contribution == 12.0
    assert ranks[1].factor_type == RiskFactorType.FLOOD_EXPOSURE
    assert ranks[1].weighted_contribution == 10.0

    # Check descending order
    for i in range(len(ranks) - 1):
        assert ranks[i].weighted_contribution >= ranks[i + 1].weighted_contribution


def test_ranking_tie_breaking_canonical_order(risk_engine, explain_engine):
    """6b. When contributions are tied, canonical factor order breaks ties deterministically."""
    # Set R and S to same contribution:
    # R: 0.15 * 40 = 6.0
    # S: 0.15 * 40 = 6.0
    # Canonical order: R comes before S
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 0.0,
        RiskFactorType.FLOOD_EXPOSURE: 0.0,
        RiskFactorType.RAINFALL_INTENSITY: 40.0,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 40.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 0.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 0.0,
    }
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result)

    assert explanation.ranked_contributions[0].factor_type == RiskFactorType.RAINFALL_INTENSITY
    assert explanation.ranked_contributions[1].factor_type == RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY


# =====================================================================
# 7. Safety-Critical Missing Factors (INSUFFICIENT_FACTORS)
# =====================================================================


def test_insufficient_factors_safety_preservation(risk_engine, explain_engine):
    """7. Missing factors strictly produce is_computable=False, score=None, and explicit missing list."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 80.0,
        RiskFactorType.FLOOD_EXPOSURE: 50.0,
        # Rainfall missing
        RiskFactorType.RAINFALL_INTENSITY: None,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 60.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 40.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 30.0,
    }
    comp_result = risk_engine.compute_risk(factors=factors, village_id="VILL_REMOTE_042")
    assert comp_result.status == RiskComputationStatus.INSUFFICIENT_FACTORS
    assert comp_result.score is None

    explanation = explain_engine.explain(comp_result)

    assert explanation.status == RiskComputationStatus.INSUFFICIENT_FACTORS
    assert explanation.is_computable is False
    assert explanation.score is None
    assert explanation.classification is None
    assert explanation.dominant_factor is None
    assert RiskFactorType.RAINFALL_INTENSITY in explanation.missing_factors

    # Verify narrative emphasizes safety guard
    assert "Assessment Incomplete" in explanation.narrative_explanation
    assert "Rainfall Intensity" in explanation.narrative_explanation
    assert "NEVER" in explanation.narrative_explanation
    assert "zero" in explanation.narrative_explanation

    # Factor detail for missing factor should have is_available=False and None contribution
    missing_detail = next(d for d in explanation.factor_contributions if d.factor_type == RiskFactorType.RAINFALL_INTENSITY)
    assert missing_detail.is_available is False
    assert missing_detail.normalized_value is None
    assert missing_detail.weighted_contribution is None


# =====================================================================
# 8. Invalid Numerical Input Handling
# =====================================================================


def test_invalid_input_safety_preservation(risk_engine, explain_engine):
    """8. Invalid factor values (NaN/Inf) produce INVALID_INPUT explanation with score=None."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: float("nan"),
        RiskFactorType.FLOOD_EXPOSURE: 50.0,
        RiskFactorType.RAINFALL_INTENSITY: 50.0,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 50.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 50.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 50.0,
    }
    comp_result = risk_engine.compute_risk(factors=factors)
    assert comp_result.status == RiskComputationStatus.INVALID_INPUT
    assert comp_result.score is None

    explanation = explain_engine.explain(comp_result)
    assert explanation.status == RiskComputationStatus.INVALID_INPUT
    assert explanation.is_computable is False
    assert explanation.score is None
    assert "Assessment Rejected" in explanation.narrative_explanation


# =====================================================================
# 9-11. Risk Classification Integration (M3-07)
# =====================================================================


def test_m3_07_classification_automatic_integration(risk_engine, explain_engine):
    """9a. Automatic classification integration assigns expected M3-07 band and interval notation."""
    # Score: 0.30*90 + 0.20*90 + 0.15*90 + 0.15*90 + 0.10*90 + 0.10*90 = 90.0 (CRITICAL)
    factors = {f: 90.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result, classify_if_needed=True)

    assert explanation.classification is not None
    assert explanation.classification.band == RiskBand.CRITICAL
    assert explanation.classification.band_name == "CRITICAL"
    assert explanation.classification.interval_notation == "[85.0, 100.0]"
    assert "CRITICAL" in explanation.narrative_explanation


def test_m3_07_explicit_classification_result_provided(risk_engine, explain_engine):
    """9b. Explicit pre-computed RiskClassificationResult is accepted and preserved."""
    factors = {f: 40.0 for f in REQUIRED_FACTORS}  # Score 40.0 -> MODERATE
    comp_result = risk_engine.compute_risk(factors=factors, village_id="VILL_007")

    classifier = RiskClassificationEngine()
    cls_result = classifier.classify(comp_result)

    explanation = explain_engine.explain(
        composite_result=comp_result,
        classification_result=cls_result,
    )
    assert explanation.classification is not None
    assert explanation.classification.band == RiskBand.MODERATE
    assert explanation.classification.band_name == "MODERATE"
    assert explanation.classification.interval_notation == "[25.0, 50.0)"


def test_incompatible_classification_score_raises_error(risk_engine, explain_engine):
    """10a. Provided classification result with mismatched score raises IncompatibleClassificationError."""
    factors = {f: 50.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)  # score = 50.0

    # Synthetic mismatched classification result with score = 75.0
    bad_cls = RiskClassificationResult(
        score=75.0,
        band=RiskBand.VERY_HIGH,
        village_id=None,
        explainability=RiskClassificationExplainability(
            band=RiskBand.VERY_HIGH,
            band_name="VERY_HIGH",
            score=75.0,
            interval_notation="[70.0, 85.0)",
            lower_bound=70.0,
            upper_bound=85.0,
            lower_inclusive=True,
            upper_inclusive=False,
            audit_trail="Mismatched score test",
        ),
    )

    with pytest.raises(IncompatibleClassificationError, match="does not match composite risk score"):
        explain_engine.explain(composite_result=comp_result, classification_result=bad_cls)


def test_incompatible_classification_village_id_raises_error(risk_engine, explain_engine):
    """10b. Provided classification result with mismatched village_id raises IncompatibleClassificationError."""
    factors = {f: 50.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors, village_id="VILL_ALPHA")

    bad_cls = RiskClassificationResult(
        score=50.0,
        band=RiskBand.HIGH,
        village_id="VILL_BETA",
        explainability=RiskClassificationExplainability(
            band=RiskBand.HIGH,
            band_name="HIGH",
            score=50.0,
            interval_notation="[50.0, 70.0)",
            lower_bound=50.0,
            upper_bound=70.0,
            lower_inclusive=True,
            upper_inclusive=False,
            audit_trail="Mismatched village test",
        ),
    )

    with pytest.raises(IncompatibleClassificationError, match="does not match composite result village_id"):
        explain_engine.explain(composite_result=comp_result, classification_result=bad_cls)


def test_unclassified_explanation_optionality(risk_engine, explain_engine):
    """11. When classify_if_needed=False and no classification passed, explanation remains valid with classification=None."""
    factors = {f: 50.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result, classify_if_needed=False)

    assert explanation.status == RiskComputationStatus.COMPUTED
    assert explanation.classification is None
    assert "unclassified" in explanation.narrative_explanation


# =====================================================================
# 12. Strict Determinism
# =====================================================================


def test_strict_explanation_determinism(risk_engine, explain_engine):
    """12. Repeated evaluations with identical inputs produce bit-for-bit identical explanation models."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 67.8,
        RiskFactorType.FLOOD_EXPOSURE: 34.5,
        RiskFactorType.RAINFALL_INTENSITY: 88.9,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 52.1,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 41.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 63.4,
    }
    comp1 = risk_engine.compute_risk(factors=factors, village_id="VILL_DET_01")
    comp2 = risk_engine.compute_risk(factors=factors, village_id="VILL_DET_01")

    exp1 = explain_engine.explain(comp1)
    exp2 = explain_engine.explain(comp2)

    assert exp1.model_dump() == exp2.model_dump()
    assert exp1.narrative_explanation == exp2.narrative_explanation
    assert exp1.audit_trail == exp2.audit_trail


# =====================================================================
# 13. Regional Configuration Provenance
# =====================================================================


def test_configuration_provenance_metadata(risk_engine, explain_engine):
    """13. Explanation metadata properly records regional profile source and weights."""
    factors = {f: 50.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result)

    prov = explanation.configuration_provenance
    assert prov is not None
    assert prov["profile_id"] == "himalayan_pilot"
    assert prov["source"] == "RegionProfileRegistry"
    assert prov["weights"]["hazard_weight"] == 0.30
    assert prov["weights"]["flood_weight"] == 0.20


# =====================================================================
# 14. Convenience Method: explain_computation
# =====================================================================


def test_explain_computation_orchestration(explain_engine):
    """14. explain_computation orchestrates M3-06 computation and M3-08 explanation seamlessly."""
    factors = {
        "H": 80.0,
        "F": 30.0,
        "R": 70.0,
        "S": 60.0,
        "D": 40.0,
        "V": 50.0,
    }
    explanation = explain_engine.explain_computation(
        factors=factors,
        village_id="VILL_DIRECT_01",
        classify=True,
    )
    # Expected: 0.30*80 + 0.20*30 + 0.15*70 + 0.15*60 + 0.10*40 + 0.10*50
    # = 24.0 + 6.0 + 10.5 + 9.0 + 4.0 + 5.0 = 58.5 (HIGH)
    assert explanation.score == 58.5
    assert explanation.village_id == "VILL_DIRECT_01"
    assert explanation.classification.band == RiskBand.HIGH
    assert explanation.dominant_factor == RiskFactorType.HAZARD_SEVERITY


# =====================================================================
# 15. Scope Boundary Checks
# =====================================================================


def test_scope_boundary_omissions(risk_engine, explain_engine):
    """15. Ensure M3-08 does not leak Red Zones (M3-10), vulnerability scoring (M3-09), or relocation (M3-12)."""
    factors = {f: 50.0 for f in REQUIRED_FACTORS}
    comp_result = risk_engine.compute_risk(factors=factors)
    explanation = explain_engine.explain(comp_result)

    data = explanation.model_dump()
    assert "red_zone" not in data
    assert "relocation_priority" not in data
    assert "evacuation_route" not in data
    assert "candidate_site" not in data
