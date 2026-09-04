"""Unit tests for the M3-05 Risk Normalization Engine.

Verifies:
1. Linear minimum maps to 0.0
2. Linear maximum maps to 100.0
3. Linear midpoint maps deterministically
4. Below-range input clamps correctly
5. Above-range input clamps correctly
6. Invalid range configuration is rejected
7. NaN rejected
8. Infinity rejected
9. Rainfall heavy threshold behavior
10. Rainfall very-heavy threshold behavior
11. Rainfall thresholds sourced from M3-01 configuration
12. Cumulative rainfall flags are not treated as mutually exclusive
13. Categorical severity mapping is deterministic
14. Unsupported category is explicitly rejected/reported
15. Missing/unknown input does NOT become zero
16. Normalized values always remain within [0, 100]
17. Identical input/configuration produces identical output
18. Provenance/source record identity is preserved
19. Explainability metadata is populated
20. No composite risk aggregation is performed
"""

import math
import pytest

from app.core.profiles import get_profile, list_profiles
from app.core.profiles.models import RegionProfile
from app.core.risk.normalization.contracts import (
    CategoricalSeverityPolicy,
    FactorCategory,
    LinearRangeConfig,
    NormalizationMethod,
    NormalizationResult,
    NormalizationStatus,
    PiecewiseThresholdConfig,
)
from app.core.risk.normalization.engine import RiskNormalizationEngine
from app.core.risk.normalization.errors import (
    InvalidInputError,
    NormalizationConfigError,
    UnsupportedFactorError,
)
from app.core.risk.normalization.methods import (
    categorical_severity_normalize,
    linear_normalize,
    piecewise_threshold_normalize,
)
from app.data.ingestion.schemas import (
    CanonicalFloodRecord,
    CanonicalHazardObservationRecord,
    CanonicalLandslideRecord,
    CanonicalPopulationRecord,
    CanonicalRainfallRecord,
)
from app.data.providers.contracts import ProviderMode, ProviderProvenance


@pytest.fixture
def default_engine() -> RiskNormalizationEngine:
    return RiskNormalizationEngine()


@pytest.fixture
def sample_provenance() -> ProviderProvenance:
    return ProviderProvenance(
        provider_id="mock_rainfall",
        provider_name="Mock IMD Rainfall Adapter",
        mode=ProviderMode.MOCK,
        is_synthetic=True,
        region_id="himalayan_pilot",
    )


# =====================================================================
# 1-3. Linear Normalization Tests
# =====================================================================


def test_linear_minimum_maps_to_zero():
    """1. Linear minimum maps to 0.0."""
    config = LinearRangeConfig(min_value=10.0, max_value=50.0)
    score, was_clamped, reason = linear_normalize(10.0, config)
    assert score == 0.0
    assert was_clamped is False
    assert reason is None


def test_linear_maximum_maps_to_hundred():
    """2. Linear maximum maps to 100.0."""
    config = LinearRangeConfig(min_value=10.0, max_value=50.0)
    score, was_clamped, reason = linear_normalize(50.0, config)
    assert score == 100.0
    assert was_clamped is False
    assert reason is None


def test_linear_midpoint_maps_deterministically():
    """3. Linear midpoint maps deterministically to 50.0."""
    config = LinearRangeConfig(min_value=0.0, max_value=200.0)
    score, was_clamped, reason = linear_normalize(100.0, config)
    assert score == 50.0
    assert was_clamped is False


# =====================================================================
# 4-6. Clamping & Invalid Range Configuration
# =====================================================================


def test_below_range_input_clamps_correctly():
    """4. Below-range input clamps correctly to 0.0 with was_clamped=True."""
    config = LinearRangeConfig(min_value=0.0, max_value=100.0)
    score, was_clamped, reason = linear_normalize(-25.0, config)
    assert score == 0.0
    assert was_clamped is True
    assert reason is not None
    assert "below minimum bound" in reason


def test_above_range_input_clamps_correctly():
    """5. Above-range input clamps correctly to 100.0 with was_clamped=True."""
    config = LinearRangeConfig(min_value=0.0, max_value=100.0)
    score, was_clamped, reason = linear_normalize(175.5, config)
    assert score == 100.0
    assert was_clamped is True
    assert reason is not None
    assert "exceeds maximum bound" in reason


def test_invalid_range_configuration_rejected():
    """6. Invalid range configuration (max <= min) is rejected with NormalizationConfigError."""
    # max == min
    with pytest.raises(NormalizationConfigError, match="strictly greater than min_value"):
        LinearRangeConfig(min_value=50.0, max_value=50.0)

    # max < min
    with pytest.raises(NormalizationConfigError, match="strictly greater than min_value"):
        LinearRangeConfig(min_value=100.0, max_value=20.0)


# =====================================================================
# 7-8. NaN and Infinity Rejection
# =====================================================================


def test_nan_input_rejected():
    """7. NaN input is rejected with InvalidInputError."""
    config = LinearRangeConfig(min_value=0.0, max_value=100.0)
    with pytest.raises(InvalidInputError, match="cannot be NaN or infinite"):
        linear_normalize(float("nan"), config)

    piecewise_cfg = PiecewiseThresholdConfig(benchmarks=[(0.0, 0.0), (100.0, 100.0)])
    with pytest.raises(InvalidInputError, match="cannot be NaN or infinite"):
        piecewise_threshold_normalize(float("nan"), piecewise_cfg)


def test_infinity_input_rejected():
    """8. Infinity input is rejected with InvalidInputError."""
    config = LinearRangeConfig(min_value=0.0, max_value=100.0)
    with pytest.raises(InvalidInputError, match="cannot be NaN or infinite"):
        linear_normalize(float("inf"), config)

    with pytest.raises(InvalidInputError, match="cannot be NaN or infinite"):
        linear_normalize(float("-inf"), config)


# =====================================================================
# 9-12. Rainfall Thresholds & Profile Sourcing
# =====================================================================


def test_rainfall_heavy_threshold_behavior(default_engine):
    """9. Rainfall at exactly the heavy threshold maps to the designated benchmark (50.0)."""
    # IMD heavy rainfall threshold in Himalayan profile is 64.5 mm
    res = default_engine.normalize_rainfall(64.5, record_id="rain_001")
    assert res.status == NormalizationStatus.NORMALIZED
    assert res.normalized_value == 50.0
    assert res.was_clamped is False
    assert res.explainability.thresholds_applied["rainfall_heavy_24h_mm"] == 64.5


def test_rainfall_very_heavy_threshold_behavior(default_engine):
    """10. Rainfall at very-heavy threshold maps to 80.0."""
    # IMD very heavy rainfall threshold in Himalayan profile is 115.5 mm
    res = default_engine.normalize_rainfall(115.5, record_id="rain_002")
    assert res.status == NormalizationStatus.NORMALIZED
    assert res.normalized_value == 80.0
    assert res.was_clamped is False
    assert res.explainability.thresholds_applied["rainfall_very_heavy_24h_mm"] == 115.5


def test_rainfall_thresholds_sourced_from_m3_01_configuration(default_engine):
    """11. Engine dynamically retrieves thresholds from the active RegionProfile."""
    profile = get_profile("himalayan_pilot")
    expected_heavy = profile.hazard_parameters.thresholds.rainfall_heavy_24h_mm
    expected_very_heavy = profile.hazard_parameters.thresholds.rainfall_very_heavy_24h_mm

    assert expected_heavy == 64.5
    assert expected_very_heavy == 115.5

    benchmarks = default_engine.rainfall_piecewise_config.benchmarks
    assert benchmarks[1] == (expected_heavy, 50.0)
    assert benchmarks[2] == (expected_very_heavy, 80.0)


def test_cumulative_rainfall_flags_not_mutually_exclusive(default_engine):
    """12. Cumulative exceedance flags (>=115.5mm sets both True) are preserved and not binned."""
    # When rain is 130.0 mm, both is_heavy_rain and is_very_heavy_rain can be True
    res = default_engine.normalize_rainfall(
        130.0,
        record_id="rain_cumul_01",
        is_heavy_rain=True,
        is_very_heavy_rain=True,
    )
    assert res.status == NormalizationStatus.NORMALIZED
    assert res.normalized_value > 80.0
    assert res.explainability.parameters_used["cumulative_flags"]["is_heavy_rain"] is True
    assert res.explainability.parameters_used["cumulative_flags"]["is_very_heavy_rain"] is True


# =====================================================================
# 13-14. Categorical Severity Normalization
# =====================================================================


def test_categorical_severity_mapping_is_deterministic():
    """13. Categorical severity mapping produces deterministic 0-100 scores."""
    policy = CategoricalSeverityPolicy()
    assert categorical_severity_normalize("low", policy)[0] == 20.0
    assert categorical_severity_normalize("moderate", policy)[0] == 40.0
    assert categorical_severity_normalize("high", policy)[0] == 65.0
    assert categorical_severity_normalize("very_high", policy)[0] == 85.0
    assert categorical_severity_normalize("critical", policy)[0] == 100.0

    # Case insensitivity
    assert categorical_severity_normalize("HIGH", policy)[0] == 65.0
    assert categorical_severity_normalize(" Critical ", policy)[0] == 100.0


def test_unsupported_category_rejected_or_reported(default_engine):
    """14. Unsupported severity category is rejected or reported with diagnostic issue."""
    policy = CategoricalSeverityPolicy()
    with pytest.raises(InvalidInputError, match="Unsupported severity category 'catastrophic'"):
        categorical_severity_normalize("catastrophic", policy)

    res = default_engine.normalize_categorical("unknown_danger", factor_category=FactorCategory.HAZARD_OBSERVATION)
    assert res.status == NormalizationStatus.INVALID
    assert res.normalized_value is None
    assert "Unsupported severity category" in res.diagnostic_message


# =====================================================================
# 15. Safety-Critical Missing / Unknown Handling
# =====================================================================


def test_missing_unknown_input_does_not_become_zero(default_engine):
    """15. Safety-critical: Missing or null input NEVER evaluates to 0.0 factor."""
    res_none_val = default_engine.normalize_rainfall(None, record_id="missing_rain")
    assert res_none_val.status == NormalizationStatus.UNAVAILABLE
    assert res_none_val.normalized_value is None
    assert res_none_val.is_unknown_or_unavailable is True
    assert res_none_val.normalized_value != 0.0

    res_none_rec = default_engine.normalize_record(None)
    assert res_none_rec.status == NormalizationStatus.UNAVAILABLE
    assert res_none_rec.normalized_value is None
    assert res_none_rec.is_unknown_or_unavailable is True


# =====================================================================
# 16-17. Invariants: Bounds & Determinism
# =====================================================================


def test_normalized_values_always_bounded_zero_to_hundred(default_engine):
    """16. All valid normalized values strictly satisfy 0.0 <= factor <= 100.0."""
    test_values = [-100.0, 0.0, 10.0, 64.5, 90.0, 115.5, 204.4, 500.0]
    for v in test_values:
        res = default_engine.normalize_rainfall(v)
        assert res.normalized_value is not None
        assert 0.0 <= res.normalized_value <= 100.0
        assert not math.isnan(res.normalized_value)
        assert not math.isinf(res.normalized_value)


def test_identical_input_configuration_produces_identical_output(default_engine):
    """17. Identical input and configuration produces identical output (idempotency/determinism)."""
    res1 = default_engine.normalize_rainfall(82.4, record_id="rec_same")
    res2 = default_engine.normalize_rainfall(82.4, record_id="rec_same")
    assert res1.model_dump() == res2.model_dump()


# =====================================================================
# 18-19. Provenance & Explainability
# =====================================================================


def test_provenance_and_record_identity_preserved(default_engine, sample_provenance):
    """18. Provenance and source record identity are preserved in the result."""
    res = default_engine.normalize_rainfall(
        75.0,
        record_id="rec_prov_01",
        provenance=sample_provenance,
    )
    assert res.record_id == "rec_prov_01"
    assert res.provenance is not None
    assert res.provenance.provider_id == "mock_rainfall"
    assert res.provenance.is_synthetic is True


def test_explainability_metadata_populated(default_engine):
    """19. Structured explainability metadata is completely populated for auditability."""
    res = default_engine.normalize_flood(2.5, record_id="flood_exp_01")
    assert res.explainability.method == NormalizationMethod.LINEAR
    assert "min_value" in res.explainability.parameters_used
    assert "max_value" in res.explainability.parameters_used
    assert res.explainability.input_domain_range == (0.0, 5.0)
    assert "Linear range normalization" in res.explainability.formula_description


# =====================================================================
# 20. Scope Boundary Verification (No Composite Risk Calculation)
# =====================================================================


def test_no_composite_risk_aggregation_performed(default_engine):
    """20. Explicit scope verification: engine only calculates individual factors, NOT composite risk."""
    # Ensure there is NO calculate_composite_risk or similar method on RiskNormalizationEngine
    assert not hasattr(default_engine, "calculate_composite_risk")
    assert not hasattr(default_engine, "calculate_risk_score")
    assert not hasattr(default_engine, "classify_risk_band")
    assert not hasattr(default_engine, "demarcate_red_zone")


# =====================================================================
# Canonical Record Ingestion Pipeline Integration Tests
# =====================================================================


def test_canonical_records_normalization(default_engine, sample_provenance):
    """Verify normalize_record correctly handles canonical records from M3-04."""
    # Canonical Rainfall
    rain = CanonicalRainfallRecord(
        record_id="can_rain_01",
        observed_at="2026-09-04T12:00:00Z",
        location_coordinates=(78.5, 30.5),
        provenance=sample_provenance,
        rainfall_24h_mm=64.5,
        severity="moderate",
        is_heavy_rain=True,
        is_very_heavy_rain=False,
        ingested_at="2026-09-04T12:05:00Z",
        batch_id="batch_01",
        canonical_hash="hash_01",
    )
    res_rain = default_engine.normalize_record(rain)
    assert res_rain.factor_category == FactorCategory.RAINFALL
    assert res_rain.normalized_value == 50.0

    # Canonical Flood
    flood = CanonicalFloodRecord(
        record_id="can_flood_01",
        observed_at="2026-09-04T12:00:00Z",
        location_coordinates=(78.5, 30.5),
        provenance=sample_provenance,
        water_level_m_above_danger=2.5,
        severity="high",
        ingested_at="2026-09-04T12:05:00Z",
        batch_id="batch_01",
        canonical_hash="hash_02",
    )
    res_flood = default_engine.normalize_record(flood)
    assert res_flood.factor_category == FactorCategory.FLOOD
    assert res_flood.normalized_value == 50.0  # 2.5m out of 5.0m max

    # Canonical Landslide
    landslide = CanonicalLandslideRecord(
        record_id="can_ls_01",
        observed_at="2026-09-04T12:00:00Z",
        location_coordinates=(78.5, 30.5),
        provenance=sample_provenance,
        debris_volume_cu_m=5000.0,
        severity="high",
        road_blocked=True,
        ingested_at="2026-09-04T12:05:00Z",
        batch_id="batch_01",
        canonical_hash="hash_03",
    )
    res_ls = default_engine.normalize_record(landslide)
    assert res_ls.factor_category == FactorCategory.LANDSLIDE
    assert res_ls.normalized_value == 50.0  # 5000 m³ out of 10000 m³ max

    # Canonical Hazard Observation (Seismic)
    seismic = CanonicalHazardObservationRecord(
        record_id="can_seismic_01",
        observed_at="2026-09-04T12:00:00Z",
        location_coordinates=(78.5, 30.5),
        provenance=sample_provenance,
        hazard_type="seismic",
        severity="very_high",
        intensity_value=7.0,  # critical threshold
        intensity_unit="MMI",
        ingested_at="2026-09-04T12:05:00Z",
        batch_id="batch_01",
        canonical_hash="hash_04",
    )
    res_seismic = default_engine.normalize_record(seismic)
    assert res_seismic.factor_category == FactorCategory.SEISMIC
    assert res_seismic.normalized_value == 75.0


def test_population_record_deferred_to_m3_09(default_engine, sample_provenance):
    """Verify CanonicalPopulationRecord returns DEFERRED status and None score."""
    pop = CanonicalPopulationRecord(
        village_id="VIL-HIM-001",
        village_name="Demo Village",
        region_code="HIM",
        district_code="DIST-01",
        block_code="BLK-01",
        location_coordinates=(78.5, 30.5),
        total_population=450,
        households=90,
        elderly_count=50,
        children_count=80,
        disabled_count=10,
        livestock_count=120,
        provenance=sample_provenance,
        ingested_at="2026-09-04T12:05:00Z",
        batch_id="batch_01",
        canonical_hash="hash_pop",
    )
    res_pop = default_engine.normalize_record(pop)
    assert res_pop.factor_category == FactorCategory.POPULATION_EXPOSURE
    assert res_pop.status == NormalizationStatus.DEFERRED
    assert res_pop.normalized_value is None
    assert res_pop.is_unknown_or_unavailable is True
    assert "deferred to chunk M3-09" in res_pop.diagnostic_message
