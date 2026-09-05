"""Comprehensive unit and regression test suite for Permanent Red Zone Demarcation (Chunk M3-10)."""

import math
import pytest
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely import wkt

from app.core.profiles import get_profile
from app.core.profiles.models import DangerLevel, RegionProfileId
from app.core.risk.classification.contracts import RiskBand
from app.core.risk.red_zone.contracts import (
    GeophysicalObservationInput,
    PermanentRedZoneCandidate,
    PermanentRedZoneExplainability,
    RedZoneStatus,
    RedZoneType,
    TriggerAudit,
)
from app.core.risk.red_zone.engine import PermanentRedZoneEngine
from app.core.risk.red_zone.errors import (
    InsufficientGeophysicalDataError,
    InvalidGeophysicalDataError,
    RedZoneConfigError,
    RedZoneError,
    SpatialGeometryError,
)
from app.core.risk.red_zone.geometry import (
    calculate_geodesic_area_sq_km,
    create_geodesic_buffer,
    dissolve_overlapping_candidates,
    normalize_to_multipolygon,
)


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def himalayan_engine() -> PermanentRedZoneEngine:
    return PermanentRedZoneEngine(profile=get_profile(RegionProfileId.HIMALAYAN_PILOT))


@pytest.fixture
def riverine_engine() -> PermanentRedZoneEngine:
    return PermanentRedZoneEngine(profile=get_profile(RegionProfileId.RIVERINE_TEMPLATE))


@pytest.fixture
def coastal_engine() -> PermanentRedZoneEngine:
    return PermanentRedZoneEngine(profile=get_profile(RegionProfileId.COASTAL_TEMPLATE))


@pytest.fixture
def default_engine() -> PermanentRedZoneEngine:
    return PermanentRedZoneEngine()


@pytest.fixture
def sample_point() -> Point:
    # Joshimath area coordinates: lat 30.556, lon 79.567
    return Point(79.567, 30.556)


@pytest.fixture
def sample_polygon() -> Polygon:
    return Polygon([
        (79.560, 30.550),
        (79.570, 30.550),
        (79.570, 30.560),
        (79.560, 30.560),
        (79.560, 30.550),
    ])


# =====================================================================
# 1. Active subsidence trigger
# =====================================================================


def test_active_subsidence_triggers_candidate(himalayan_engine: PermanentRedZoneEngine, sample_point: Point):
    """Rule 1: active_subsidence == True triggers a permanent red zone candidate."""
    obs = GeophysicalObservationInput(
        village_id="vil_subsidence_001",
        village_name="Joshimath Upper Ward",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=10.0,  # Below slope threshold
        historical_landslide_count=0,  # Below landslide threshold
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.ACTIVE_SUBSIDENCE
    assert candidate.danger_level == DangerLevel.UNINHABITABLE
    assert candidate.explainability.active_subsidence_triggered is True
    assert candidate.explainability.compound_hazard_triggered is False
    assert "Active ground subsidence" in candidate.explainability.trigger_summary
    assert candidate.geometry.geom_type == "MultiPolygon"
    assert candidate.is_active is False
    assert candidate.declared_by_officer_id is None


# =====================================================================
# 2. Slope + historical landslide thresholds trigger candidate
# =====================================================================


def test_slope_and_historical_landslides_trigger_candidate(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 2: slope >= 35 deg and historical_landslides >= 1 triggers landslide danger."""
    obs = GeophysicalObservationInput(
        village_id="vil_landslide_001",
        village_name="Raini Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=42.5,
        historical_landslide_count=3,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.LANDSLIDE_DANGER
    # Preserves configured default_danger_level (no invented trigger-based CRITICAL mapping)
    assert candidate.danger_level == himalayan_engine.default_danger_level
    assert candidate.danger_level != DangerLevel.CRITICAL
    assert candidate.explainability.active_subsidence_triggered is False
    assert candidate.explainability.compound_hazard_triggered is True
    assert candidate.explainability.slope_threshold_met is True
    assert candidate.explainability.historical_landslides_threshold_met is True
    assert candidate.geometry.geom_type == "MultiPolygon"


def test_compound_danger_when_both_triggers_active(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """When both active subsidence and compound landslide rules trigger, danger is COMPOUND."""
    obs = GeophysicalObservationInput(
        village_id="vil_compound_001",
        village_name="Helang Sector",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=45.0,
        historical_landslide_count=5,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.COMPOUND_DANGER
    assert candidate.danger_level == DangerLevel.UNINHABITABLE
    assert candidate.explainability.active_subsidence_triggered is True
    assert candidate.explainability.compound_hazard_triggered is True


# =====================================================================
# 3. Values exactly at thresholds are handled correctly
# =====================================================================


def test_values_exactly_at_thresholds_trigger_candidate(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 3: values exactly at min_slope_deg (35.0) and min_historical_landslides (1) trigger candidate."""
    obs = GeophysicalObservationInput(
        village_id="vil_boundary_001",
        village_name="Boundary Test Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=35.0,  # Exactly Himalayan threshold
        historical_landslide_count=1,  # Exactly Himalayan threshold
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.LANDSLIDE_DANGER
    assert candidate.explainability.slope_threshold_met is True
    assert candidate.explainability.historical_landslides_threshold_met is True


# =====================================================================
# 4. Values below thresholds do not trigger compound rule
# =====================================================================


@pytest.mark.parametrize(
    "slope,landslides",
    [
        (34.9, 5),  # Slope just below 35.0
        (45.0, 0),  # Landslides below 1
        (34.9, 0),  # Both below
        (10.0, 0),  # Well below
    ],
)
def test_values_below_thresholds_do_not_trigger(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point, slope: float, landslides: int
):
    """Rule 4: Values failing either slope or landslide threshold do not trigger."""
    obs = GeophysicalObservationInput(
        village_id="vil_safe_001",
        village_name="Safe Foothill Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=slope,
        historical_landslide_count=landslides,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.NOT_DEMARCATED
    assert candidate.danger_level is None
    assert candidate.explainability.compound_hazard_triggered is False
    assert candidate.explainability.active_subsidence_triggered is False


# =====================================================================
# 5. Upstream CRITICAL risk corroborates candidate
# =====================================================================


def test_critical_risk_corroborates_candidate(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 5: Upstream CRITICAL risk corroborates permanent red-zone candidate."""
    obs = GeophysicalObservationInput(
        village_id="vil_crit_001",
        village_name="High Risk Critical Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=38.0,
        historical_landslide_count=2,
        upstream_risk_band=RiskBand.CRITICAL,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.explainability.risk_band_corroborated is True
    assert "Corroborated by upstream composite risk classification CRITICAL" in candidate.explainability.trigger_summary


def test_critical_risk_with_subsidence(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Active subsidence + CRITICAL risk band provides maximum corroboration."""
    obs = GeophysicalObservationInput(
        village_id="vil_crit_sub_001",
        village_name="Subsiding Critical Ward",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=20.0,
        historical_landslide_count=0,
        upstream_risk_band=RiskBand.CRITICAL,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.explainability.risk_band_corroborated is True
    assert candidate.danger_level == DangerLevel.UNINHABITABLE


# =====================================================================
# 6. SAFE/MODERATE + steep slope without subsidence becomes MONITOR
# =====================================================================


@pytest.mark.parametrize("risk_band", [RiskBand.SAFE, RiskBand.MODERATE])
def test_safe_or_moderate_with_steep_slope_becomes_monitor(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point, risk_band: RiskBand
):
    """Rule 6: SAFE or MODERATE combined with steep slope without active subsidence must not silently become red zone -> MONITOR."""
    obs = GeophysicalObservationInput(
        village_id="vil_monitor_001",
        village_name="Monitored Ridge Village",
        location_geometry=sample_point,
        active_subsidence=False,  # No active subsidence
        slope_deg=40.0,  # Steep slope
        historical_landslide_count=2,  # History of landslides
        upstream_risk_band=risk_band,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.MONITOR
    # MONITOR status has no candidate danger_level assigned (no invented VERY_HIGH mapping)
    assert candidate.danger_level is None
    assert candidate.explainability.monitoring_recommended is True
    assert "downgraded from proposed red zone to MONITOR" in candidate.explainability.trigger_summary


def test_safe_or_moderate_with_active_subsidence_still_triggers_candidate(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Active subsidence overrides SAFE/MODERATE because subsidence is an immediate physical failure."""
    obs = GeophysicalObservationInput(
        village_id="vil_sub_safe_001",
        village_name="Subsiding Low Composite Risk Village",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=20.0,
        historical_landslide_count=0,
        upstream_risk_band=RiskBand.SAFE,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.ACTIVE_SUBSIDENCE
    assert candidate.danger_level == DangerLevel.UNINHABITABLE


# =====================================================================
# 7. Missing slope is INSUFFICIENT_DATA
# =====================================================================


def test_missing_slope_yields_insufficient_data(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 7: Missing slope is INSUFFICIENT_DATA (never interpreted as safe or 0)."""
    obs = GeophysicalObservationInput(
        village_id="vil_no_slope_001",
        village_name="Unsurveyed Ridge Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=None,  # Missing slope
        historical_landslide_count=2,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.INSUFFICIENT_DATA
    assert candidate.danger_level is None
    assert "slope_deg" in candidate.explainability.missing_required_indicators
    assert "Missing required geophysical indicator(s)" in candidate.explainability.trigger_summary


def test_strict_mode_raises_on_missing_slope(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """When strict=True, missing required data raises InsufficientGeophysicalDataError."""
    obs = GeophysicalObservationInput(
        village_id="vil_no_slope_002",
        village_name="Strict Missing Slope",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=None,
        historical_landslide_count=2,
    )

    with pytest.raises(InsufficientGeophysicalDataError) as exc_info:
        himalayan_engine.evaluate_village(obs, strict=True)
    assert "slope_deg" in exc_info.value.missing_fields


# =====================================================================
# 8. Missing historical landslide count is INSUFFICIENT_DATA
# =====================================================================


def test_missing_landslide_count_yields_insufficient_data(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 8: Missing historical landslide count is INSUFFICIENT_DATA where required."""
    obs = GeophysicalObservationInput(
        village_id="vil_no_ls_001",
        village_name="Unrecorded Landslides Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=40.0,
        historical_landslide_count=None,  # Missing landslides
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.INSUFFICIENT_DATA
    assert candidate.danger_level is None
    assert "historical_landslide_count" in candidate.explainability.missing_required_indicators


# =====================================================================
# 9. Missing subsidence information is not converted to false/safe
# =====================================================================


def test_missing_subsidence_yields_insufficient_data(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 9: Missing subsidence must not be defaulted to False/safe."""
    obs = GeophysicalObservationInput(
        village_id="vil_no_sub_001",
        village_name="Unsurveyed Subsidence Village",
        location_geometry=sample_point,
        active_subsidence=None,  # Missing subsidence
        slope_deg=20.0,
        historical_landslide_count=0,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.status == RedZoneStatus.INSUFFICIENT_DATA
    assert "active_subsidence" in candidate.explainability.missing_required_indicators


# =====================================================================
# 10. Point input produces valid MultiPolygon using configured buffer
# =====================================================================


def test_point_input_produces_valid_multipolygon(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 10: Point input creates geodesic circular buffer using regional profile's hazard_buffer_m (500m)."""
    obs = GeophysicalObservationInput(
        village_id="vil_buffer_001",
        village_name="Buffered Village",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.geometry.geom_type == "MultiPolygon"
    assert candidate.geometry.is_valid
    assert not candidate.geometry.is_empty
    assert candidate.buffer_distance_applied_m == 500.0

    # Area of circular buffer with r=500m should be approx pi * 0.5^2 = 0.7854 sq km
    expected_area = math.pi * (0.5**2)
    assert pytest.approx(candidate.area_sq_km, rel=0.05) == expected_area


def test_create_geodesic_buffer_directly():
    """Geodesic buffer utility produces valid MultiPolygon with accurate metric area."""
    pt = Point(79.567, 30.556)
    mp = create_geodesic_buffer(pt, buffer_distance_m=500.0)

    assert isinstance(mp, MultiPolygon)
    assert mp.is_valid
    area_sq_km = calculate_geodesic_area_sq_km(mp)
    expected_area = math.pi * (0.5**2)
    assert pytest.approx(area_sq_km, rel=0.05) == expected_area


# =====================================================================
# 11. Polygon / MultiPolygon input is normalized correctly
# =====================================================================


def test_polygon_input_normalized_to_multipolygon(
    himalayan_engine: PermanentRedZoneEngine, sample_polygon: Polygon
):
    """Rule 11: Polygon input is normalized to valid MultiPolygon directly without buffering."""
    obs = GeophysicalObservationInput(
        village_id="vil_poly_001",
        village_name="Hazard Polygon Area",
        location_geometry=sample_polygon,
        active_subsidence=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.geometry.geom_type == "MultiPolygon"
    assert candidate.geometry.is_valid
    assert candidate.buffer_distance_applied_m is None
    assert candidate.area_sq_km > 0.0


def test_normalize_to_multipolygon_handles_geojson_dict():
    """normalize_to_multipolygon converts geojson dict to MultiPolygon."""
    geojson_poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.560, 30.550],
                [79.570, 30.550],
                [79.570, 30.560],
                [79.560, 30.560],
                [79.560, 30.550],
            ]
        ],
    }
    mp = normalize_to_multipolygon(geojson_poly)
    assert isinstance(mp, MultiPolygon)
    assert mp.is_valid


# =====================================================================
# 12. Overlapping candidates dissolve without losing provenance
# =====================================================================


def test_overlapping_candidates_dissolve_preserving_provenance(
    himalayan_engine: PermanentRedZoneEngine,
):
    """Rule 12: Overlapping candidates dissolve into single MultiPolygon without losing provenance or source IDs."""
    # Two adjacent points 400m apart (buffer radius is 500m, so they will overlap)
    pt1 = Point(79.567, 30.556)
    pt2 = Point(79.567, 30.559)

    obs1 = GeophysicalObservationInput(
        village_id="vil_overlap_A",
        village_name="Ward Alpha",
        location_geometry=pt1,
        active_subsidence=True,
        slope_deg=38.0,
        historical_landslide_count=2,
    )
    obs2 = GeophysicalObservationInput(
        village_id="vil_overlap_B",
        village_name="Ward Beta",
        location_geometry=pt2,
        active_subsidence=False,
        slope_deg=40.0,
        historical_landslide_count=3,
    )

    # Batch demarcation
    dissolved = himalayan_engine.demarcate_permanent_red_zones([obs1, obs2], dissolve=True)

    assert len(dissolved) == 1
    merged = dissolved[0]
    assert merged.status == RedZoneStatus.PROPOSED
    assert merged.danger_level == himalayan_engine.default_danger_level
    assert "vil_overlap_A" in merged.contributing_village_ids
    assert "vil_overlap_B" in merged.contributing_village_ids
    assert len(merged.contributing_village_ids) == 2
    assert merged.geometry.geom_type == "MultiPolygon"
    assert merged.geometry.is_valid

    # Check that provenance/explainability holds details for both
    assert "vil_overlap_A" in merged.explainability.source_village_provenance
    assert "vil_overlap_B" in merged.explainability.source_village_provenance
    assert len(merged.explainability.trigger_audits) == 2


def test_non_overlapping_candidates_remain_separate(himalayan_engine: PermanentRedZoneEngine):
    """Non-overlapping candidates remain distinct candidates when dissolved."""
    pt1 = Point(79.500, 30.500)
    pt2 = Point(79.700, 30.700)  # Several kilometers away

    obs1 = GeophysicalObservationInput(
        village_id="vil_far_1",
        village_name="Far Village 1",
        location_geometry=pt1,
        active_subsidence=True,
    )
    obs2 = GeophysicalObservationInput(
        village_id="vil_far_2",
        village_name="Far Village 2",
        location_geometry=pt2,
        active_subsidence=True,
    )

    dissolved = himalayan_engine.demarcate_permanent_red_zones([obs1, obs2], dissolve=True)
    assert len(dissolved) == 2


# =====================================================================
# 13. Output remains EPSG:4326 / SRID 4326
# =====================================================================


def test_geometry_srid_is_4326(himalayan_engine: PermanentRedZoneEngine, sample_point: Point):
    """Rule 13: Output geometry remains EPSG:4326 / SRID 4326."""
    obs = GeophysicalObservationInput(
        village_id="vil_srid_001",
        village_name="SRID Check Village",
        location_geometry=sample_point,
        active_subsidence=True,
    )

    candidate = himalayan_engine.evaluate_village(obs)
    assert candidate.srid == 4326

    # Verify bounding box is in geographic degree range (-180..180, -90..90)
    minx, miny, maxx, maxy = candidate.geometry.bounds
    assert -180.0 <= minx <= 180.0
    assert -90.0 <= miny <= 90.0
    assert -180.0 <= maxx <= 180.0
    assert -90.0 <= maxy <= 90.0


# =====================================================================
# 14. Governance invariants enforced
# =====================================================================


def test_governance_invariants_candidate_not_officer_declared(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 14: Candidate output does not imply officer or legal declaration."""
    obs = GeophysicalObservationInput(
        village_id="vil_gov_001",
        village_name="Governance Village",
        location_geometry=sample_point,
        active_subsidence=True,
    )

    candidate = himalayan_engine.evaluate_village(obs)

    assert candidate.is_active is False
    assert candidate.declared_by_officer_id is None
    assert candidate.declared_at is None
    assert "proposed" in candidate.status.value
    assert "CANDIDATE ONLY" in candidate.explainability.governance_notice


def test_governance_validation_rejects_active_flag(sample_polygon: Polygon):
    """PermanentRedZoneCandidate raises error if instantiated with is_active=True."""
    mp = normalize_to_multipolygon(sample_polygon)
    audit = TriggerAudit(
        village_id="v1",
        active_subsidence_triggered=True,
        slope_deg=35.0,
        historical_landslide_count=1,
        active_subsidence_triggered_met=True,
        compound_hazard_triggered=False,
    )
    explainability = PermanentRedZoneExplainability(
        trigger_summary="Test summary",
        trigger_audits=[audit],
    )

    with pytest.raises(ValueError, match="must be False for candidate zones"):
        PermanentRedZoneCandidate(
            candidate_id="cand_test",
            status=RedZoneStatus.PROPOSED,
            zone_type=RedZoneType.ACTIVE_SUBSIDENCE,
            danger_level=DangerLevel.UNINHABITABLE,
            contributing_village_ids=["v1"],
            geometry=mp,
            area_sq_km=1.0,
            explainability=explainability,
            is_candidate=True,
            is_active=True,  # Violates governance invariant
        )


def test_governance_validation_rejects_officer_declaration(sample_polygon: Polygon):
    """PermanentRedZoneCandidate raises error if instantiated with declared_by_officer_id."""
    mp = normalize_to_multipolygon(sample_polygon)
    audit = TriggerAudit(
        village_id="v1",
        active_subsidence_triggered=True,
        slope_deg=35.0,
        historical_landslide_count=1,
        active_subsidence_triggered_met=True,
        compound_hazard_triggered=False,
    )
    explainability = PermanentRedZoneExplainability(
        trigger_summary="Test summary",
        trigger_audits=[audit],
    )

    with pytest.raises(ValueError, match="declared_by_officer_id must be None"):
        PermanentRedZoneCandidate(
            candidate_id="cand_test",
            status=RedZoneStatus.PROPOSED,
            zone_type=RedZoneType.ACTIVE_SUBSIDENCE,
            danger_level=DangerLevel.UNINHABITABLE,
            contributing_village_ids=["v1"],
            geometry=mp,
            area_sq_km=1.0,
            explainability=explainability,
            is_candidate=True,
            declared_by_officer_id=999,  # Violates governance invariant
        )


# =====================================================================
# 15. Strict determinism across repeated inputs
# =====================================================================


def test_strict_determinism_across_repeated_evaluations(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Rule 15: Repeated evaluations with identical inputs produce bitwise deterministic results."""
    obs = GeophysicalObservationInput(
        village_id="vil_det_001",
        village_name="Deterministic Ridge",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=40.0,
        historical_landslide_count=2,
    )

    res1 = himalayan_engine.evaluate_village(obs)
    res2 = himalayan_engine.evaluate_village(obs)

    assert res1.candidate_id == res2.candidate_id
    assert res1.status == res2.status
    assert res1.zone_type == res2.zone_type
    assert res1.danger_level == res2.danger_level
    assert res1.area_sq_km == res2.area_sq_km
    assert res1.geometry.equals(res2.geometry)


# =====================================================================
# 16. Regional profile threshold variations
# =====================================================================


def test_riverine_template_thresholds(riverine_engine: PermanentRedZoneEngine, sample_point: Point):
    """Riverine template profile: min_slope_deg=15.0, min_historical_landslides=0."""
    obs = GeophysicalObservationInput(
        village_id="vil_riv_001",
        village_name="Riverbank Village",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=15.5,
        historical_landslide_count=0,
    )

    candidate = riverine_engine.evaluate_village(obs)
    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.LANDSLIDE_DANGER


def test_coastal_template_thresholds(coastal_engine: PermanentRedZoneEngine, sample_point: Point):
    """Coastal template profile: min_slope_deg=10.0, min_historical_landslides=0."""
    obs = GeophysicalObservationInput(
        village_id="vil_coast_001",
        village_name="Cliffside Fishery",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=10.5,
        historical_landslide_count=0,
    )

    candidate = coastal_engine.evaluate_village(obs)
    assert candidate.status == RedZoneStatus.PROPOSED
    assert candidate.zone_type == RedZoneType.LANDSLIDE_DANGER


# =====================================================================
# 17. Input validation and error cases
# =====================================================================


def test_invalid_negative_slope():
    """GeophysicalObservationInput rejects negative slope."""
    with pytest.raises(InvalidGeophysicalDataError, match="must be within"):
        GeophysicalObservationInput(
            village_id="v1",
            slope_deg=-5.0,
        )


def test_invalid_slope_exceeding_90():
    """GeophysicalObservationInput rejects slope > 90 degrees."""
    with pytest.raises(InvalidGeophysicalDataError, match="must be within"):
        GeophysicalObservationInput(
            village_id="v1",
            slope_deg=95.0,
        )


def test_invalid_negative_landslides():
    """GeophysicalObservationInput rejects negative landslide count."""
    with pytest.raises(InvalidGeophysicalDataError, match="cannot be negative"):
        GeophysicalObservationInput(
            village_id="v1",
            historical_landslide_count=-1,
        )


def test_invalid_nan_slope():
    """GeophysicalObservationInput rejects NaN slope."""
    with pytest.raises(InvalidGeophysicalDataError, match="cannot be NaN or infinite"):
        GeophysicalObservationInput(
            village_id="v1",
            slope_deg=float("nan"),
        )


def test_invalid_buffer_distance_raises():
    """create_geodesic_buffer rejects non-positive buffer distance."""
    pt = Point(79.567, 30.556)
    with pytest.raises(SpatialGeometryError, match="must be positive"):
        create_geodesic_buffer(pt, buffer_distance_m=-100.0)


def test_invalid_latitude_for_geodesic_buffer():
    """create_geodesic_buffer rejects invalid latitude."""
    pt = Point(79.567, 95.0)
    with pytest.raises(SpatialGeometryError, match="Invalid latitude for buffer"):
        create_geodesic_buffer(pt, buffer_distance_m=500.0)


# =====================================================================
# 18. DangerLevel contract and configuration invariants
# =====================================================================


def test_no_unapproved_danger_level_mappings_across_triggers(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """Engine must NOT invent trigger-based danger level mappings (landslide -> CRITICAL, subsidence -> UNINHABITABLE).

    All candidate permanent red zones must strictly use the profile-configured default_danger_level.
    """
    # 1. Landslide-only trigger
    obs_landslide = GeophysicalObservationInput(
        village_id="vil_ls_only",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=40.0,
        historical_landslide_count=2,
    )
    cand_ls = himalayan_engine.evaluate_village(obs_landslide)
    assert cand_ls.status == RedZoneStatus.PROPOSED
    assert cand_ls.zone_type == RedZoneType.LANDSLIDE_DANGER
    assert cand_ls.danger_level == himalayan_engine.default_danger_level
    assert cand_ls.danger_level != DangerLevel.CRITICAL  # Explicitly proves no invented CRITICAL mapping

    # 2. Subsidence-only trigger
    obs_subsidence = GeophysicalObservationInput(
        village_id="vil_sub_only",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )
    cand_sub = himalayan_engine.evaluate_village(obs_subsidence)
    assert cand_sub.status == RedZoneStatus.PROPOSED
    assert cand_sub.zone_type == RedZoneType.ACTIVE_SUBSIDENCE
    assert cand_sub.danger_level == himalayan_engine.default_danger_level

    # 3. Compound trigger
    obs_compound = GeophysicalObservationInput(
        village_id="vil_comp_only",
        location_geometry=sample_point,
        active_subsidence=True,
        slope_deg=40.0,
        historical_landslide_count=2,
    )
    cand_comp = himalayan_engine.evaluate_village(obs_compound)
    assert cand_comp.status == RedZoneStatus.PROPOSED
    assert cand_comp.zone_type == RedZoneType.COMPOUND_DANGER
    assert cand_comp.danger_level == himalayan_engine.default_danger_level


def test_danger_level_strictly_respects_custom_configured_profile(sample_point: Point):
    """Engine strictly uses whatever default_danger_level is configured on the regional profile."""
    # Build a copy of Himalayan profile with a distinct default_danger_level
    base_profile = get_profile(RegionProfileId.HIMALAYAN_PILOT)
    custom_criteria = base_profile.red_zone_thresholds.permanent_criteria.model_copy(
        update={"default_danger_level": DangerLevel.VERY_HIGH}
    )
    custom_thresholds = base_profile.red_zone_thresholds.model_copy(
        update={"permanent_criteria": custom_criteria}
    )
    custom_profile = base_profile.model_copy(
        update={"red_zone_thresholds": custom_thresholds}
    )

    custom_engine = PermanentRedZoneEngine(profile=custom_profile)
    assert custom_engine.default_danger_level == DangerLevel.VERY_HIGH

    # Evaluate landslide-only village under custom profile
    obs = GeophysicalObservationInput(
        village_id="vil_custom_ls",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=40.0,
        historical_landslide_count=2,
    )
    cand = custom_engine.evaluate_village(obs)
    assert cand.status == RedZoneStatus.PROPOSED
    assert cand.danger_level == DangerLevel.VERY_HIGH  # Matches configured profile value exactly
    assert cand.danger_level != DangerLevel.CRITICAL
    assert cand.danger_level != DangerLevel.UNINHABITABLE


def test_monitor_status_has_no_danger_level_assigned(
    himalayan_engine: PermanentRedZoneEngine, sample_point: Point
):
    """MONITOR status represents non-candidate observation and must not invent a danger level."""
    obs = GeophysicalObservationInput(
        village_id="vil_mon_002",
        location_geometry=sample_point,
        active_subsidence=False,
        slope_deg=38.0,
        historical_landslide_count=1,
        upstream_risk_band=RiskBand.SAFE,
    )
    cand = himalayan_engine.evaluate_village(obs)
    assert cand.status == RedZoneStatus.MONITOR
    assert cand.is_candidate is False
    assert cand.danger_level is None


def test_dissolved_candidates_preserve_configured_danger_level_without_trigger_selection():
    """Dissolved candidates do not invent danger-level aggregation rules based on trigger types."""
    pt1 = Point(79.567, 30.556)
    pt2 = Point(79.567, 30.559)

    engine = PermanentRedZoneEngine()
    obs1 = GeophysicalObservationInput(
        village_id="v_dissolve_1",
        location_geometry=pt1,
        active_subsidence=True,
    )
    obs2 = GeophysicalObservationInput(
        village_id="v_dissolve_2",
        location_geometry=pt2,
        active_subsidence=False,
        slope_deg=40.0,
        historical_landslide_count=2,
    )

    dissolved = engine.demarcate_permanent_red_zones([obs1, obs2], dissolve=True)
    assert len(dissolved) == 1
    # Dissolved zone danger level is strictly the profile configured default
    assert dissolved[0].danger_level == engine.default_danger_level


def test_dissolve_rejects_missing_danger_level_when_neither_source_available():
    """Dissolve utility raises RedZoneConfigError when neither caller nor candidates supply a danger_level.

    Verifies that the dissolve utility NEVER invents a fallback DangerLevel.
    """
    poly1 = box(79.560, 30.550, 79.570, 30.560)
    poly2 = box(79.565, 30.555, 79.575, 30.565)  # Intersects poly1

    audit = TriggerAudit(
        village_id="v1",
        active_subsidence_triggered=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )
    explain = PermanentRedZoneExplainability(
        trigger_summary="Summary",
        trigger_audit=audit,
        trigger_audits=[audit],
        source_village_ids=["v1"],
    )

    # Use model_construct to simulate candidates lacking danger_level
    cand1 = PermanentRedZoneCandidate.model_construct(
        candidate_id="c1",
        zone_id="c1",
        name="Candidate 1",
        status=RedZoneStatus.PROPOSED,
        danger_level=None,
        geometry=normalize_to_multipolygon(poly1),
        explainability=explain,
        contributing_village_ids=["v1"],
    )
    cand2 = PermanentRedZoneCandidate.model_construct(
        candidate_id="c2",
        zone_id="c2",
        name="Candidate 2",
        status=RedZoneStatus.PROPOSED,
        danger_level=None,
        geometry=normalize_to_multipolygon(poly2),
        explainability=explain,
        contributing_village_ids=["v2"],
    )

    # Calling dissolve without default_danger_level must raise RedZoneConfigError, not silently choose UNINHABITABLE
    with pytest.raises(RedZoneConfigError, match="neither default_danger_level nor an existing candidate danger_level was provided"):
        dissolve_overlapping_candidates([cand1, cand2], default_danger_level=None)


def test_dissolve_single_candidate_rejects_missing_danger_level_when_neither_source_available():
    """Single candidate normalization in dissolve raises RedZoneConfigError if danger_level is completely missing."""
    poly = box(79.560, 30.550, 79.570, 30.560)
    audit = TriggerAudit(
        village_id="v_single",
        active_subsidence_triggered=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )
    explain = PermanentRedZoneExplainability(
        trigger_summary="Single Summary",
        trigger_audit=audit,
        trigger_audits=[audit],
        source_village_ids=["v_single"],
    )
    cand = PermanentRedZoneCandidate.model_construct(
        candidate_id="c_single",
        zone_id="c_single",
        name="Single Candidate",
        status=RedZoneStatus.PROPOSED,
        danger_level=None,
        geometry=normalize_to_multipolygon(poly),
        explainability=explain,
        contributing_village_ids=["v_single"],
    )

    with pytest.raises(RedZoneConfigError, match="neither default_danger_level nor an existing candidate danger_level was provided"):
        dissolve_overlapping_candidates([cand], default_danger_level=None)


def test_dissolve_adheres_to_strict_resolution_order():
    """Dissolve adheres to resolution order: explicit default_danger_level > candidate danger_level."""
    poly1 = box(79.560, 30.550, 79.570, 30.560)
    poly2 = box(79.565, 30.555, 79.575, 30.565)

    audit = TriggerAudit(
        village_id="v1",
        active_subsidence_triggered=True,
        slope_deg=20.0,
        historical_landslide_count=0,
    )
    explain = PermanentRedZoneExplainability(
        trigger_summary="Summary",
        trigger_audit=audit,
        trigger_audits=[audit],
        source_village_ids=["v1"],
    )

    cand1 = PermanentRedZoneCandidate(
        candidate_id="c1",
        status=RedZoneStatus.PROPOSED,
        zone_type=RedZoneType.ACTIVE_SUBSIDENCE,
        danger_level=DangerLevel.VERY_HIGH,
        geometry=normalize_to_multipolygon(poly1),
        explainability=explain,
        contributing_village_ids=["v1"],
        is_candidate=True,
    )
    cand2 = PermanentRedZoneCandidate(
        candidate_id="c2",
        status=RedZoneStatus.PROPOSED,
        zone_type=RedZoneType.ACTIVE_SUBSIDENCE,
        danger_level=DangerLevel.VERY_HIGH,
        geometry=normalize_to_multipolygon(poly2),
        explainability=explain,
        contributing_village_ids=["v2"],
        is_candidate=True,
    )

    # 1. When default_danger_level is None, existing candidate danger_level is used
    dissolved_from_candidate = dissolve_overlapping_candidates([cand1, cand2], default_danger_level=None)
    assert len(dissolved_from_candidate) == 1
    assert dissolved_from_candidate[0].danger_level == DangerLevel.VERY_HIGH

    # 2. When explicit default_danger_level is supplied, caller specification takes precedence
    dissolved_with_explicit = dissolve_overlapping_candidates([cand1, cand2], default_danger_level=DangerLevel.CRITICAL)
    assert len(dissolved_with_explicit) == 1
    assert dissolved_with_explicit[0].danger_level == DangerLevel.CRITICAL
