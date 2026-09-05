"""Comprehensive unit test suite for Relocation Priority Scoring Engine (Chunk M3-12).

Authoritative Formula:
  Relocation Priority = 0.40*Risk + 0.25*Exposure + 0.20*Vulnerability + 0.10*HistoricalImpact + 0.05*Accessibility

Authoritative Priority Bands:
  [80.0, 100.0] -> IMMEDIATE
  [60.0, 80.0)  -> SHORT_TERM
  [40.0, 60.0)  -> MEDIUM_TERM
  [0.0, 40.0)   -> MONITOR
"""

import math
import pytest
from datetime import datetime
from typing import Dict, Any

from app.core.profiles import get_profile
from app.core.profiles.models import (
    RegionProfile,
    RegionProfileId,
    RelocationPriorityBand,
)
from app.core.risk.computation.contracts import (
    CompositeRiskResult,
    RiskComputationStatus,
)
from app.core.risk.computation.engine import MultiHazardRiskEngine
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
from app.core.risk.relocation_priority.engine import RelocationPriorityEngine
from app.core.risk.relocation_priority.errors import (
    InsufficientPriorityDataError,
    InvalidPriorityDataError,
    PriorityConfigError,
    RelocationPriorityError,
)
from app.core.risk.vulnerability.contracts import (
    DemographicExposureResult,
    DemographicInput,
    ScoringStatus,
    SocialVulnerabilityResult,
    VulnerabilityInput,
)
from app.core.risk.vulnerability.engine import VulnerabilityExposureEngine
from app.data.providers.contracts import ProviderMode, ProviderProvenance


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def himalayan_profile() -> RegionProfile:
    return get_profile(RegionProfileId.HIMALAYAN_PILOT)


@pytest.fixture
def default_engine(himalayan_profile: RegionProfile) -> RelocationPriorityEngine:
    return RelocationPriorityEngine(profile=himalayan_profile)


@pytest.fixture
def sample_provenance() -> ProviderProvenance:
    return ProviderProvenance(
        provider_id="mock_relocation_provider",
        provider_name="Mock Relocation Assessment Provider",
        mode=ProviderMode.MOCK,
        is_synthetic=True,
        region_id="himalayan_pilot",
    )


# =====================================================================
# 1. Exact Formula Calculation with Known Factors
# =====================================================================


def test_exact_formula_calculation_with_known_factors(default_engine: RelocationPriorityEngine) -> None:
    """Verify formula: 0.40*80 + 0.25*60 + 0.20*50 + 0.10*40 + 0.05*20 = 62.00."""
    result = default_engine.evaluate(
        village_id="VIL-001",
        village_name="Joshimath Ward 4",
        risk=80.0,
        exposure=60.0,
        vulnerability=50.0,
        historical_impact=40.0,
        accessibility=20.0,
    )

    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score is not None
    assert math.isclose(result.priority_score, 62.00, abs_tol=1e-4)
    assert result.priority_band == RelocationPriorityBand.SHORT_TERM
    assert result.village_id == "VIL-001"
    assert result.village_name == "Joshimath Ward 4"
    assert result.is_actionable_proposal is True
    assert result.is_automatic_evacuation is False

    # Check individual contributions
    expected_contributions = {
        "risk": 32.00,
        "exposure": 15.00,
        "vulnerability": 10.00,
        "historical_impact": 4.00,
        "accessibility": 1.00,
    }
    for factor, expected_val in expected_contributions.items():
        assert math.isclose(result.factor_contributions[factor], expected_val, abs_tol=1e-4)

    # Primary driver check
    assert result.explainability.primary_driver == PriorityFactorType.RISK.display_name
    assert result.explainability.primary_driver_contribution == 32.00


# =====================================================================
# 2. Individual Factor Weight Verification
# =====================================================================


@pytest.mark.parametrize(
    ("active_factor", "factor_kwargs", "expected_score", "expected_band"),
    [
        ("risk", {"risk": 100.0, "exposure": 0.0, "vulnerability": 0.0, "historical_impact": 0.0, "accessibility": 0.0}, 40.0, RelocationPriorityBand.MEDIUM_TERM),
        ("exposure", {"risk": 0.0, "exposure": 100.0, "vulnerability": 0.0, "historical_impact": 0.0, "accessibility": 0.0}, 25.0, RelocationPriorityBand.MONITOR),
        ("vulnerability", {"risk": 0.0, "exposure": 0.0, "vulnerability": 100.0, "historical_impact": 0.0, "accessibility": 0.0}, 20.0, RelocationPriorityBand.MONITOR),
        ("historical_impact", {"risk": 0.0, "exposure": 0.0, "vulnerability": 0.0, "historical_impact": 100.0, "accessibility": 0.0}, 10.0, RelocationPriorityBand.MONITOR),
        ("accessibility", {"risk": 0.0, "exposure": 0.0, "vulnerability": 0.0, "historical_impact": 0.0, "accessibility": 100.0}, 5.0, RelocationPriorityBand.MONITOR),
    ],
)
def test_individual_factor_weights(
    default_engine: RelocationPriorityEngine,
    active_factor: str,
    factor_kwargs: Dict[str, float],
    expected_score: float,
    expected_band: RelocationPriorityBand,
) -> None:
    """Verify that each factor isolates its exact configured weight (0.40, 0.25, 0.20, 0.10, 0.05)."""
    result = default_engine.evaluate(village_id="VIL-WEIGHT", **factor_kwargs)
    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score is not None
    assert math.isclose(result.priority_score, expected_score, abs_tol=1e-4)
    assert result.priority_band == expected_band
    assert math.isclose(result.factor_contributions[active_factor], expected_score, abs_tol=1e-4)


# =====================================================================
# 3. All Factors at 0.0
# =====================================================================


def test_all_factors_zero(default_engine: RelocationPriorityEngine) -> None:
    """All 5 factors at 0.0 must yield priority score 0.0, MONITOR band, and honest 0.0% contributions without division by zero."""
    result = default_engine.evaluate(
        village_id="VIL-MIN",
        risk=0.0,
        exposure=0.0,
        vulnerability=0.0,
        historical_impact=0.0,
        accessibility=0.0,
    )
    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score == 0.0
    assert not math.isnan(result.priority_score)
    assert not math.isinf(result.priority_score)
    assert result.priority_band == RelocationPriorityBand.MONITOR
    assert result.explainability.was_clamped is False

    # Check that contribution_percentage does not fail with division by zero or invent percentages
    assert len(result.factor_details) == 5
    for detail in result.factor_details:
        assert detail.weighted_contribution == 0.0
        assert detail.contribution_percentage == 0.0
        assert not math.isnan(detail.contribution_percentage)
        assert not math.isinf(detail.contribution_percentage)

    # When all contributions are 0, there is no primary urgency driver
    assert result.explainability.primary_driver is None
    assert result.explainability.primary_driver_contribution is None
    assert "No urgency drivers active" in result.explainability.summary_narrative


def test_independent_formula_verification_hand_calculated(default_engine: RelocationPriorityEngine) -> None:
    """Independent formula check:
    Risk = 80, Exposure = 60, Vulnerability = 40, Historical Impact = 20, Accessibility = 10
    0.40*80 + 0.25*60 + 0.20*40 + 0.10*20 + 0.05*10 = 32.0 + 15.0 + 8.0 + 2.0 + 0.5 = 57.50
    Band: [40.0, 60.0) -> MEDIUM_TERM
    """
    result = default_engine.evaluate(
        village_id="VIL-HAND-CALC",
        village_name="Hand Calculated Test",
        risk=80.0,
        exposure=60.0,
        vulnerability=40.0,
        historical_impact=20.0,
        accessibility=10.0,
    )
    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score is not None
    assert math.isclose(result.priority_score, 57.50, abs_tol=1e-4)
    assert result.priority_band == RelocationPriorityBand.MEDIUM_TERM

    # Individual contributions
    assert math.isclose(result.factor_contributions["risk"], 32.0, abs_tol=1e-4)
    assert math.isclose(result.factor_contributions["exposure"], 15.0, abs_tol=1e-4)
    assert math.isclose(result.factor_contributions["vulnerability"], 8.0, abs_tol=1e-4)
    assert math.isclose(result.factor_contributions["historical_impact"], 2.0, abs_tol=1e-4)
    assert math.isclose(result.factor_contributions["accessibility"], 0.5, abs_tol=1e-4)

    # Sum of weights
    w = default_engine.weights_config
    total_weights = w.risk_weight + w.exposure_weight + w.vulnerability_weight + w.historical_impact_weight + w.accessibility_weight
    assert math.isclose(total_weights, 1.0, abs_tol=1e-4)


# =====================================================================
# 4. All Factors at 100.0
# =====================================================================


def test_all_factors_max(default_engine: RelocationPriorityEngine) -> None:
    """All 5 factors at 100.0 must yield priority score 100.0 and IMMEDIATE band."""
    result = default_engine.evaluate(
        village_id="VIL-MAX",
        risk=100.0,
        exposure=100.0,
        vulnerability=100.0,
        historical_impact=100.0,
        accessibility=100.0,
    )
    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score == 100.0
    assert result.priority_band == RelocationPriorityBand.IMMEDIATE
    assert result.explainability.was_clamped is False


# =====================================================================
# 5. Score Clamping Behavior
# =====================================================================


def test_score_clamping_behavior(default_engine: RelocationPriorityEngine) -> None:
    """Confirm mathematical score is strictly clamped to [0.0, 100.0]."""
    # A standard evaluation within range is not clamped
    result = default_engine.evaluate(
        village_id="VIL-NORMAL",
        risk=50.0,
        exposure=50.0,
        vulnerability=50.0,
        historical_impact=50.0,
        accessibility=50.0,
    )
    assert result.priority_score == 50.0
    assert result.explainability.was_clamped is False


# =====================================================================
# 6 & 7. Exact Threshold Boundaries and Adjacent Values
# =====================================================================


@pytest.mark.parametrize(
    ("target_score", "expected_band"),
    [
        (100.0, RelocationPriorityBand.IMMEDIATE),
        (80.01, RelocationPriorityBand.IMMEDIATE),
        (80.00, RelocationPriorityBand.IMMEDIATE),
        (79.99, RelocationPriorityBand.SHORT_TERM),
        (60.01, RelocationPriorityBand.SHORT_TERM),
        (60.00, RelocationPriorityBand.SHORT_TERM),
        (59.99, RelocationPriorityBand.MEDIUM_TERM),
        (40.01, RelocationPriorityBand.MEDIUM_TERM),
        (40.00, RelocationPriorityBand.MEDIUM_TERM),
        (39.99, RelocationPriorityBand.MONITOR),
        (1.00, RelocationPriorityBand.MONITOR),
        (0.00, RelocationPriorityBand.MONITOR),
    ],
)
def test_exact_and_adjacent_boundary_classifications(
    default_engine: RelocationPriorityEngine,
    target_score: float,
    expected_band: RelocationPriorityBand,
) -> None:
    """Verify exact boundary classifications:
    - [80.0, 100.0] -> IMMEDIATE
    - [60.0, 80.0)  -> SHORT_TERM
    - [40.0, 60.0)  -> MEDIUM_TERM
    - [0.0, 40.0)   -> MONITOR
    """
    # By setting all factors to target_score, since weights sum to 1.0, score = target_score
    result = default_engine.evaluate(
        village_id="VIL-BOUNDARY",
        risk=target_score,
        exposure=target_score,
        vulnerability=target_score,
        historical_impact=target_score,
        accessibility=target_score,
    )
    assert result.status == RelocationPriorityStatus.SCORED
    assert result.priority_score is not None
    assert math.isclose(result.priority_score, target_score, abs_tol=1e-4)
    assert result.priority_band == expected_band


# =====================================================================
# 8 - 12. Missing Factor Handling (Safety: Never default to 0)
# =====================================================================


def test_missing_risk_factor(default_engine: RelocationPriorityEngine) -> None:
    """Missing risk factor must yield INSUFFICIENT_DATA with priority_score=None."""
    result = default_engine.evaluate(
        village_id="VIL-MISSING-R",
        risk=None,
        exposure=50.0,
        vulnerability=50.0,
        historical_impact=50.0,
        accessibility=50.0,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert result.priority_band is None
    assert result.missing_factors == ["risk"]
    assert result.is_actionable_proposal is False
    assert "risk" in result.explainability.summary_narrative


def test_missing_exposure_factor(default_engine: RelocationPriorityEngine) -> None:
    """Missing exposure factor must yield INSUFFICIENT_DATA with priority_score=None."""
    result = default_engine.evaluate(
        village_id="VIL-MISSING-E",
        risk=50.0,
        exposure=None,
        vulnerability=50.0,
        historical_impact=50.0,
        accessibility=50.0,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert result.priority_band is None
    assert result.missing_factors == ["exposure"]


def test_missing_vulnerability_factor(default_engine: RelocationPriorityEngine) -> None:
    """Missing vulnerability factor must yield INSUFFICIENT_DATA with priority_score=None."""
    result = default_engine.evaluate(
        village_id="VIL-MISSING-V",
        risk=50.0,
        exposure=50.0,
        vulnerability=None,
        historical_impact=50.0,
        accessibility=50.0,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert result.priority_band is None
    assert result.missing_factors == ["vulnerability"]


def test_missing_historical_impact_factor(default_engine: RelocationPriorityEngine) -> None:
    """Missing historical impact factor must yield INSUFFICIENT_DATA with priority_score=None."""
    result = default_engine.evaluate(
        village_id="VIL-MISSING-H",
        risk=50.0,
        exposure=50.0,
        vulnerability=50.0,
        historical_impact=None,
        accessibility=50.0,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert result.priority_band is None
    assert result.missing_factors == ["historical_impact"]


def test_missing_accessibility_factor(default_engine: RelocationPriorityEngine) -> None:
    """Missing accessibility factor must yield INSUFFICIENT_DATA with priority_score=None."""
    result = default_engine.evaluate(
        village_id="VIL-MISSING-A",
        risk=50.0,
        exposure=50.0,
        vulnerability=50.0,
        historical_impact=50.0,
        accessibility=None,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert result.priority_band is None
    assert result.missing_factors == ["accessibility"]


def test_multiple_missing_factors(default_engine: RelocationPriorityEngine) -> None:
    """Multiple missing factors must all be audited in missing_factors."""
    result = default_engine.evaluate(
        village_id="VIL-MULTI-MISSING",
        risk=50.0,
        exposure=None,
        vulnerability=None,
        historical_impact=50.0,
        accessibility=None,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert set(result.missing_factors) == {"exposure", "vulnerability", "accessibility"}


# =====================================================================
# 13. Strict Mode Error Handling
# =====================================================================


def test_strict_mode_error_handling(default_engine: RelocationPriorityEngine) -> None:
    """Under strict=True, missing factor(s) must raise InsufficientPriorityDataError."""
    with pytest.raises(InsufficientPriorityDataError) as exc_info:
        default_engine.evaluate(
            village_id="VIL-STRICT",
            risk=80.0,
            exposure=None,
            vulnerability=50.0,
            historical_impact=40.0,
            accessibility=20.0,
            strict=True,
        )
    assert "exposure" in exc_info.value.missing_fields
    assert "Missing required relocation priority factor" in str(exc_info.value)


# =====================================================================
# 14. Rejection of Negative Factor Values
# =====================================================================


@pytest.mark.parametrize("bad_val", [-0.01, -1.0, -50.0])
def test_rejection_negative_factor_values(default_engine: RelocationPriorityEngine, bad_val: float) -> None:
    """Negative factor values must raise InvalidPriorityDataError."""
    with pytest.raises(InvalidPriorityDataError) as exc_info:
        default_engine.evaluate(
            village_id="VIL-NEG",
            risk=bad_val,
            exposure=50.0,
            vulnerability=50.0,
            historical_impact=50.0,
            accessibility=50.0,
        )
    assert "outside valid range [0.0, 100.0]" in str(exc_info.value)


# =====================================================================
# 15. Rejection of Factor Values Exceeding 100.0
# =====================================================================


@pytest.mark.parametrize("bad_val", [100.01, 105.0, 500.0])
def test_rejection_factor_values_exceeding_max(default_engine: RelocationPriorityEngine, bad_val: float) -> None:
    """Factor values > 100.0 must raise InvalidPriorityDataError."""
    with pytest.raises(InvalidPriorityDataError) as exc_info:
        default_engine.evaluate(
            village_id="VIL-OVER",
            risk=50.0,
            exposure=bad_val,
            vulnerability=50.0,
            historical_impact=50.0,
            accessibility=50.0,
        )
    assert "outside valid range [0.0, 100.0]" in str(exc_info.value)


# =====================================================================
# 16. Rejection of NaN, Infinity, and Boolean Values
# =====================================================================


@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
def test_rejection_nan_and_inf_values(default_engine: RelocationPriorityEngine, bad_val: float) -> None:
    """NaN or infinite factor values must raise InvalidPriorityDataError."""
    with pytest.raises(InvalidPriorityDataError) as exc_info:
        default_engine.evaluate(
            village_id="VIL-NAN",
            risk=bad_val,
            exposure=50.0,
            vulnerability=50.0,
            historical_impact=50.0,
            accessibility=50.0,
        )
    assert "cannot be NaN or infinite" in str(exc_info.value)


@pytest.mark.parametrize("bool_val", [True, False])
def test_rejection_boolean_inputs(default_engine: RelocationPriorityEngine, bool_val: bool) -> None:
    """Boolean inputs must be explicitly rejected with InvalidPriorityDataError."""
    with pytest.raises(InvalidPriorityDataError) as exc_info:
        default_engine.evaluate(
            village_id="VIL-BOOL",
            risk=bool_val,
            exposure=50.0,
            vulnerability=50.0,
            historical_impact=50.0,
            accessibility=50.0,
        )
    assert "boolean cannot be used as a numerical score" in str(exc_info.value)


# =====================================================================
# 17. Deterministic Repeated Calculation
# =====================================================================


def test_deterministic_repeated_calculation(default_engine: RelocationPriorityEngine) -> None:
    """Repeated execution with identical inputs must yield identical numerical results."""
    kwargs = {
        "village_id": "VIL-DETERMINISTIC",
        "risk": 75.25,
        "exposure": 63.80,
        "vulnerability": 42.10,
        "historical_impact": 88.00,
        "accessibility": 15.50,
    }
    baseline = default_engine.evaluate(**kwargs)
    for _ in range(50):
        run_res = default_engine.evaluate(**kwargs)
        assert run_res.priority_score == baseline.priority_score
        assert run_res.priority_band == baseline.priority_band
        assert run_res.factor_contributions == baseline.factor_contributions
        assert run_res.explainability.summary_narrative == baseline.explainability.summary_narrative


# =====================================================================
# 18. Explainability Factor Breakdown & Auditability
# =====================================================================


def test_explainability_factor_breakdown(default_engine: RelocationPriorityEngine) -> None:
    """Verify factor breakdown detail, contributions, percentages, and narrative."""
    result = default_engine.evaluate(
        village_id="VIL-EXPLAIN",
        village_name="Mana Settlement",
        risk=90.0,
        exposure=70.0,
        vulnerability=40.0,
        historical_impact=30.0,
        accessibility=10.0,
    )
    # 0.40*90 + 0.25*70 + 0.20*40 + 0.10*30 + 0.05*10 = 36 + 17.5 + 8 + 3 + 0.5 = 65.0
    assert result.priority_score == 65.0
    assert result.priority_band == RelocationPriorityBand.SHORT_TERM

    expl = result.explainability
    assert len(expl.factor_breakdown) == 5
    assert expl.primary_driver == PriorityFactorType.RISK.display_name
    assert math.isclose(expl.primary_driver_contribution, 36.0, abs_tol=1e-4)

    # Check symbols and display names
    symbols = [f.symbol for f in expl.factor_breakdown]
    assert symbols == ["R", "E", "V", "H", "A"]

    # Check contribution percentages sum to ~100%
    total_pct = sum(f.contribution_percentage for f in expl.factor_breakdown if f.contribution_percentage)
    assert math.isclose(total_pct, 100.0, abs_tol=0.1)

    # Check descriptions
    for detail in expl.factor_breakdown:
        assert detail.description != ""
        assert detail.is_available is True
        assert detail.normalized_value is not None


# =====================================================================
# 19. Upstream Contract Consumption & Provenance
# =====================================================================


def test_upstream_contract_consumption_and_provenance(
    default_engine: RelocationPriorityEngine,
    sample_provenance: ProviderProvenance,
) -> None:
    """Upstream result envelopes must be consumed directly and their provenance aggregated."""
    # 1. CompositeRiskResult via MultiHazardRiskEngine with sample_provenance
    risk_engine = MultiHazardRiskEngine()
    risk_res = risk_engine.compute_from_values(
        hazard_severity=85.0,
        flood_exposure=85.0,
        rainfall_intensity=85.0,
        slope_landslide_susceptibility=85.0,
        infrastructure_vulnerability=85.0,
        social_vulnerability=85.0,
        provenance=sample_provenance,
    )
    assert risk_res.score == 85.0

    # 2. DemographicExposureResult via VulnerabilityExposureEngine
    vuln_engine = VulnerabilityExposureEngine()
    demo_inp = DemographicInput(
        village_id="HIM-VILL-001",
        total_population=500,
        households=110,
        elderly_count=50,
        children_count=100,
        disabled_count=10,
        livestock_count=150,
        provenance=sample_provenance,
    )
    exposure_res = vuln_engine.score_demographic_exposure(demo_inp)
    assert exposure_res.normalized_value == 53.75

    # 3. SocialVulnerabilityResult via VulnerabilityExposureEngine
    vuln_inp = VulnerabilityInput(
        village_id="HIM-VILL-001",
        social_vulnerability_index=0.40,
        economic_vulnerability_index=0.60,
        structural_vulnerability_index=0.50,
        road_connectivity_index=0.80,
        provenance=sample_provenance,
    )
    vuln_res = vuln_engine.score_social_vulnerability(vuln_inp)
    assert vuln_res.normalized_value == 42.5

    result = default_engine.evaluate(
        village_id="VIL-UPSTREAM",
        village_name="Joshimath Center",
        risk=risk_res,
        exposure=exposure_res,
        vulnerability=vuln_res,
        historical_impact=30.0,
        accessibility=15.0,
    )

    # 0.40*85 + 0.25*53.75 + 0.20*42.5 + 0.10*30 + 0.05*15 = 34.0 + 13.4375 + 8.5 + 3.0 + 0.75 = 59.6875
    assert result.status == RelocationPriorityStatus.SCORED
    assert math.isclose(result.priority_score, 59.6875, abs_tol=1e-4)
    assert result.priority_band == RelocationPriorityBand.MEDIUM_TERM

    # Provenance aggregated
    assert len(result.provenance) >= 3
    assert result.provenance[0]["provider_id"] == "mock_relocation_provider"


def test_upstream_contract_incomplete_handling(default_engine: RelocationPriorityEngine) -> None:
    """Uncomputed/failed upstream results must be treated as missing data."""
    risk_engine = MultiHazardRiskEngine()
    incomplete_risk_res = risk_engine.compute_from_values(
        hazard_severity=80.0,
        flood_exposure=50.0,
        rainfall_intensity=60.0,
        slope_landslide_susceptibility=40.0,
        infrastructure_vulnerability=30.0,
        social_vulnerability=None,  # missing -> INSUFFICIENT_FACTORS
    )
    assert incomplete_risk_res.status == RiskComputationStatus.INSUFFICIENT_FACTORS
    assert incomplete_risk_res.score is None

    result = default_engine.evaluate(
        village_id="VIL-FAIL-UPSTREAM",
        risk=incomplete_risk_res,
        exposure=50.0,
        vulnerability=50.0,
        historical_impact=50.0,
        accessibility=50.0,
    )
    assert result.status == RelocationPriorityStatus.INSUFFICIENT_DATA
    assert result.priority_score is None
    assert "risk" in result.missing_factors


# =====================================================================
# 20. Governance Invariants
# =====================================================================


def test_governance_invariants(default_engine: RelocationPriorityEngine) -> None:
    """Governance invariants:
    - is_automatic_evacuation is strictly False.
    - is_actionable_proposal is True when SCORED, False when INSUFFICIENT_DATA.
    - Governance notice is present.
    - Setting is_automatic_evacuation=True raises ValueError.
    """
    scored_res = default_engine.evaluate(
        village_id="VIL-GOV",
        risk=90.0,
        exposure=90.0,
        vulnerability=90.0,
        historical_impact=90.0,
        accessibility=90.0,
    )
    assert scored_res.is_automatic_evacuation is False
    assert scored_res.is_actionable_proposal is True
    assert "DECISION SUPPORT ONLY" in scored_res.governance_notice
    assert "DECISION SUPPORT ONLY" in scored_res.explainability.governance_notice

    # Test validator blocks automatic evacuation
    with pytest.raises(ValueError) as exc_info:
        RelocationPriorityResult(
            village_id="VIL-EVAC",
            status=RelocationPriorityStatus.SCORED,
            priority_score=90.0,
            priority_band=RelocationPriorityBand.IMMEDIATE,
            is_automatic_evacuation=True,
            explainability=scored_res.explainability,
        )
    assert "is_automatic_evacuation=True" in str(exc_info.value)


# =====================================================================
# 21. Batch Evaluation & Typed Inputs
# =====================================================================


def test_batch_evaluation_and_typed_inputs(default_engine: RelocationPriorityEngine) -> None:
    """Test evaluate_factors and evaluate_batch across mixed inputs."""
    inp1 = RelocationPriorityInput(
        village_id="VIL-B1",
        village_name="Village 1",
        risk=85.0,
        exposure=80.0,
        vulnerability=75.0,
        historical_impact=60.0,
        accessibility=40.0,
    )
    inp2 = RelocationPriorityInput(
        village_id="VIL-B2",
        village_name="Village 2",
        risk=20.0,
        exposure=20.0,
        vulnerability=20.0,
        historical_impact=20.0,
        accessibility=20.0,
    )
    dict_item = {
        "village_id": "VIL-B3",
        "risk": 95.0,
        "exposure": None,  # Missing
        "vulnerability": 50.0,
        "historical_impact": 50.0,
        "accessibility": 50.0,
    }

    # Evaluate single typed input
    single_res = default_engine.evaluate_factors(inp1)
    assert single_res.status == RelocationPriorityStatus.SCORED
    assert single_res.priority_band == RelocationPriorityBand.SHORT_TERM

    # Evaluate batch
    batch_results = default_engine.evaluate_batch([inp1, inp2, dict_item])
    assert len(batch_results) == 3
    assert batch_results[0].village_id == "VIL-B1"
    assert batch_results[0].status == RelocationPriorityStatus.SCORED
    assert batch_results[1].village_id == "VIL-B2"
    assert batch_results[1].status == RelocationPriorityStatus.SCORED
    assert batch_results[1].priority_band == RelocationPriorityBand.MONITOR
    assert batch_results[2].village_id == "VIL-B3"
    assert batch_results[2].status == RelocationPriorityStatus.INSUFFICIENT_DATA


# =====================================================================
# 22. Profile Factory & Configuration Validation
# =====================================================================


def test_profile_factory_and_config_validation(himalayan_profile: RegionProfile) -> None:
    """Verify initialization from profile string, RegionProfileId, and configuration validation."""
    eng1 = RelocationPriorityEngine.from_profile("himalayan_pilot")
    eng2 = RelocationPriorityEngine.from_profile(RegionProfileId.HIMALAYAN_PILOT)
    eng3 = RelocationPriorityEngine.from_profile(himalayan_profile)

    assert eng1.weights_config.risk_weight == 0.40
    assert eng2.weights_config.exposure_weight == 0.25
    assert eng3.bands_config.immediate_min == 80.0

    # Invalid weights sum
    with pytest.raises(PriorityConfigError) as exc_info:
        RelocationPriorityWeightsConfig(
            risk_weight=0.50,
            exposure_weight=0.50,
            vulnerability_weight=0.20,
            historical_impact_weight=0.10,
            accessibility_weight=0.05,
        )
    assert "weights must sum to 1.0" in str(exc_info.value)

    # Invalid band ordering
    with pytest.raises(PriorityConfigError) as exc_info:
        PriorityScoreBandsConfig(
            monitor_max=40.0,
            medium_term_min=70.0,
            short_term_min=60.0,  # Invalid: short < medium
            immediate_min=80.0,
        )
    assert "cutoffs must be strictly ascending" in str(exc_info.value)
