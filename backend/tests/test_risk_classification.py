"""Unit tests for Chunk M3-07: Risk Classification & Grading Engine.

Verifies:
1. 0 -> SAFE
2. value below 25 -> SAFE
3. 24.999... -> SAFE
4. 25 -> MODERATE
5. value below 50 -> MODERATE
6. 50 -> HIGH
7. value below 70 -> HIGH
8. 70 -> VERY_HIGH
9. value below 85 -> VERY_HIGH
10. 85 -> CRITICAL
11. 100 -> CRITICAL
12. invalid negative score rejected
13. invalid score >100 rejected
14. NaN rejected
15. infinity rejected
16. classification is deterministic
17. original score is preserved in the result
18. explainability identifies the selected band/range
19. integration with M3-06 CompositeRiskResult
20. incomplete CompositeRiskResult rejected
21. configuration validation (monotonic cutoffs)
22. scope boundary: no Red Zones or relocation priority
"""

import math
import pytest

from app.core.profiles.models import RiskBand
from app.core.risk.classification.contracts import (
    RiskClassificationResult,
    RiskScoreBandsConfig,
)
from app.core.risk.classification.engine import RiskClassificationEngine
from app.core.risk.classification.errors import (
    ClassificationBandConfigError,
    InvalidRiskScoreError,
)
from app.core.risk.computation.contracts import (
    CompositeRiskExplainability,
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorType,
)


@pytest.fixture
def classifier() -> RiskClassificationEngine:
    return RiskClassificationEngine()


# =====================================================================
# 1-11. Boundary & Interval Classification Tests
# =====================================================================


def test_zero_maps_to_safe(classifier):
    """1. Score of 0.0 maps to SAFE."""
    res = classifier.classify(0.0)
    assert res.band == RiskBand.SAFE
    assert res.score == 0.0
    assert res.explainability.lower_bound == 0.0
    assert res.explainability.upper_bound == 25.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is False


def test_value_below_25_maps_to_safe(classifier):
    """2. Score strictly below 25.0 (e.g. 14.5) maps to SAFE."""
    res = classifier.classify(14.5)
    assert res.band == RiskBand.SAFE
    assert res.score == 14.5


def test_boundary_just_below_25_maps_to_safe(classifier):
    """3. Boundary value 24.9999 maps to SAFE."""
    res = classifier.classify(24.9999)
    assert res.band == RiskBand.SAFE
    assert res.score == 24.9999


def test_boundary_25_maps_to_moderate(classifier):
    """4. Boundary value 25.0 maps to MODERATE (inclusive lower bound)."""
    res = classifier.classify(25.0)
    assert res.band == RiskBand.MODERATE
    assert res.score == 25.0
    assert res.explainability.lower_bound == 25.0
    assert res.explainability.upper_bound == 50.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is False


def test_value_below_50_maps_to_moderate(classifier):
    """5. Score between 25.0 and 50.0 (e.g. 37.5) maps to MODERATE."""
    res = classifier.classify(37.5)
    assert res.band == RiskBand.MODERATE
    assert res.score == 37.5

    # Just below 50.0
    res_edge = classifier.classify(49.9999)
    assert res_edge.band == RiskBand.MODERATE
    assert res_edge.score == 49.9999


def test_boundary_50_maps_to_high(classifier):
    """6. Boundary value 50.0 maps to HIGH (inclusive lower bound)."""
    res = classifier.classify(50.0)
    assert res.band == RiskBand.HIGH
    assert res.score == 50.0
    assert res.explainability.lower_bound == 50.0
    assert res.explainability.upper_bound == 70.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is False


def test_value_below_70_maps_to_high(classifier):
    """7. Score between 50.0 and 70.0 (e.g. 62.3) maps to HIGH."""
    res = classifier.classify(62.3)
    assert res.band == RiskBand.HIGH
    assert res.score == 62.3

    # Just below 70.0
    res_edge = classifier.classify(69.9999)
    assert res_edge.band == RiskBand.HIGH
    assert res_edge.score == 69.9999


def test_boundary_70_maps_to_very_high(classifier):
    """8. Boundary value 70.0 maps to VERY_HIGH (inclusive lower bound)."""
    res = classifier.classify(70.0)
    assert res.band == RiskBand.VERY_HIGH
    assert res.score == 70.0
    assert res.explainability.lower_bound == 70.0
    assert res.explainability.upper_bound == 85.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is False


def test_value_below_85_maps_to_very_high(classifier):
    """9. Score between 70.0 and 85.0 (e.g. 78.4) maps to VERY_HIGH."""
    res = classifier.classify(78.4)
    assert res.band == RiskBand.VERY_HIGH
    assert res.score == 78.4

    # Just below 85.0
    res_edge = classifier.classify(84.9999)
    assert res_edge.band == RiskBand.VERY_HIGH
    assert res_edge.score == 84.9999


def test_boundary_85_maps_to_critical(classifier):
    """10. Boundary value 85.0 maps to CRITICAL (inclusive lower bound)."""
    res = classifier.classify(85.0)
    assert res.band == RiskBand.CRITICAL
    assert res.score == 85.0
    assert res.explainability.lower_bound == 85.0
    assert res.explainability.upper_bound == 100.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is True


def test_boundary_100_maps_to_critical(classifier):
    """11. Boundary value 100.0 maps to CRITICAL (inclusive upper bound)."""
    res = classifier.classify(100.0)
    assert res.band == RiskBand.CRITICAL
    assert res.score == 100.0
    assert res.explainability.lower_bound == 85.0
    assert res.explainability.upper_bound == 100.0
    assert res.explainability.lower_inclusive is True
    assert res.explainability.upper_inclusive is True


# =====================================================================
# 12-15. Rejection of Invalid Numeric Inputs (No Clamping)
# =====================================================================


def test_invalid_negative_score_rejected(classifier):
    """12. Scores below 0.0 are strictly rejected and NEVER clamped to SAFE."""
    with pytest.raises(InvalidRiskScoreError, match="out of valid bounds"):
        classifier.classify(-0.001)

    with pytest.raises(InvalidRiskScoreError, match="out of valid bounds"):
        classifier.classify(-25.0)


def test_invalid_score_above_100_rejected(classifier):
    """13. Scores above 100.0 are strictly rejected and NEVER clamped to CRITICAL."""
    with pytest.raises(InvalidRiskScoreError, match="out of valid bounds"):
        classifier.classify(100.0001)

    with pytest.raises(InvalidRiskScoreError, match="out of valid bounds"):
        classifier.classify(150.0)


def test_nan_score_rejected(classifier):
    """14. NaN scores are rejected."""
    with pytest.raises(InvalidRiskScoreError, match="cannot classify NaN or infinite"):
        classifier.classify(float("nan"))


def test_infinity_score_rejected(classifier):
    """15. Positive and negative infinity scores are rejected."""
    with pytest.raises(InvalidRiskScoreError, match="cannot classify NaN or infinite"):
        classifier.classify(float("inf"))

    with pytest.raises(InvalidRiskScoreError, match="cannot classify NaN or infinite"):
        classifier.classify(float("-inf"))


def test_boolean_and_non_numeric_rejected(classifier):
    """Boolean and malformed non-numeric types are rejected."""
    with pytest.raises(InvalidRiskScoreError, match="Invalid risk score type 'bool'"):
        classifier.classify(True)

    with pytest.raises(InvalidRiskScoreError, match="Unsupported risk score input type"):
        classifier.classify("high")


# =====================================================================
# 16-18. Determinism, Precision Preservation & Explainability
# =====================================================================


def test_classification_is_strictly_deterministic(classifier):
    """16. Repeated classifications of identical scores produce identical results."""
    res1 = classifier.classify(54.321, village_id="VIL-101")
    res2 = classifier.classify(54.321, village_id="VIL-101")
    assert res1.model_dump() == res2.model_dump()


def test_original_score_preserved_exactly(classifier):
    """17. Original continuous score is preserved without precision loss."""
    raw_score = 67.891234
    res = classifier.classify(raw_score)
    assert res.score == raw_score
    assert math.isclose(res.score, 67.891234, abs_tol=1e-6)


def test_explainability_identifies_selected_band_and_range(classifier):
    """18. Explainability accurately captures interval notation, bounds, and audit trail."""
    res = classifier.classify(74.2)
    exp = res.explainability
    assert exp.band == RiskBand.VERY_HIGH
    assert exp.band_name == "VERY_HIGH"
    assert exp.interval_notation == "[70.0, 85.0)"
    assert exp.lower_bound == 70.0
    assert exp.upper_bound == 85.0
    assert exp.lower_inclusive is True
    assert exp.upper_inclusive is False
    assert "Score 74.2000 classified as VERY_HIGH based on interval [70.0, 85.0)" in exp.audit_trail


# =====================================================================
# 19-20. M3-06 CompositeRiskResult Integration & Incomplete Checks
# =====================================================================


def test_integration_with_m3_06_composite_risk_result(classifier):
    """19. Classifier cleanly ingests M3-06 CompositeRiskResult objects."""
    composite = CompositeRiskResult(
        village_id="VIL-042",
        score=59.0,
        status=RiskComputationStatus.COMPUTED,
        factor_contributions={
            RiskFactorType.HAZARD_SEVERITY: 24.0,
            RiskFactorType.FLOOD_EXPOSURE: 10.0,
            RiskFactorType.RAINFALL_INTENSITY: 9.0,
            RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 6.0,
            RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 7.0,
            RiskFactorType.SOCIAL_VULNERABILITY: 3.0,
        },
        factor_values_used={},
        weights_used={},
        missing_factors=[],
        explainability=CompositeRiskExplainability(
            formula_derivation="Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V",
            weights={},
            contributions={},
            normalized_factors_used={},
            audit_trail="Risk score = 59.0000",
        ),
    )
    res = classifier.classify(composite)
    assert res.score == 59.0
    assert res.band == RiskBand.HIGH
    assert res.village_id == "VIL-042"
    assert res.composite_result is composite


def test_incomplete_composite_result_rejected(classifier):
    """20. An incomplete M3-06 result (INSUFFICIENT_FACTORS, score=None) cannot be classified."""
    insufficient = CompositeRiskResult(
        village_id="VIL-099",
        score=None,
        status=RiskComputationStatus.INSUFFICIENT_FACTORS,
        missing_factors=[RiskFactorType.SOCIAL_VULNERABILITY],
        explainability=CompositeRiskExplainability(
            formula_derivation="Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V",
            weights={},
            contributions={},
            normalized_factors_used={},
            audit_trail="Computation aborted",
        ),
    )
    with pytest.raises(InvalidRiskScoreError, match="Cannot classify incomplete composite risk result"):
        classifier.classify(insufficient)


# =====================================================================
# 21-22. Configuration Validation & Scope Boundary Checks
# =====================================================================


def test_configuration_validation_strictly_increasing():
    """21. RiskScoreBandsConfig validates that cutoffs are strictly increasing."""
    # Valid default config
    cfg = RiskScoreBandsConfig()
    assert cfg.safe_max == 25.0
    assert cfg.critical_max == 100.0

    # Non-monotonic config rejected
    with pytest.raises(ClassificationBandConfigError, match="strictly increasing"):
        RiskScoreBandsConfig(
            safe_max=30.0,
            moderate_max=20.0,  # Invalid: moderate < safe
            high_max=70.0,
            very_high_max=85.0,
            critical_max=100.0,
        )

    # critical_max != 100 rejected
    with pytest.raises(ClassificationBandConfigError, match="critical_max must be 100.0"):
        RiskScoreBandsConfig(
            safe_max=25.0,
            moderate_max=50.0,
            high_max=70.0,
            very_high_max=85.0,
            critical_max=95.0,
        )


def test_scope_boundary_no_red_zones_or_relocation(classifier):
    """22. Classifier does NOT demarcate Red Zones or compute relocation priority."""
    assert not hasattr(classifier, "demarcate_red_zone")
    assert not hasattr(classifier, "is_red_zone")
    assert not hasattr(classifier, "compute_relocation_priority")
    assert not hasattr(classifier, "score_vulnerability")
