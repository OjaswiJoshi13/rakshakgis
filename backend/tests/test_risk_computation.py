"""Unit tests for Chunk M3-06: Multi-Hazard Risk Computation Engine.

Verifies:
1. All-zero factors => 0.0
2. All-100 factors => 100.0
3. Individual factors at 100 => exact weight * 100
4. Mixed values => exact weighted result
5. Factors at boundaries 0 and 100
6. Final result remains within [0.0, 100.0]
7. Unavailable factor is NOT treated as zero
8. Missing factor produces structured unavailable/insufficient-input result
9. NaN / infinity / invalid values are rejected
10. Weight configuration sums correctly to 1.0
11. Contribution breakdown is correct and sums to final score
12. Deterministic repeated computation gives identical output
13. M3-05 NormalizationResult integration
14. Scope boundary: no risk bands or Red Zones
"""

import math
import pytest

from app.core.profiles import get_profile
from app.core.risk.computation.contracts import (
    CompositeRiskResult,
    RiskComputationStatus,
    RiskFactorInput,
    RiskFactorType,
    RiskWeightsConfig,
)
from app.core.risk.computation.engine import MultiHazardRiskEngine
from app.core.risk.computation.errors import (
    InvalidFactorValueError,
    WeightConfigurationError,
)
from app.core.risk.normalization.contracts import (
    FactorCategory,
    NormalizationExplainability,
    NormalizationMethod,
    NormalizationResult,
    NormalizationStatus,
)


@pytest.fixture
def default_engine() -> MultiHazardRiskEngine:
    return MultiHazardRiskEngine()


# =====================================================================
# 1-3. Boundary and Single Factor Weight Tests
# =====================================================================


def test_all_zero_factors_produce_zero(default_engine):
    """1. All factors at 0.0 produce composite risk score of 0.0."""
    res = default_engine.compute_from_values(
        hazard_severity=0.0,
        flood_exposure=0.0,
        rainfall_intensity=0.0,
        slope_landslide_susceptibility=0.0,
        infrastructure_vulnerability=0.0,
        social_vulnerability=0.0,
    )
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == 0.0
    for factor, contrib in res.factor_contributions.items():
        assert contrib == 0.0


def test_all_hundred_factors_produce_hundred(default_engine):
    """2. All factors at 100.0 produce composite risk score of 100.0."""
    res = default_engine.compute_from_values(
        hazard_severity=100.0,
        flood_exposure=100.0,
        rainfall_intensity=100.0,
        slope_landslide_susceptibility=100.0,
        infrastructure_vulnerability=100.0,
        social_vulnerability=100.0,
    )
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == 100.0
    assert res.factor_contributions[RiskFactorType.HAZARD_SEVERITY] == 30.0
    assert res.factor_contributions[RiskFactorType.FLOOD_EXPOSURE] == 20.0
    assert res.factor_contributions[RiskFactorType.RAINFALL_INTENSITY] == 15.0
    assert res.factor_contributions[RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY] == 15.0
    assert res.factor_contributions[RiskFactorType.INFRASTRUCTURE_VULNERABILITY] == 10.0
    assert res.factor_contributions[RiskFactorType.SOCIAL_VULNERABILITY] == 10.0


@pytest.mark.parametrize(
    "active_factor,expected_score",
    [
        (RiskFactorType.HAZARD_SEVERITY, 30.0),
        (RiskFactorType.FLOOD_EXPOSURE, 20.0),
        (RiskFactorType.RAINFALL_INTENSITY, 15.0),
        (RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY, 15.0),
        (RiskFactorType.INFRASTRUCTURE_VULNERABILITY, 10.0),
        (RiskFactorType.SOCIAL_VULNERABILITY, 10.0),
    ],
)
def test_individual_factors_at_hundred(default_engine, active_factor, expected_score):
    """3. Each individual factor at 100 with others at 0 produces exact weight*100."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 0.0,
        RiskFactorType.FLOOD_EXPOSURE: 0.0,
        RiskFactorType.RAINFALL_INTENSITY: 0.0,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 0.0,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 0.0,
        RiskFactorType.SOCIAL_VULNERABILITY: 0.0,
    }
    factors[active_factor] = 100.0

    res = default_engine.compute_risk(factors)
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == expected_score
    assert res.factor_contributions[active_factor] == expected_score


# =====================================================================
# 4-6. Mixed Values, Bounds & Invariants
# =====================================================================


def test_mixed_value_exact_summation(default_engine):
    """4. Mixed known values produce exact weighted sum:
    0.30(80) + 0.20(50) + 0.15(60) + 0.15(40) + 0.10(30) + 0.10(20)
    = 24 + 10 + 9 + 6 + 3 + 2 = 54.0
    """
    res = default_engine.compute_from_values(
        hazard_severity=80.0,
        flood_exposure=50.0,
        rainfall_intensity=60.0,
        slope_landslide_susceptibility=40.0,
        infrastructure_vulnerability=30.0,
        social_vulnerability=20.0,
    )
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == 54.0
    assert res.factor_contributions[RiskFactorType.HAZARD_SEVERITY] == 24.0
    assert res.factor_contributions[RiskFactorType.FLOOD_EXPOSURE] == 10.0
    assert res.factor_contributions[RiskFactorType.RAINFALL_INTENSITY] == 9.0
    assert res.factor_contributions[RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY] == 6.0
    assert res.factor_contributions[RiskFactorType.INFRASTRUCTURE_VULNERABILITY] == 3.0
    assert res.factor_contributions[RiskFactorType.SOCIAL_VULNERABILITY] == 2.0


def test_factors_at_boundaries(default_engine):
    """5. Factors strictly at boundary values (0.0 and 100.0) calculate properly."""
    res = default_engine.compute_from_values(
        hazard_severity=100.0,
        flood_exposure=0.0,
        rainfall_intensity=100.0,
        slope_landslide_susceptibility=0.0,
        infrastructure_vulnerability=100.0,
        social_vulnerability=0.0,
    )
    # 0.30*100 + 0 + 0.15*100 + 0 + 0.10*100 + 0 = 30 + 15 + 10 = 55.0
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == 55.0


def test_final_score_bounded_zero_to_hundred(default_engine):
    """6. The final composite risk score strictly satisfies 0.0 <= score <= 100.0."""
    res = default_engine.compute_from_values(
        hazard_severity=99.9,
        flood_exposure=99.9,
        rainfall_intensity=99.9,
        slope_landslide_susceptibility=99.9,
        infrastructure_vulnerability=99.9,
        social_vulnerability=99.9,
    )
    assert res.status == RiskComputationStatus.COMPUTED
    assert 0.0 <= res.score <= 100.0
    assert not math.isnan(res.score)
    assert not math.isinf(res.score)


# =====================================================================
# 7-8. Safety-Critical Missing / Unavailable Handling
# =====================================================================


def test_unavailable_factor_is_not_treated_as_zero(default_engine):
    """7. Safety-critical: Unavailable factor NEVER defaults to 0 risk."""
    # If social vulnerability (V) was silently treated as 0: score would be 52.0 (54 - 2)
    # The engine must refuse to fabricate a score and return score=None with INSUFFICIENT_FACTORS
    res = default_engine.compute_from_values(
        hazard_severity=80.0,
        flood_exposure=50.0,
        rainfall_intensity=60.0,
        slope_landslide_susceptibility=40.0,
        infrastructure_vulnerability=30.0,
        social_vulnerability=None,  # MISSING!
    )
    assert res.status == RiskComputationStatus.INSUFFICIENT_FACTORS
    assert res.score is None
    assert RiskFactorType.SOCIAL_VULNERABILITY in res.missing_factors
    assert "Missing or unmonitored factors are never silently coerced to zero" in res.diagnostic_message


def test_missing_factor_produces_structured_insufficient_result(default_engine):
    """8. Omission of required factors yields structured result with missing_factors list."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 50.0,
        RiskFactorType.FLOOD_EXPOSURE: 50.0,
        # rainfall, slope, infrastructure, social are omitted
    }
    res = default_engine.compute_risk(factors)
    assert res.status == RiskComputationStatus.INSUFFICIENT_FACTORS
    assert res.score is None
    assert len(res.missing_factors) == 4
    assert RiskFactorType.RAINFALL_INTENSITY in res.missing_factors
    assert RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY in res.missing_factors
    assert RiskFactorType.INFRASTRUCTURE_VULNERABILITY in res.missing_factors
    assert RiskFactorType.SOCIAL_VULNERABILITY in res.missing_factors


# =====================================================================
# 9-10. Input Validation & Weight Configuration
# =====================================================================


def test_nan_and_infinity_rejected(default_engine):
    """9. NaN, Infinity, and out-of-range values produce INVALID_INPUT status."""
    res_nan = default_engine.compute_from_values(
        hazard_severity=float("nan"),
        flood_exposure=50.0,
        rainfall_intensity=50.0,
        slope_landslide_susceptibility=50.0,
        infrastructure_vulnerability=50.0,
        social_vulnerability=50.0,
    )
    assert res_nan.status == RiskComputationStatus.INVALID_INPUT
    assert res_nan.score is None

    res_inf = default_engine.compute_from_values(
        hazard_severity=float("inf"),
        flood_exposure=50.0,
        rainfall_intensity=50.0,
        slope_landslide_susceptibility=50.0,
        infrastructure_vulnerability=50.0,
        social_vulnerability=50.0,
    )
    assert res_inf.status == RiskComputationStatus.INVALID_INPUT
    assert res_inf.score is None

    res_out_of_range = default_engine.compute_from_values(
        hazard_severity=150.0,
        flood_exposure=50.0,
        rainfall_intensity=50.0,
        slope_landslide_susceptibility=50.0,
        infrastructure_vulnerability=50.0,
        social_vulnerability=50.0,
    )
    assert res_out_of_range.status == RiskComputationStatus.INVALID_INPUT
    assert res_out_of_range.score is None


def test_weight_configuration_sums_correctly():
    """10. Weights must sum to 1.0; invalid weight configs are rejected."""
    weights = RiskWeightsConfig()
    total = sum(weights.as_dict().values())
    assert math.isclose(total, 1.0, rel_tol=1e-5)

    with pytest.raises(WeightConfigurationError, match="must sum to 1.0"):
        RiskWeightsConfig(
            hazard_severity=0.50,
            flood_exposure=0.50,
            rainfall_intensity=0.50,
            slope_landslide_susceptibility=0.15,
            infrastructure_vulnerability=0.10,
            social_vulnerability=0.10,
        )


# =====================================================================
# 11-12. Explainability & Determinism
# =====================================================================


def test_contribution_breakdown_matches_final_score(default_engine):
    """11. Factor contributions exactly sum to the final composite score."""
    res = default_engine.compute_from_values(
        hazard_severity=75.5,
        flood_exposure=45.0,
        rainfall_intensity=65.2,
        slope_landslide_susceptibility=55.0,
        infrastructure_vulnerability=35.0,
        social_vulnerability=25.0,
    )
    assert res.status == RiskComputationStatus.COMPUTED
    contributions_sum = sum(res.factor_contributions.values())
    assert math.isclose(res.score, contributions_sum, rel_tol=1e-3, abs_tol=1e-3)
    assert res.explainability.formula_derivation.startswith("Risk =")
    assert "Risk score = " in res.explainability.audit_trail


def test_deterministic_repeated_computation(default_engine):
    """12. Identical input factors produce identical output (determinism and idempotency)."""
    factors = {
        RiskFactorType.HAZARD_SEVERITY: 62.3,
        RiskFactorType.FLOOD_EXPOSURE: 41.8,
        RiskFactorType.RAINFALL_INTENSITY: 88.0,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: 33.5,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: 19.4,
        RiskFactorType.SOCIAL_VULNERABILITY: 52.1,
    }
    res1 = default_engine.compute_risk(factors, village_id="VIL-001")
    res2 = default_engine.compute_risk(factors, village_id="VIL-001")
    assert res1.model_dump() == res2.model_dump()


# =====================================================================
# 13. M3-05 NormalizationResult Integration
# =====================================================================


def test_integration_with_m3_05_normalization_results(default_engine):
    """13. MultiHazardRiskEngine directly consumes NormalizationResult instances from M3-05."""
    norm_h = NormalizationResult(
        record_id="h_01",
        factor_category=FactorCategory.LANDSLIDE,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value=5000.0,
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.LINEAR,
            parameters_used={},
            formula_description="Landslide debris linear scaling",
        ),
    )
    norm_f = NormalizationResult(
        record_id="f_01",
        factor_category=FactorCategory.FLOOD,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value=2.5,
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.LINEAR,
            parameters_used={},
            formula_description="Flood water level linear scaling",
        ),
    )
    norm_r = NormalizationResult(
        record_id="r_01",
        factor_category=FactorCategory.RAINFALL,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value=64.5,
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.THRESHOLD_PIECEWISE,
            parameters_used={},
            formula_description="Rainfall IMD piecewise interpolation",
        ),
    )
    norm_s = NormalizationResult(
        record_id="s_01",
        factor_category=FactorCategory.SEISMIC,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value=7.0,
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.THRESHOLD_PIECEWISE,
            parameters_used={},
            formula_description="Seismic MMI interpolation",
        ),
    )
    norm_d = NormalizationResult(
        record_id="d_01",
        factor_category=FactorCategory.HAZARD_OBSERVATION,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value="moderate",
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.CATEGORICAL_SEVERITY,
            parameters_used={},
            formula_description="Infrastructure severity mapping",
        ),
    )
    norm_v = NormalizationResult(
        record_id="v_01",
        factor_category=FactorCategory.HAZARD_OBSERVATION,
        status=NormalizationStatus.NORMALIZED,
        raw_input_value="moderate",
        normalized_value=50.0,
        explainability=NormalizationExplainability(
            method=NormalizationMethod.CATEGORICAL_SEVERITY,
            parameters_used={},
            formula_description="Social vulnerability severity mapping",
        ),
    )

    factors = {
        RiskFactorType.HAZARD_SEVERITY: norm_h,
        RiskFactorType.FLOOD_EXPOSURE: norm_f,
        RiskFactorType.RAINFALL_INTENSITY: norm_r,
        RiskFactorType.SLOPE_LANDSLIDE_SUSCEPTIBILITY: norm_s,
        RiskFactorType.INFRASTRUCTURE_VULNERABILITY: norm_d,
        RiskFactorType.SOCIAL_VULNERABILITY: norm_v,
    }

    res = default_engine.compute_risk(factors, village_id="VIL-INTEG-01")
    assert res.status == RiskComputationStatus.COMPUTED
    assert res.score == 50.0
    assert res.village_id == "VIL-INTEG-01"
    assert res.explainability.raw_values_used[RiskFactorType.HAZARD_SEVERITY] == 5000.0


# =====================================================================
# 14. Scope Boundary Check
# =====================================================================


def test_scope_boundary_no_classification_or_red_zones(default_engine):
    """14. Engine does NOT compute risk bands, Red Zones, or relocation priorities."""
    assert not hasattr(default_engine, "classify_risk_band")
    assert not hasattr(default_engine, "assign_risk_band")
    assert not hasattr(default_engine, "demarcate_red_zone")
    assert not hasattr(default_engine, "compute_relocation_priority")
