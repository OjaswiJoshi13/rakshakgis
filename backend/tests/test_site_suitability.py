"""Automated unit and integration tests for Multi-Criteria Site Suitability Engine (Chunk M4-02)."""

import math
from unittest.mock import MagicMock
import pytest

from app.core.database import get_db
from app.core.profiles.himalayan import HIMALAYAN_PILOT_PROFILE
from app.core.relocation.suitability import (
    CriterionType,
    HardConstraintType,
    InvalidSiteDataError,
    SiteSuitabilityEngine,
    SiteSuitabilityInput,
    SuitabilityConfigError,
    SuitabilityDecision,
    SuitabilityThresholdsConfig,
    SuitabilityWeightsConfig,
)
from app.data.synthetic.loader import get_synthetic_candidate_sites_geojson
from app.main import app
from app.models.relocation import CandidateSite, Infrastructure, SiteCapacity
from app.schemas.sites import GeoJSONPoint, GeoJSONPolygon


# ==============================================================================
# Helper Factories
# ==============================================================================


def create_sample_suitable_site(
    site_id="SITE-GOOD-01",
    name="Safe Plateau Site",
    slope=6.0,
    buffer_m=1000.0,
    households=120,
    water_lpd=80.0,
    road_width=6.0,
    dist_hw=1.0,
    all_weather=True,
    dist_health=1.5,
    dist_school=1.0,
    dist_emergency=3.0,
    livelihood="high",
    expansion="high",
) -> SiteSuitabilityInput:
    """Helper to build a robust candidate site input with optimal parameters."""
    return SiteSuitabilityInput(
        site_id=site_id,
        name=name,
        terrain_slope_deg=slope,
        hazard_buffer_distance_m=buffer_m,
        soil_stability="consolidated_alluvium",
        elevation_m=1200.0,
        area_sq_m=50000.0,
        max_households=households,
        max_population=households * 4,
        available_households=households,
        available_population=households * 4,
        sanitation_units=30,
        road_width_m=road_width,
        distance_to_highway_km=dist_hw,
        all_weather_access=all_weather,
        water_supply_lpd_per_capita=water_lpd,
        water_source_distance_m=300.0,
        perennial_water_source=True,
        distance_to_health_center_km=dist_health,
        has_on_site_health_center=False,
        distance_to_school_km=dist_school,
        distance_to_emergency_km=dist_emergency,
        has_on_site_helipad_or_shelter=False,
        livelihood_potential=livelihood,
        distance_to_farmland_km=0.5,
        distance_to_market_km=1.5,
        expansion_potential=expansion,
    )


# ==============================================================================
# 1. Fully Suitable Site Tests
# ==============================================================================


def test_fully_suitable_site_passes_all_checks():
    """Test 1: Fully suitable site passes all hard constraints with high score and SUITABLE decision."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()

    result = engine.evaluate(site)

    assert result.is_eligible is True
    assert result.decision == SuitabilityDecision.SUITABLE
    assert result.overall_score >= 70.0
    assert len(result.failed_constraints) == 0
    assert all(c.passed for c in result.hard_constraints)
    assert len(result.criteria_scores) == 9


# ==============================================================================
# 2. Hard Constraint Hazard Safety Failure Tests
# ==============================================================================


def test_site_failing_hazard_slope_constraint():
    """Test 2a: Site failing slope safety threshold (e.g. 19.5 deg > 15.0 deg) is disqualified."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site(slope=19.5)

    result = engine.evaluate(site)

    assert result.is_eligible is False
    assert result.decision == SuitabilityDecision.INELIGIBLE
    assert "Terrain Slope Safety" in result.failed_constraints
    assert any("exceeds maximum safe limit" in r for r in result.summary_reasons)


def test_site_failing_hazard_buffer_constraint():
    """Test 2b: Site inside mandatory hazard buffer (e.g. 220m < 500m) is disqualified."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site(buffer_m=220.0)

    result = engine.evaluate(site)

    assert result.is_eligible is False
    assert result.decision == SuitabilityDecision.INELIGIBLE
    assert "Hazard Exclusion Buffer" in result.failed_constraints
    assert any("mandatory hazard exclusion buffer" in r for r in result.summary_reasons)


# ==============================================================================
# 3. Hard Constraint Usable Capacity Failure Tests
# ==============================================================================


def test_site_failing_zero_capacity():
    """Test 3a: Site with zero available/max households fails capacity hard constraint."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site(households=0)

    result = engine.evaluate(site)

    assert result.is_eligible is False
    assert result.decision == SuitabilityDecision.INELIGIBLE
    assert "Known Usable Capacity" in result.failed_constraints
    assert any("household capacity is 0" in r for r in result.summary_reasons)


def test_site_failing_missing_capacity():
    """Test 3b: Site with missing capacity (None) must not be treated as unlimited."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()
    site.available_households = None
    site.max_households = None

    result = engine.evaluate(site)

    assert result.is_eligible is False
    assert result.decision == SuitabilityDecision.INELIGIBLE
    assert "Known Usable Capacity" in result.failed_constraints
    assert any("Capacity data is missing/unknown" in r for r in result.summary_reasons)


# ==============================================================================
# 4. Invariant: Strong Weighted Scores Cannot Override Hard Failure
# ==============================================================================


def test_strong_weighted_scores_cannot_override_hard_constraint():
    """Test 4: Site with perfect infrastructure scores but failing slope constraint remains INELIGIBLE."""
    engine = SiteSuitabilityEngine()
    # Perfect road, water, health, school, emergency, livelihood, expansion, capacity, BUT slope=22.0
    site = create_sample_suitable_site(
        slope=22.0,  # Hard failure!
        buffer_m=2000.0,
        households=300,
        water_lpd=100.0,
        road_width=10.0,
        dist_hw=0.1,
        dist_health=0.2,
        dist_school=0.2,
        dist_emergency=0.5,
        livelihood="high",
        expansion="high",
    )
    site.has_on_site_health_center = True
    site.has_on_site_helipad_or_shelter = True

    result = engine.evaluate(site)

    # Invariant check
    assert result.is_eligible is False
    assert result.decision == SuitabilityDecision.INELIGIBLE
    assert "Terrain Slope Safety" in result.failed_constraints
    # Even if weighted score is calculated for audit transparency:
    assert result.overall_score > 0.0
    assert any("cannot override hard safety/capacity limits" in r for r in result.summary_reasons)


# ==============================================================================
# 5. Weighted-Score Calculation & Weights Validation
# ==============================================================================


def test_weights_sum_to_one_validation():
    """Test 5a: Configured weights must sum strictly to 1.0 (100%)."""
    weights = SuitabilityWeightsConfig()
    assert math.isclose(
        (
            weights.hazard_safety
            + weights.capacity
            + weights.road_access
            + weights.water_availability
            + weights.healthcare_access
            + weights.school_access
            + weights.emergency_services
            + weights.livelihood_access
            + weights.expansion_potential
        ),
        1.0,
    )

    # Invalid weights sum raises SuitabilityConfigError
    with pytest.raises(SuitabilityConfigError):
        SuitabilityWeightsConfig(hazard_safety=0.50, capacity=0.20)  # sums to < 1.0


def test_weighted_contribution_calculation_exactness():
    """Test 5b: Sum of weighted contributions equals overall score within rounding tolerance."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()

    result = engine.evaluate(site)

    sum_contributions = sum(c.weighted_contribution for c in result.criteria_scores.values())
    assert math.isclose(result.overall_score, sum_contributions, abs_tol=0.2)


# ==============================================================================
# 6. Criterion-Level Output Verification (All 9 Criteria)
# ==============================================================================


def test_all_nine_criteria_present_with_contributions():
    """Test 6: Result contains all 9 distinct criteria with weights, scores, and contributions."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()

    result = engine.evaluate(site)

    expected_criteria = {
        CriterionType.HAZARD_SAFETY.value: 0.30,
        CriterionType.CAPACITY.value: 0.20,
        CriterionType.ROAD_ACCESS.value: 0.10,
        CriterionType.WATER_AVAILABILITY.value: 0.10,
        CriterionType.HEALTHCARE_ACCESS.value: 0.10,
        CriterionType.SCHOOL_ACCESS.value: 0.05,
        CriterionType.EMERGENCY_SERVICES.value: 0.05,
        CriterionType.LIVELIHOOD_ACCESS.value: 0.05,
        CriterionType.EXPANSION_POTENTIAL.value: 0.05,
    }

    assert set(result.criteria_scores.keys()) == set(expected_criteria.keys())

    for crit_key, expected_w in expected_criteria.items():
        crit_res = result.criteria_scores[crit_key]
        assert crit_res.weight == expected_w
        assert 0.0 <= crit_res.raw_score <= 100.0
        assert math.isclose(
            crit_res.weighted_contribution,
            round(crit_res.raw_score * crit_res.weight, 2),
            abs_tol=0.05,
        )


# ==============================================================================
# 7. Boundary Values for Scoring
# ==============================================================================


def test_scoring_boundary_values():
    """Test 7: Boundary values (slope 0 deg, slope 15 deg, distance 0 km, large distances)."""
    engine = SiteSuitabilityEngine()

    # Slope at 0.0 deg (flat river terrace)
    flat_site = create_sample_suitable_site(slope=0.0)
    flat_res = engine.evaluate(flat_site)
    assert flat_res.criteria_scores[CriterionType.HAZARD_SAFETY.value].raw_score >= 85.0

    # Slope exactly at 15.0 deg boundary
    boundary_site = create_sample_suitable_site(slope=15.0)
    boundary_res = engine.evaluate(boundary_site)
    assert boundary_res.is_eligible is True
    # At 15 deg, slope score drops to ~50
    assert boundary_res.criteria_scores[CriterionType.HAZARD_SAFETY.value].raw_score < flat_res.criteria_scores[CriterionType.HAZARD_SAFETY.value].raw_score

    # Extremely far distances
    far_site = create_sample_suitable_site(dist_health=25.0, dist_school=20.0, dist_emergency=30.0)
    far_res = engine.evaluate(far_site)
    assert far_res.criteria_scores[CriterionType.HEALTHCARE_ACCESS.value].raw_score == 0.0
    assert far_res.criteria_scores[CriterionType.SCHOOL_ACCESS.value].raw_score == 0.0
    assert far_res.criteria_scores[CriterionType.EMERGENCY_SERVICES.value].raw_score == 0.0


# ==============================================================================
# 8. Capacity Bottleneck / Constrained Classification
# ==============================================================================


def test_capacity_bottleneck_yields_constrained():
    """Test 8: Site with high suitability but insufficient community capacity (<20 hh) is CONSTRAINED."""
    engine = SiteSuitabilityEngine()
    # 15 households is below min_viable_households (20)
    site = create_sample_suitable_site(households=15)

    result = engine.evaluate(site)

    assert result.is_eligible is True
    assert result.decision == SuitabilityDecision.CONSTRAINED
    assert any("below standard community transfer threshold" in r for r in result.summary_reasons)


# ==============================================================================
# 9. Invalid Data Rejection
# ==============================================================================


def test_invalid_data_nan_or_inf_rejected():
    """Test 9: Passing NaN or infinite values to scoring functions raises InvalidSiteDataError."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()
    site.terrain_slope_deg = float("nan")

    with pytest.raises(InvalidSiteDataError):
        engine.evaluate(site)

    site_inf = create_sample_suitable_site()
    site_inf.hazard_buffer_distance_m = float("inf")

    with pytest.raises(InvalidSiteDataError):
        engine.evaluate(site_inf)


# ==============================================================================
# 10. Deterministic Repeated Evaluation
# ==============================================================================


def test_strict_evaluation_determinism():
    """Test 10: Repeated evaluation of identical inputs produces identical results."""
    engine = SiteSuitabilityEngine()
    site = create_sample_suitable_site()

    res1 = engine.evaluate(site)
    res2 = engine.evaluate(site)

    assert res1.overall_score == res2.overall_score
    assert res1.decision == res2.decision
    assert res1.is_eligible == res2.is_eligible
    assert res1.failed_constraints == res2.failed_constraints
    assert len(res1.criteria_scores) == len(res2.criteria_scores)

    for k in res1.criteria_scores:
        assert res1.criteria_scores[k].raw_score == res2.criteria_scores[k].raw_score
        assert res1.criteria_scores[k].weighted_contribution == res2.criteria_scores[k].weighted_contribution


# ==============================================================================
# 11. Full Evaluation of 12 Synthetic Candidate Sites
# ==============================================================================


def test_evaluation_of_all_twelve_synthetic_sites():
    """Test 11: Evaluate the complete synthetic candidate sites collection from fixtures.

    Verifies expected categorizations:
      - HIM-SITE-001 to HIM-SITE-007: SUITABLE / Eligible
      - HIM-SITE-008: Slope violation (19.5 deg) -> INELIGIBLE
      - HIM-SITE-009: Severe slope (24.0 deg) -> INELIGIBLE
      - HIM-SITE-010: Buffer violation (220m) -> INELIGIBLE
      - HIM-SITE-011: Water deficit (35 LPD) -> INELIGIBLE / Low score
      - HIM-SITE-012: Capacity bottleneck (18 hh) -> CONSTRAINED
    """
    engine = SiteSuitabilityEngine.from_region_profile(HIMALAYAN_PILOT_PROFILE)
    sites_geojson = get_synthetic_candidate_sites_geojson()
    features = sites_geojson["features"]

    assert len(features) == 12

    evaluations_by_id = {}
    for feat in features:
        site_in = SiteSuitabilityInput.from_synthetic_feature(feat)
        res = engine.evaluate(site_in)
        evaluations_by_id[site_in.site_id] = res

    # 1-7: Suitable
    for i in range(1, 8):
        s_id = f"HIM-SITE-{i:03d}"
        res = evaluations_by_id[s_id]
        assert res.is_eligible is True, f"{s_id} should be eligible"
        assert res.decision == SuitabilityDecision.SUITABLE, f"{s_id} should be SUITABLE"
        assert res.overall_score >= 65.0, f"{s_id} score {res.overall_score} should be >= 65.0"

    # 8: Slope violation
    res_8 = evaluations_by_id["HIM-SITE-008"]
    assert res_8.is_eligible is False
    assert res_8.decision == SuitabilityDecision.INELIGIBLE
    assert "Terrain Slope Safety" in res_8.failed_constraints

    # 9: Severe slope
    res_9 = evaluations_by_id["HIM-SITE-009"]
    assert res_9.is_eligible is False
    assert res_9.decision == SuitabilityDecision.INELIGIBLE
    assert "Terrain Slope Safety" in res_9.failed_constraints

    # 10: Hazard buffer violation
    res_10 = evaluations_by_id["HIM-SITE-010"]
    assert res_10.is_eligible is False
    assert res_10.decision == SuitabilityDecision.INELIGIBLE
    assert "Hazard Exclusion Buffer" in res_10.failed_constraints

    # 11: Water deficit (35 LPD) - passes hard constraints, but water score is severely depressed
    res_11 = evaluations_by_id["HIM-SITE-011"]
    assert res_11.is_eligible is True
    assert len(res_11.failed_constraints) == 0
    assert res_11.criteria_scores["water_availability"].raw_score < 30.0
    assert res_11.criteria_scores["water_availability"].weighted_contribution < 3.0
    assert res_11.decision == SuitabilityDecision.CONSTRAINED

    # 12: Capacity bottleneck (18 hh)
    res_12 = evaluations_by_id["HIM-SITE-012"]
    assert res_12.is_eligible is True
    assert res_12.decision == SuitabilityDecision.CONSTRAINED



# ==============================================================================
# 12. API Endpoint Integration Tests
# ==============================================================================


@pytest.fixture
def mock_db():
    """Provide a mocked database session."""
    return MagicMock()


def make_mock_db_site(site_id=42, name="Valley Ridge Site"):
    """Helper to mock CandidateSite model with capacities and infrastructures."""
    site = CandidateSite(
        id=site_id,
        name=name,
        district_id=1,
        location=GeoJSONPoint(type="Point", coordinates=(78.1, 30.1)),
        boundary=GeoJSONPolygon(
            type="Polygon",
            coordinates=[[[78.1, 30.1], [78.11, 30.1], [78.11, 30.11], [78.1, 30.11], [78.1, 30.1]]],
        ),
        area_sq_m=45000.0,
        terrain_slope_deg=7.0,
        elevation_m=1100.0,
        status="proposed",
    )
    site.capacities = [
        SiteCapacity(
            id=1,
            site_id=site_id,
            max_households=100,
            max_population=450,
            available_households=100,
            available_population=450,
            water_supply_lpd=35000.0,
            sanitation_units=25,
        )
    ]
    site.infrastructures = [
        Infrastructure(
            id=1,
            site_id=site_id,
            name="Emergency Helipad",
            infra_type="helipad",
            status="operational",
            location=GeoJSONPoint(type="Point", coordinates=(78.105, 30.105)),
        )
    ]
    return site


def test_api_evaluate_payload_endpoint(client):
    """Test POST /api/v1/sites/evaluate directly evaluates input payload."""
    payload = {
        "name": "Ad-Hoc Pilot Site",
        "terrain_slope_deg": 6.5,
        "hazard_buffer_distance_m": 1100.0,
        "area_sq_m": 50000.0,
        "max_households": 110,
        "available_households": 110,
        "road_width_m": 5.5,
        "distance_to_highway_km": 1.0,
        "all_weather_access": True,
        "water_supply_lpd_per_capita": 80.0,
        "distance_to_health_center_km": 2.0,
        "distance_to_school_km": 1.0,
        "distance_to_emergency_km": 3.0,
        "livelihood_potential": "high",
        "expansion_potential": "moderate",
    }
    response = client.post("/api/v1/sites/evaluate", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["site_name"] == "Ad-Hoc Pilot Site"
    assert data["is_eligible"] is True
    assert data["decision"] == "suitable"
    assert data["overall_score"] >= 65.0
    assert len(data["criteria_scores"]) == 9


def test_api_evaluate_site_by_id_endpoint(client, mock_db):
    """Test POST /api/v1/sites/{id}/evaluate evaluates database site and loads relationships."""
    site = make_mock_db_site(42, "Valley Ridge Site")
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = site
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/sites/42/evaluate", json={"persist_score": True})
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        data = res["data"]
        assert data["site_id"] == 42
        assert data["is_eligible"] is True
        assert len(data["criteria_scores"]) == 9
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_get_site_suitability_by_id_endpoint(client, mock_db):
    """Test GET /api/v1/sites/{id}/suitability retrieves evaluation for database site."""
    site = make_mock_db_site(99, "Hillside Safety Haven")
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = site
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sites/99/suitability")
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        data = res["data"]
        assert data["site_id"] == 99
        assert data["is_eligible"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_evaluate_site_by_id_not_found(client, mock_db):
    """Test POST /api/v1/sites/{id}/evaluate returns 404 when site does not exist."""
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/sites/9999/evaluate")
        assert response.status_code == 404
        res = response.json()
        assert res["success"] is False
        assert res["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_low_water_is_weighted_criterion_not_hard_constraint():
    """Test that low water supply affects weighted scoring without acting as an unconfigured hard exclusion gate."""
    engine = SiteSuitabilityEngine()

    # Site with low water (25 LPD) but safe slope (5 deg) and positive capacity (100 hh)
    site_low_water = create_sample_suitable_site(water_lpd=25.0)
    res_water = engine.evaluate(site_low_water)

    # All hard constraints pass: site is NOT marked INELIGIBLE
    assert res_water.is_eligible is True
    assert res_water.decision in (SuitabilityDecision.SUITABLE, SuitabilityDecision.CONSTRAINED)
    assert len(res_water.failed_constraints) == 0
    # Water score is significantly reduced (below 50.0 compared to >90.0 for good water)
    normal_site = create_sample_suitable_site(water_lpd=85.0)
    res_normal = engine.evaluate(normal_site)
    assert res_water.criteria_scores[CriterionType.WATER_AVAILABILITY.value].raw_score < 50.0
    assert res_water.criteria_scores[CriterionType.WATER_AVAILABILITY.value].raw_score < res_normal.criteria_scores[CriterionType.WATER_AVAILABILITY.value].raw_score - 40.0


    # In contrast, an actual hard constraint failure (slope > 15 deg) strictly marks INELIGIBLE
    site_bad_slope = create_sample_suitable_site(slope=18.0)
    res_slope = engine.evaluate(site_bad_slope)
    assert res_slope.is_eligible is False
    assert res_slope.decision == SuitabilityDecision.INELIGIBLE
    assert "Terrain Slope Safety" in res_slope.failed_constraints


def test_api_evaluate_invalid_region_profile_returns_structured_error(client, mock_db):
    """Test that requesting an invalid region profile returns structured HTTP 404 UNKNOWN_REGION_PROFILE without silent fallback."""
    payload = {
        "name": "Test Site",
        "terrain_slope_deg": 5.0,
        "max_households": 100,
    }
    # 1. Direct evaluate payload endpoint
    resp1 = client.post("/api/v1/sites/evaluate?region_profile_id=invalid_profile_name", json=payload)
    assert resp1.status_code == 404
    body1 = resp1.json()
    assert body1["success"] is False
    assert body1["error"]["code"] == "UNKNOWN_REGION_PROFILE"

    # 2. Evaluate DB site endpoint
    site = make_mock_db_site(50, "Test DB Site")
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = site
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp2 = client.post("/api/v1/sites/50/evaluate", json={"region_profile_id": "invalid_profile_name"})
        assert resp2.status_code == 404
        body2 = resp2.json()
        assert body2["success"] is False
        assert body2["error"]["code"] == "UNKNOWN_REGION_PROFILE"

        # 3. GET suitability endpoint
        resp3 = client.get("/api/v1/sites/50/suitability?region_profile_id=invalid_profile_name")
        assert resp3.status_code == 404
        body3 = resp3.json()
        assert body3["success"] is False
        assert body3["error"]["code"] == "UNKNOWN_REGION_PROFILE"
    finally:
        app.dependency_overrides.pop(get_db, None)
