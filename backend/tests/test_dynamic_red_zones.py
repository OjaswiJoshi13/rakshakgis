"""Tests for Dynamic Red Zones & Threshold Triggers (Chunk M3-11)."""

import math
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box

from app.core.profiles import get_profile
from app.core.profiles.models import DangerLevel, RegionProfileId
from app.core.risk.red_zone import (
    ComparisonOperator,
    DynamicHazardIndicator,
    DynamicHazardObservation,
    DynamicRedZoneCandidate,
    DynamicRedZoneEngine,
    DynamicThresholdConfig,
    DynamicTriggerStatus,
    InvalidGeophysicalDataError,
    PermanentRedZoneCandidate,
    PermanentRedZoneEngine,
    RedZoneConfigError,
    RedZoneStatus,
    RedZoneType,
)
from app.core.risk.red_zone.errors import InsufficientGeophysicalDataError
from app.data.providers.contracts import (
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedRainfallRecord,
    ProviderMode,
    ProviderProvenance,
)


@pytest.fixture
def himalayan_profile():
    return get_profile(RegionProfileId.HIMALAYAN_PILOT)


@pytest.fixture
def coastal_profile():
    return get_profile(RegionProfileId.COASTAL_TEMPLATE)


@pytest.fixture
def riverine_profile():
    return get_profile(RegionProfileId.RIVERINE_TEMPLATE)


@pytest.fixture
def default_engine():
    return DynamicRedZoneEngine.from_profile(RegionProfileId.HIMALAYAN_PILOT)


# =========================================================================
# 1. Boundary & Exceedance Trigger Tests
# =========================================================================


def test_rainfall_above_threshold_triggers_candidate(default_engine):
    """Rule 1: Observed rainfall strictly above configured threshold triggers dynamic candidate."""
    # Himalayan pilot rainfall trigger is 64.5 mm
    obs = DynamicHazardObservation(
        observation_id="OBS-RAIN-001",
        village_id="VIL-CHAMOLI-001",
        rainfall_24h_mm=75.0,  # > 64.5
        location=(79.5, 30.5),
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.is_candidate is True
    assert result.is_temporary is True
    assert result.zone_type == RedZoneType.FLOOD_INUNDATION
    assert result.danger_level == DangerLevel.VERY_HIGH
    assert result.geometry is not None
    assert "rainfall_24h" in result.explainability.triggered_indicators
    assert result.explainability.trigger_evaluations[0].triggered is True
    assert result.explainability.trigger_evaluations[0].observed_value == 75.0
    assert result.explainability.trigger_evaluations[0].configured_threshold == 64.5


def test_rainfall_strictly_below_threshold_does_not_trigger(default_engine):
    """Rule 2: Observed rainfall strictly below configured threshold yields NO_TRIGGER."""
    obs = DynamicHazardObservation(
        observation_id="OBS-RAIN-002",
        village_id="VIL-CHAMOLI-001",
        rainfall_24h_mm=50.0,  # < 64.5
        location=(79.5, 30.5),
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.NO_TRIGGER
    assert result.is_candidate is False
    assert result.danger_level is None
    assert result.geometry is None
    assert len(result.explainability.triggered_indicators) == 0
    assert result.explainability.trigger_evaluations[0].triggered is False


def test_rainfall_exact_equality_triggers_under_default_ge_operator(default_engine):
    """Rule 3: Observed rainfall exactly at configured threshold triggers under default >= operator (IMD standard)."""
    obs = DynamicHazardObservation(
        observation_id="OBS-RAIN-003",
        village_id="VIL-CHAMOLI-001",
        rainfall_24h_mm=64.5,  # == 64.5
        location=(79.5, 30.5),
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.is_candidate is True
    assert result.explainability.trigger_evaluations[0].triggered is True


def test_custom_greater_than_operator_boundary():
    """Rule 4: When operator is strictly GREATER_THAN (>), exact equality does NOT trigger."""
    engine = DynamicRedZoneEngine.from_profile(
        RegionProfileId.HIMALAYAN_PILOT,
        rainfall_operator=ComparisonOperator.GREATER_THAN,
    )
    # At exact threshold: 64.5
    obs_equal = DynamicHazardObservation(
        observation_id="OBS-EQ",
        rainfall_24h_mm=64.5,
    )
    res_equal = engine.evaluate_observation(obs_equal)
    assert res_equal.status == DynamicTriggerStatus.NO_TRIGGER
    assert res_equal.is_candidate is False

    # Just above threshold: 64.6
    obs_above = DynamicHazardObservation(
        observation_id="OBS-ABOVE",
        rainfall_24h_mm=64.6,
    )
    res_above = engine.evaluate_observation(obs_above)
    assert res_above.status == DynamicTriggerStatus.TRIGGERED
    assert res_above.is_candidate is True


# =========================================================================
# 2. Seismic & Other Dynamic Indicator Tests
# =========================================================================


def test_seismic_trigger_evaluation(default_engine):
    """Rule 5: Seismic intensity breaching threshold triggers candidate zone."""
    # Himalayan seismic trigger is 6.0 MMI
    obs_triggered = DynamicHazardObservation(
        observation_id="OBS-SEIS-01",
        hazard_type="seismic",
        seismic_intensity_mmi=6.5,
        location=(79.5, 30.5),
    )
    res_triggered = default_engine.evaluate_observation(obs_triggered)
    assert res_triggered.status == DynamicTriggerStatus.TRIGGERED
    assert res_triggered.zone_type == RedZoneType.ACTIVE_SUBSIDENCE

    obs_safe = DynamicHazardObservation(
        observation_id="OBS-SEIS-02",
        hazard_type="seismic",
        seismic_intensity_mmi=4.5,
    )
    res_safe = default_engine.evaluate_observation(obs_safe)
    assert res_safe.status == DynamicTriggerStatus.NO_TRIGGER


def test_water_level_and_landslide_thresholds():
    """Rule 6: Water level and landslide debris volume triggers evaluated when configured."""
    engine = DynamicRedZoneEngine.from_profile(
        RegionProfileId.HIMALAYAN_PILOT,
        water_level_trigger_m=2.0,
        landslide_debris_volume_trigger_m3=5000.0,
    )

    # Flood water level test
    flood_obs = DynamicHazardObservation(
        observation_id="OBS-FLD-01",
        water_level_m_above_danger=2.5,
    )
    res_flood = engine.evaluate_observation(flood_obs)
    assert res_flood.status == DynamicTriggerStatus.TRIGGERED
    assert res_flood.zone_type == RedZoneType.FLOOD_INUNDATION

    # Landslide debris volume test
    ls_obs = DynamicHazardObservation(
        observation_id="OBS-LS-01",
        debris_volume_cu_m=6000.0,
    )
    res_ls = engine.evaluate_observation(ls_obs)
    assert res_ls.status == DynamicTriggerStatus.TRIGGERED
    assert res_ls.zone_type == RedZoneType.LANDSLIDE_DANGER


def test_configured_threshold_below_equal_above_semantics():
    """Prove configured threshold semantics: below -> NO_TRIGGER, equal -> operator behavior, above -> TRIGGERED."""
    # Configured threshold: water_level_trigger_m = 2.0 (default operator: >=)
    engine = DynamicRedZoneEngine.from_profile(
        RegionProfileId.HIMALAYAN_PILOT,
        water_level_trigger_m=2.0,
    )

    # 1. Below threshold (1.5 m < 2.0 m) -> NO_TRIGGER
    obs_below = DynamicHazardObservation(
        observation_id="OBS-WL-BELOW",
        water_level_m_above_danger=1.5,
    )
    res_below = engine.evaluate_observation(obs_below)
    assert res_below.status == DynamicTriggerStatus.NO_TRIGGER
    assert res_below.is_candidate is False
    assert res_below.danger_level is None
    assert res_below.explainability.trigger_evaluations[0].triggered is False
    assert res_below.explainability.trigger_evaluations[0].status == DynamicTriggerStatus.NO_TRIGGER

    # 2. Equal to threshold (2.0 m == 2.0 m) under default >= operator -> TRIGGERED
    obs_equal = DynamicHazardObservation(
        observation_id="OBS-WL-EQUAL",
        water_level_m_above_danger=2.0,
    )
    res_equal = engine.evaluate_observation(obs_equal)
    assert res_equal.status == DynamicTriggerStatus.TRIGGERED
    assert res_equal.is_candidate is True
    assert res_equal.danger_level == DangerLevel.VERY_HIGH
    assert res_equal.explainability.trigger_evaluations[0].triggered is True
    assert res_equal.explainability.trigger_evaluations[0].status == DynamicTriggerStatus.TRIGGERED

    # 3. Above threshold (2.8 m > 2.0 m) -> TRIGGERED
    obs_above = DynamicHazardObservation(
        observation_id="OBS-WL-ABOVE",
        water_level_m_above_danger=2.8,
    )
    res_above = engine.evaluate_observation(obs_above)
    assert res_above.status == DynamicTriggerStatus.TRIGGERED
    assert res_above.is_candidate is True
    assert res_above.danger_level == DangerLevel.VERY_HIGH
    assert res_above.explainability.trigger_evaluations[0].triggered is True


def test_missing_water_level_threshold_yields_insufficient_data(default_engine):
    """Prove missing water-level threshold -> INSUFFICIENT_DATA, no danger level, no candidate, explicit audit."""
    # In default Himalayan pilot engine, water_level_trigger_m_above_danger is not configured (None)
    assert default_engine.config.water_level_trigger_m_above_danger is None

    obs = DynamicHazardObservation(
        observation_id="OBS-WL-UNCONF",
        village_id="VIL-WL-001",
        water_level_m_above_danger=2.5,
        location=(79.5, 30.5),
    )
    res = default_engine.evaluate_observation(obs)

    # 4. Status is INSUFFICIENT_DATA
    assert res.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    # 6. Does not assign a danger level
    assert res.danger_level is None
    # 7. Does not create a dynamic red-zone candidate
    assert res.is_candidate is False
    assert res.geometry is None
    assert res.area_sq_km is None
    # 8. Explainability / audit records missing threshold configuration
    assert "threshold_for_water_level_above_danger" in res.explainability.missing_indicators
    assert "Required dynamic threshold configuration is unavailable" in res.explainability.decision_reason
    assert len(res.explainability.trigger_evaluations) == 1
    eval_record = res.explainability.trigger_evaluations[0]
    assert eval_record.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert eval_record.configured_threshold is None
    assert eval_record.triggered is False
    assert "Required threshold configuration is unavailable" in eval_record.audit_note


def test_missing_landslide_debris_threshold_yields_insufficient_data(default_engine):
    """Prove missing landslide debris threshold -> INSUFFICIENT_DATA, no danger level, no candidate, explicit audit."""
    # In default Himalayan pilot engine, landslide_debris_volume_trigger_m3 is not configured (None)
    assert default_engine.config.landslide_debris_volume_trigger_m3 is None

    obs = DynamicHazardObservation(
        observation_id="OBS-DEBRIS-UNCONF",
        village_id="VIL-LS-001",
        debris_volume_cu_m=5000.0,
        location=(79.5, 30.5),
    )
    res = default_engine.evaluate_observation(obs)

    # 5. Status is INSUFFICIENT_DATA
    assert res.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    # 6. Does not assign a danger level
    assert res.danger_level is None
    # 7. Does not create a dynamic red-zone candidate
    assert res.is_candidate is False
    assert res.geometry is None
    assert res.area_sq_km is None
    # 8. Explainability / audit records missing threshold configuration
    assert "threshold_for_landslide_debris_volume" in res.explainability.missing_indicators
    assert "Required dynamic threshold configuration is unavailable" in res.explainability.decision_reason
    assert len(res.explainability.trigger_evaluations) == 1
    eval_record = res.explainability.trigger_evaluations[0]
    assert eval_record.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert eval_record.configured_threshold is None
    assert eval_record.triggered is False
    assert "Required threshold configuration is unavailable" in eval_record.audit_note


def test_missing_threshold_strict_mode_raises_insufficient_geophysical_data(default_engine):
    """Prove missing threshold under strict=True raises InsufficientGeophysicalDataError."""
    obs = DynamicHazardObservation(
        observation_id="OBS-STRICT-THRESH",
        water_level_m_above_danger=2.5,
    )
    with pytest.raises(InsufficientGeophysicalDataError, match="Required dynamic threshold configuration for indicator"):
        default_engine.evaluate_observation(obs, strict=True)


def test_village_evaluation_with_unconfigured_threshold_yields_insufficient_data(default_engine):
    """Prove village evaluation containing unconfigured threshold yields INSUFFICIENT_DATA when no triggers fire."""
    obs_safe_rain = DynamicHazardObservation(
        observation_id="OBS-VIL-RAIN-SAFE",
        rainfall_24h_mm=25.0,
    )
    obs_unconf_water = DynamicHazardObservation(
        observation_id="OBS-VIL-WATER-UNCONF",
        water_level_m_above_danger=1.5,
    )
    res = default_engine.evaluate_village_observations(
        [obs_safe_rain, obs_unconf_water],
        village_id="VIL-TEST-UNCONF",
    )
    assert res.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert res.is_candidate is False
    assert res.danger_level is None
    assert "threshold_for_water_level_above_danger" in res.explainability.missing_indicators


# =========================================================================
# 3. Missing & Unavailable Data Safety Tests
# =========================================================================


def test_missing_observation_value_yields_insufficient_data(default_engine):
    """Rule 7: Missing or null observation value strictly yields INSUFFICIENT_DATA (never safe or 0)."""
    obs = DynamicHazardObservation(
        observation_id="OBS-MISSING",
        village_id="VIL-001",
        hazard_type="rainfall",
        observed_value=None,
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert result.is_candidate is False
    assert result.danger_level is None
    assert result.geometry is None
    assert "rainfall_24h" in result.explainability.missing_indicators


def test_unavailable_observation_yields_insufficient_data(default_engine):
    """Rule 8: An observation marked unavailable (is_available=False) yields INSUFFICIENT_DATA."""
    obs = DynamicHazardObservation(
        observation_id="OBS-UNAVAIL",
        village_id="VIL-001",
        rainfall_24h_mm=100.0,
        is_available=False,
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert result.is_candidate is False
    assert "unavailable_observation" in result.explainability.missing_indicators


def test_strict_mode_raises_on_missing_data(default_engine):
    """Rule 9: In strict mode, missing observation value raises InsufficientGeophysicalDataError."""
    obs = DynamicHazardObservation(
        observation_id="OBS-STRICT-MISS",
        hazard_type="rainfall",
        observed_value=None,
    )
    with pytest.raises(InsufficientGeophysicalDataError, match="Missing required numerical observation"):
        default_engine.evaluate_observation(obs, strict=True)


# =========================================================================
# 4. Invalid Numerical Rejection Tests
# =========================================================================


def test_nan_observation_rejected():
    """Rule 10: NaN values in observations are strictly rejected."""
    with pytest.raises(InvalidGeophysicalDataError, match="cannot be NaN or infinite"):
        DynamicHazardObservation(
            observation_id="OBS-NAN",
            rainfall_24h_mm=float("nan"),
        )


def test_inf_observation_rejected():
    """Rule 11: Infinite values in observations are strictly rejected."""
    with pytest.raises(InvalidGeophysicalDataError, match="cannot be NaN or infinite"):
        DynamicHazardObservation(
            observation_id="OBS-INF",
            seismic_intensity_mmi=float("inf"),
        )


def test_negative_precipitation_rejected():
    """Rule 12: Negative rainfall values are strictly rejected."""
    with pytest.raises(InvalidGeophysicalDataError, match="rainfall_24h_mm cannot be negative"):
        DynamicHazardObservation(
            observation_id="OBS-NEG-RAIN",
            rainfall_24h_mm=-10.0,
        )


def test_invalid_slope_bounds_rejected():
    """Rule 13: Slope values outside [0.0, 90.0] are strictly rejected."""
    with pytest.raises(InvalidGeophysicalDataError, match="slope_deg must be within"):
        DynamicHazardObservation(
            observation_id="OBS-INV-SLOPE",
            slope_deg=95.0,
        )


def test_invalid_seismic_mmi_bounds_rejected():
    """Rule 14: Seismic intensity outside [1.0, 12.0] is strictly rejected."""
    with pytest.raises(InvalidGeophysicalDataError, match="seismic_intensity_mmi must be within"):
        DynamicHazardObservation(
            observation_id="OBS-INV-SEIS",
            seismic_intensity_mmi=13.5,
        )


def test_invalid_threshold_config_rejected():
    """Rule 15: NaN or infinite threshold configurations raise RedZoneConfigError."""
    with pytest.raises(RedZoneConfigError, match="cannot be NaN or infinite"):
        DynamicThresholdConfig(
            rainfall_trigger_24h_mm=float("nan"),
            slope_trigger_min_deg=25.0,
        )


# =========================================================================
# 5. Regional Profile Resolution & Changing Threshold Tests
# =========================================================================


def test_regional_profile_threshold_resolution(himalayan_profile, coastal_profile, riverine_profile):
    """Rule 16: Dynamic thresholds resolve accurately from distinct regional profiles."""
    eng_him = DynamicRedZoneEngine.from_profile(himalayan_profile)
    eng_cst = DynamicRedZoneEngine.from_profile(coastal_profile)
    eng_riv = DynamicRedZoneEngine.from_profile(riverine_profile)

    assert eng_him.config.rainfall_trigger_24h_mm == 64.5
    assert eng_cst.config.rainfall_trigger_24h_mm == 80.0
    assert eng_riv.config.rainfall_trigger_24h_mm == 75.0

    assert eng_him.buffer_m == 500.0
    assert eng_cst.buffer_m == 1500.0
    assert eng_riv.buffer_m == 1000.0


def test_changing_profile_threshold_changes_trigger_result():
    """Rule 17: Changing configured threshold changes dynamic trigger result without modifying engine code."""
    # 70.0 mm rainfall
    obs = DynamicHazardObservation(
        observation_id="OBS-COMPARE",
        rainfall_24h_mm=70.0,
    )

    # In Himalayan (threshold = 64.5 mm) -> TRIGGERED (70.0 >= 64.5)
    eng_him = DynamicRedZoneEngine.from_profile(RegionProfileId.HIMALAYAN_PILOT)
    res_him = eng_him.evaluate_observation(obs)
    assert res_him.status == DynamicTriggerStatus.TRIGGERED

    # In Coastal (threshold = 80.0 mm) -> NO_TRIGGER (70.0 < 80.0)
    eng_cst = DynamicRedZoneEngine.from_profile(RegionProfileId.COASTAL_TEMPLATE)
    res_cst = eng_cst.evaluate_observation(obs)
    assert res_cst.status == DynamicTriggerStatus.NO_TRIGGER


def test_strict_repeated_evaluation_determinism(default_engine):
    """Rule 18: Repeated evaluations of the same observation produce strictly identical results."""
    obs = DynamicHazardObservation(
        observation_id="OBS-DET-01",
        village_id="VIL-DETERMINISTIC",
        rainfall_24h_mm=72.4,
        location=(79.52, 30.48),
    )

    res1 = default_engine.evaluate_observation(obs)
    res2 = default_engine.evaluate_observation(obs)

    assert res1.status == res2.status
    assert res1.is_candidate == res2.is_candidate
    assert res1.danger_level == res2.danger_level
    assert res1.area_sq_km == res2.area_sq_km
    assert res1.explainability.decision_reason == res2.explainability.decision_reason


# =========================================================================
# 6. Spatial Geometry & Overlap Dissolution Tests
# =========================================================================


def test_point_observation_produces_geodesic_buffer(default_engine):
    """Rule 19: Point location produces geodesic circular buffer with valid MultiPolygon in EPSG:4326."""
    obs = DynamicHazardObservation(
        observation_id="OBS-PT-01",
        rainfall_24h_mm=85.0,
        location=(79.5, 30.5),
    )
    result = default_engine.evaluate_observation(obs)

    assert result.geometry is not None
    assert isinstance(result.geometry, MultiPolygon)
    assert result.geometry.is_valid
    assert result.area_sq_km is not None
    assert result.area_sq_km > 0.0
    # For a 500m radius circle, area is ~pi * 0.5^2 ~= 0.785 sq km
    assert 0.75 < result.area_sq_km < 0.85


def test_polygonal_observation_normalized_to_multipolygon(default_engine):
    """Rule 20: Pre-existing polygon observation is normalized to valid MultiPolygon."""
    poly = Polygon([(79.5, 30.5), (79.51, 30.5), (79.51, 30.51), (79.5, 30.51), (79.5, 30.5)])
    obs = DynamicHazardObservation(
        observation_id="OBS-POLY-01",
        rainfall_24h_mm=90.0,
        geometry=poly,
    )
    result = default_engine.evaluate_observation(obs)

    assert result.geometry is not None
    assert isinstance(result.geometry, MultiPolygon)
    assert result.geometry.is_valid


def test_missing_location_produces_none_geometry_without_fabrication(default_engine):
    """Rule 21: If observation has no spatial location, geometry is None; no polygon is fabricated."""
    obs = DynamicHazardObservation(
        observation_id="OBS-NO-GEOM",
        rainfall_24h_mm=90.0,
        location=None,
        geometry=None,
    )
    result = default_engine.evaluate_observation(obs)

    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.is_candidate is True
    assert result.geometry is None
    assert result.area_sq_km is None


def test_overlapping_dynamic_zones_dissolve_preserving_provenance(default_engine):
    """Rule 22: Overlapping triggered candidates dissolve into unified perimeter with full provenance."""
    cand1 = default_engine.evaluate_observation(
        DynamicHazardObservation(
            observation_id="OBS-A",
            village_id="VIL-A",
            rainfall_24h_mm=80.0,
            location=(79.500, 30.500),
            provenance={"source": "IMD-Station-1"},
        )
    )
    cand2 = default_engine.evaluate_observation(
        DynamicHazardObservation(
            observation_id="OBS-B",
            village_id="VIL-B",
            rainfall_24h_mm=85.0,
            location=(79.503, 30.503),  # ~400m apart, overlapping 500m buffers
            provenance={"source": "IMD-Station-2"},
        )
    )

    dissolved = default_engine.dissolve_overlapping_dynamic_zones([cand1, cand2])

    assert len(dissolved) == 1
    d_zone = dissolved[0]
    assert d_zone.status == DynamicTriggerStatus.TRIGGERED
    assert d_zone.explainability.is_dissolved is True
    assert d_zone.explainability.dissolved_count == 2
    assert "OBS-A" in d_zone.contributing_observation_ids
    assert "OBS-B" in d_zone.contributing_observation_ids
    assert "VIL-A" in d_zone.contributing_village_ids
    assert "VIL-B" in d_zone.contributing_village_ids
    assert len(d_zone.explainability.source_provenance) == 2


def test_non_overlapping_candidates_remain_separate(default_engine):
    """Rule 23: Spatially distant candidates do not dissolve."""
    cand1 = default_engine.evaluate_observation(
        DynamicHazardObservation(
            observation_id="OBS-FAR-1",
            village_id="VIL-FAR-1",
            rainfall_24h_mm=80.0,
            location=(79.0, 30.0),
        )
    )
    cand2 = default_engine.evaluate_observation(
        DynamicHazardObservation(
            observation_id="OBS-FAR-2",
            village_id="VIL-FAR-2",
            rainfall_24h_mm=85.0,
            location=(80.0, 31.0),
        )
    )

    dissolved = default_engine.dissolve_overlapping_dynamic_zones([cand1, cand2])
    assert len(dissolved) == 2


# =========================================================================
# 7. Multi-Observation & Compound Triggers
# =========================================================================


def test_village_multi_observation_compound_trigger(default_engine):
    """Rule 24: Compound rainfall + slope breaches compound trigger in village evaluation."""
    obs_rain = DynamicHazardObservation(
        observation_id="OBS-C-RAIN",
        village_id="VIL-HILL-01",
        rainfall_24h_mm=70.0,  # >= 64.5
    )
    obs_slope = DynamicHazardObservation(
        observation_id="OBS-C-SLOPE",
        village_id="VIL-HILL-01",
        slope_deg=32.0,  # >= 25.0
    )

    res = default_engine.evaluate_village_observations(
        [obs_rain, obs_slope],
        village_id="VIL-HILL-01",
        location=(79.5, 30.5),
    )

    assert res.status == DynamicTriggerStatus.TRIGGERED
    assert res.is_candidate is True
    assert "compound_rainfall_slope" in res.explainability.triggered_indicators
    assert res.zone_type == RedZoneType.COMPOUND_DANGER
    assert len(res.contributing_observation_ids) == 2


def test_village_multi_observation_all_safe_yields_no_trigger(default_engine):
    """Rule 25: All safe observations yield NO_TRIGGER for village."""
    obs_rain = DynamicHazardObservation(
        observation_id="OBS-S-RAIN",
        rainfall_24h_mm=30.0,
    )
    obs_seis = DynamicHazardObservation(
        observation_id="OBS-S-SEIS",
        seismic_intensity_mmi=3.0,
    )

    res = default_engine.evaluate_village_observations(
        [obs_rain, obs_seis],
        village_id="VIL-SAFE-01",
    )

    assert res.status == DynamicTriggerStatus.NO_TRIGGER
    assert res.is_candidate is False
    assert res.danger_level is None


def test_village_multi_observation_with_missing_and_no_trigger_yields_insufficient_data(default_engine):
    """Rule 26: Missing data with no active triggers yields INSUFFICIENT_DATA (never safe)."""
    obs_safe = DynamicHazardObservation(
        observation_id="OBS-SAFE",
        rainfall_24h_mm=20.0,
    )
    obs_missing = DynamicHazardObservation(
        observation_id="OBS-MISS",
        hazard_type="seismic",
        observed_value=None,
    )

    res = default_engine.evaluate_village_observations(
        [obs_safe, obs_missing],
        village_id="VIL-UNKNOWN-01",
    )

    assert res.status == DynamicTriggerStatus.INSUFFICIENT_DATA
    assert res.is_candidate is False


# =========================================================================
# 8. Governance Invariants & Separation from Permanent Red Zones
# =========================================================================


def test_governance_invariants_candidate_not_active(default_engine):
    """Rule 27: Candidate zone strictly enforces is_active=False and declared_by_officer_id=None."""
    obs = DynamicHazardObservation(
        observation_id="OBS-GOV",
        rainfall_24h_mm=90.0,
    )
    result = default_engine.evaluate_observation(obs)

    assert result.is_active is False
    assert result.declared_by_officer_id is None
    assert result.declared_at is None
    assert "PROPOSED DYNAMIC ALERT CANDIDATE ONLY" in result.explainability.governance_notice


def test_governance_validation_rejects_active_flag(default_engine):
    """Rule 28: Direct instantiation of candidate with is_active=True raises ValueError."""
    with pytest.raises(ValueError, match="cannot have is_active=True"):
        DynamicRedZoneCandidate(
            candidate_id="TEST",
            status=DynamicTriggerStatus.TRIGGERED,
            is_candidate=True,
            is_active=True,  # Violates governance invariant
            zone_type=RedZoneType.FLOOD_INUNDATION,
            danger_level=DangerLevel.VERY_HIGH,
            explainability=default_engine.evaluate_observation(
                DynamicHazardObservation(rainfall_24h_mm=80.0)
            ).explainability,
        )


def test_dynamic_zone_remains_distinct_from_permanent_m3_10_zone(himalayan_profile):
    """Rule 29: Dynamic candidates (M3-11) and Permanent candidates (M3-10) are semantically distinguishable."""
    perm_engine = PermanentRedZoneEngine.from_profile(himalayan_profile)
    dyn_engine = DynamicRedZoneEngine.from_profile(himalayan_profile)

    perm_cand = perm_engine.evaluate_village({
        "village_id": "VIL-TEST",
        "active_subsidence": True,
        "slope_deg": 36.0,
        "historical_landslide_count": 2,
        "location": (79.5, 30.5),
    })

    dyn_cand = dyn_engine.evaluate_observation(
        DynamicHazardObservation(
            village_id="VIL-TEST",
            rainfall_24h_mm=80.0,
        )
    )

    assert isinstance(perm_cand, PermanentRedZoneCandidate)
    assert isinstance(dyn_cand, DynamicRedZoneCandidate)
    assert dyn_cand.is_temporary is True
    assert getattr(perm_cand, "is_temporary", False) is False
    assert perm_cand.status == RedZoneStatus.PROPOSED
    assert dyn_cand.status == DynamicTriggerStatus.TRIGGERED


# =========================================================================
# 9. Adapter Coercion from M3-03 Contracts
# =========================================================================


def test_coercion_from_normalized_rainfall_record(default_engine):
    """Rule 30: Engine directly consumes M3-03 NormalizedRainfallRecord."""
    rec = NormalizedRainfallRecord(
        record_id="RAIN-REC-01",
        observed_at="2026-09-06T00:00:00Z",
        location_coordinates=(79.5, 30.5),
        village_id="VIL-001",
        village_name="Test Village",
        rainfall_24h_mm=78.0,
        severity="very_high",
        is_heavy_rain=True,
        provenance=ProviderProvenance(
            provider_id="mock_imd",
            provider_name="IMD Mock Provider",
            mode=ProviderMode.MOCK,
        ),
    )

    result = default_engine.evaluate_observation(rec)
    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.explainability.source_observation_ids == ["RAIN-REC-01"]
    assert result.explainability.source_provenance[0]["provider_id"] == "mock_imd"


def test_coercion_from_normalized_flood_record():
    """Rule 31: Engine directly consumes M3-03 NormalizedFloodRecord when flood threshold configured."""
    engine = DynamicRedZoneEngine.from_profile(
        RegionProfileId.HIMALAYAN_PILOT,
        water_level_trigger_m=1.5,
    )
    rec = NormalizedFloodRecord(
        record_id="FLD-REC-01",
        observed_at="2026-09-06T00:00:00Z",
        location_coordinates=(79.5, 30.5),
        village_id="VIL-002",
        water_level_m_above_danger=2.0,
        flood_type="flash_flood",
        severity="critical",
        provenance=ProviderProvenance(
            provider_id="mock_cwc",
            provider_name="CWC Mock Provider",
            mode=ProviderMode.MOCK,
        ),
    )

    result = engine.evaluate_observation(rec)
    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.zone_type == RedZoneType.FLOOD_INUNDATION


def test_coercion_from_normalized_landslide_record():
    """Rule 32: Engine directly consumes M3-03 NormalizedLandslideRecord when debris threshold configured."""
    engine = DynamicRedZoneEngine.from_profile(
        RegionProfileId.HIMALAYAN_PILOT,
        landslide_debris_volume_trigger_m3=3000.0,
    )
    rec = NormalizedLandslideRecord(
        record_id="LS-REC-01",
        observed_at="2026-09-06T00:00:00Z",
        location_coordinates=(79.5, 30.5),
        village_id="VIL-003",
        debris_volume_cu_m=4500.0,
        severity="critical",
        road_blocked=True,
        provenance=ProviderProvenance(
            provider_id="mock_gsi",
            provider_name="GSI Mock Provider",
            mode=ProviderMode.MOCK,
        ),
    )

    result = engine.evaluate_observation(rec)
    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.zone_type == RedZoneType.LANDSLIDE_DANGER


def test_coercion_from_normalized_hazard_observation_record(default_engine):
    """Rule 33: Engine directly consumes generalized NormalizedHazardObservationRecord."""
    rec = NormalizedHazardObservationRecord(
        record_id="GEN-HAZ-01",
        observed_at="2026-09-06T00:00:00Z",
        location_coordinates=(79.5, 30.5),
        village_id="VIL-004",
        hazard_type="rainfall",
        intensity_value=82.0,
        intensity_unit="mm",
        severity="high",
        provenance=ProviderProvenance(
            provider_id="mock_telemetry",
            provider_name="Telemetry Mock Provider",
            mode=ProviderMode.MOCK,
        ),
    )

    result = default_engine.evaluate_observation(rec)
    assert result.status == DynamicTriggerStatus.TRIGGERED
    assert result.explainability.trigger_evaluations[0].observed_value == 82.0

