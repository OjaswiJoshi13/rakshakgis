"""Focused automated tests for Chunk M4-03: Carrying Capacity & Infrastructure Sizing."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db
from app.core.relocation.capacity import (
    CapacityPlanningConfig,
    CarryingCapacityEngine,
    InfrastructureDimension,
    InvalidCapacityDataError,
    SiteCapacityInput,
)
from app.core.relocation.suitability import (
    SiteSuitabilityEngine,
    SiteSuitabilityInput,
    SuitabilityDecision,
)
from app.data.synthetic.loader import load_himalayan_pilot_dataset
from app.models.geographic import District
from app.models.relocation import CandidateSite, SiteCapacity, Infrastructure


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    session = MagicMock()
    return session


def create_sample_capacity_input(
    incoming_hh: int = 50,
    current_occ: int = 0,
    housing: int = 100,
    water: int = 80,
    sanitation: int = 90,
    healthcare: int = 120,
    shelter: int = 110,
    household_size: float = 4.17,
) -> SiteCapacityInput:
    """Helper to construct a valid SiteCapacityInput with all 5 critical dimensions populated."""
    return SiteCapacityInput(
        site_id="TEST-SITE-001",
        site_name="Test Relocation Site",
        incoming_households=incoming_hh,
        current_occupancy_households=current_occ,
        household_size=household_size,
        housing_capacity=housing,
        water_capacity=water,
        sanitation_capacity=sanitation,
        healthcare_capacity=healthcare,
        shelter_capacity=shelter,
    )


# ==============================================================================
# 1. CORE CAPACITY RULE: MIN(housing, water, sanitation, healthcare, shelter)
# ==============================================================================

def test_effective_capacity_is_min_of_five_critical_dimensions():
    """Test 1: Effective capacity is strictly the MIN of housing, water, sanitation, healthcare, and shelter."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        housing=100,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 80
    assert result.limiting_factors == ["water"]
    assert result.available_capacity_households == 80
    assert result.capacity_margin_households == 30  # 80 - 50
    assert result.feasible is True


# ==============================================================================
# 2. LIMITING FACTOR IDENTIFICATION
# ==============================================================================

def test_water_is_limiting_factor_when_water_capacity_is_smallest():
    """Test 2: Water is reported as the limiting factor when water capacity is smallest."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        housing=150,
        water=45,
        sanitation=100,
        healthcare=120,
        shelter=110,
    )
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 45
    assert result.limiting_factors == ["water"]


def test_housing_is_limiting_factor_when_housing_is_smallest():
    """Test 3: Housing is reported as the limiting factor when housing capacity is smallest."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        housing=35,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 35
    assert result.limiting_factors == ["housing"]


def test_multiple_tied_limiting_factors_reported_deterministically():
    """Test 4: Multiple tied limiting factors are all reported deterministically and sorted alphabetically."""
    engine = CarryingCapacityEngine()

    # Tie between housing and water (both 75)
    site_input = create_sample_capacity_input(
        housing=75,
        water=75,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 75
    assert result.limiting_factors == ["housing", "water"]

    # All 5 dimensions tied at 60
    site_all_tied = create_sample_capacity_input(
        housing=60,
        water=60,
        sanitation=60,
        healthcare=60,
        shelter=60,
    )
    res_all_tied = engine.evaluate(site_all_tied)

    assert res_all_tied.effective_capacity_households == 60
    assert res_all_tied.limiting_factors == [
        "healthcare",
        "housing",
        "sanitation",
        "shelter",
        "water",
    ]


# ==============================================================================
# 3. CAPACITY MARGIN AND FEASIBILITY
# ==============================================================================

def test_incoming_households_exactly_equal_available_capacity():
    """Test 5: When incoming households exactly equal available capacity, feasible=True and margin=0."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        incoming_hh=80,
        current_occ=0,
        housing=100,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 80
    assert result.available_capacity_households == 80
    assert result.capacity_margin_households == 0
    assert result.remaining_capacity_households == 0
    assert result.feasible is True


def test_incoming_households_exceed_available_capacity_preserves_negative_margin():
    """Test 6: When incoming households exceed available capacity, feasible=False and negative margin is preserved."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        incoming_hh=105,
        current_occ=10,
        housing=100,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    # effective = 80, current_occ = 10 -> available = 70. incoming = 105 -> margin = -35
    result = engine.evaluate(site_input)

    assert result.effective_capacity_households == 80
    assert result.available_capacity_households == 70
    assert result.capacity_margin_households == -35
    assert result.remaining_capacity_households == -35
    assert result.feasible is False
    assert any("deficit of 35 households" in r for r in result.reasons)


def test_zero_available_capacity_infeasible():
    """Test 7: Zero available capacity is classified as infeasible."""
    engine = CarryingCapacityEngine()

    # Site with capacity fully occupied
    site_fully_occupied = create_sample_capacity_input(
        incoming_hh=0,
        current_occ=80,
        housing=100,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    res1 = engine.evaluate(site_fully_occupied)
    assert res1.available_capacity_households == 0
    assert res1.feasible is False

    # Site with zero total effective capacity
    site_zero_cap = create_sample_capacity_input(
        incoming_hh=10,
        current_occ=0,
        housing=0,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )
    res2 = engine.evaluate(site_zero_cap)
    assert res2.effective_capacity_households == 0
    assert res2.available_capacity_households == 0
    assert res2.capacity_margin_households == -10
    assert res2.feasible is False


# ==============================================================================
# 4. UNKNOWN DATA SAFETY
# ==============================================================================

def test_missing_unknown_critical_capacity_never_treated_as_unlimited():
    """Test 8: Unknown/missing critical capacity is NEVER treated as unlimited; yields indeterminate/infeasible result."""
    engine = CarryingCapacityEngine()

    # Shelter capacity is None (missing/unknown)
    site_missing_shelter = SiteCapacityInput(
        site_id="TEST-UNKNOWN-001",
        site_name="Unknown Shelter Site",
        incoming_households=50,
        housing_capacity=100,
        water_capacity=80,
        sanitation_capacity=90,
        healthcare_capacity=120,
        shelter_capacity=None,
    )
    result = engine.evaluate(site_missing_shelter)

    assert result.effective_capacity_households is None
    assert result.available_capacity_households is None
    assert result.capacity_margin_households is None
    assert result.feasible is False
    assert result.unknown_dimensions == ["shelter"]
    assert any("unknown or missing" in r for r in result.reasons)


# ==============================================================================
# 5. INPUT DATA VALIDATION
# ==============================================================================

def test_negative_capacity_rejected():
    """Test 9: Negative capacity is rejected with InvalidCapacityDataError."""
    with pytest.raises(InvalidCapacityDataError):
        SiteCapacityInput(
            site_name="Invalid Negative Capacity Site",
            incoming_households=50,
            housing_capacity=-10,
        )


def test_negative_incoming_households_rejected():
    """Test 10: Negative incoming households is rejected."""
    with pytest.raises(InvalidCapacityDataError):
        SiteCapacityInput(
            site_name="Invalid Negative Demand Site",
            incoming_households=-25,
            housing_capacity=100,
        )


def test_nan_and_infinity_rejected():
    """Test 11: NaN and Infinity are rejected across all numerical inputs."""
    with pytest.raises(InvalidCapacityDataError):
        SiteCapacityInput(
            site_name="NaN Capacity Site",
            incoming_households=50,
            water_capacity=float("nan"),
        )

    with pytest.raises(InvalidCapacityDataError):
        SiteCapacityInput(
            site_name="Inf Capacity Site",
            incoming_households=50,
            water_capacity=float("inf"),
        )


# ==============================================================================
# 6. REPEATED DETERMINISM
# ==============================================================================

def test_deterministic_repeated_evaluation():
    """Test 12: Repeated evaluation of identical inputs produces identical results."""
    engine = CarryingCapacityEngine()
    site_input = create_sample_capacity_input(
        incoming_hh=65,
        housing=100,
        water=80,
        sanitation=90,
        healthcare=120,
        shelter=110,
    )

    baseline = engine.evaluate(site_input)
    for _ in range(50):
        res = engine.evaluate(site_input)
        assert res.effective_capacity_households == baseline.effective_capacity_households
        assert res.available_capacity_households == baseline.available_capacity_households
        assert res.capacity_margin_households == baseline.capacity_margin_households
        assert res.limiting_factors == baseline.limiting_factors
        assert res.feasible == baseline.feasible
        assert res.reasons == baseline.reasons


# ==============================================================================
# 7. INFRASTRUCTURE SIZING AND DEFICIT CALCULATIONS
# ==============================================================================

def test_infrastructure_sizing_and_deficit_calculations():
    """Test 13: Infrastructure demand, existing capacity, and deficits are correctly calculated in physical units."""
    config = CapacityPlanningConfig(
        water_supply_lpd_per_capita=70.0,
        land_area_sq_m_per_household=120.0,
        persons_per_household=4.0,
        households_per_sanitation_unit=4.0,
    )
    engine = CarryingCapacityEngine(config)

    # 100 incoming households; water capacity only 75 households
    site_input = SiteCapacityInput(
        site_id="TEST-INFRA-001",
        site_name="Infra Sizing Test Site",
        incoming_households=100,
        housing_capacity=150,
        water_capacity=75,
        sanitation_capacity=120,
        healthcare_capacity=150,
        shelter_capacity=150,
        household_size=4.0,
    )
    result = engine.evaluate(site_input)

    assert result.feasible is False
    assert result.limiting_factors == ["water"]
    assert result.capacity_margin_households == -25  # 75 - 100
    assert result.deficits == {"water": 25}

    # Verify physical water demand: 100 hh * 4 persons * 70 LPD = 28,000 LPD
    water_res = result.infrastructure_results["water"]
    assert water_res.demand_physical_quantity == 28000.0
    # Existing water: 75 hh * 4 * 70 = 21,000 LPD
    assert water_res.existing_physical_quantity == 21000.0
    assert water_res.deficit_or_surplus_physical == -7000.0
    assert water_res.is_feasible is False

    # Verify sanitation: 100 hh / 4 = 25 units demand; 120 hh / 4 = 30 units existing
    san_res = result.infrastructure_results["sanitation"]
    assert san_res.demand_physical_quantity == 25.0
    assert san_res.existing_physical_quantity == 30.0
    assert san_res.deficit_or_surplus_physical == +5.0
    assert san_res.is_feasible is True


# ==============================================================================
# 8. RELATIONSHIP TO M4-02: SUITABILITY VS CARRYING CAPACITY
# ==============================================================================

def test_high_suitability_score_does_not_override_insufficient_capacity():
    """Test 14: A site with very high suitability score (M4-02) cannot override insufficient carrying capacity (M4-03)."""
    suitability_engine = SiteSuitabilityEngine()
    capacity_engine = CarryingCapacityEngine()

    # M4-02 Suitability Evaluation (Topographic safety, access, livelihood are ideal)
    suit_input = SiteSuitabilityInput(
        site_id="SITE-HIGH-SUIT-001",
        name="High Suitability Flat Plateau",
        terrain_slope_deg=4.5,
        hazard_buffer_distance_m=1200.0,
        max_households=40,  # Small physical capacity
        available_households=40,
        road_width_m=6.0,
        distance_to_highway_km=0.5,
        all_weather_access=True,
        water_supply_lpd_per_capita=85.0,
        perennial_water_source=True,
        distance_to_health_center_km=1.0,
        distance_to_school_km=1.0,
        distance_to_emergency_km=2.0,
        livelihood_potential="high",
        expansion_potential="high",
    )
    suit_res = suitability_engine.evaluate(suit_input)
    assert suit_res.is_eligible is True
    assert suit_res.overall_score >= 80.0
    assert suit_res.decision in (SuitabilityDecision.SUITABLE, SuitabilityDecision.CONSTRAINED)

    # M4-03 Carrying Capacity Evaluation for relocation demand of 100 households
    cap_input = SiteCapacityInput(
        site_id="SITE-HIGH-SUIT-001",
        site_name="High Suitability Flat Plateau",
        incoming_households=100,  # Demand exceeds the 40 hh capacity
        housing_capacity=40,
        water_capacity=40,
        sanitation_capacity=40,
        healthcare_capacity=100,
        shelter_capacity=100,
    )
    cap_res = capacity_engine.evaluate(cap_input)

    assert cap_res.effective_capacity_households == 40
    assert cap_res.capacity_margin_households == -60  # Deficit of 60 households
    assert cap_res.feasible is False  # High suitability CANNOT override capacity deficit!


# ==============================================================================
# 9. SYNTHETIC FIXTURE EXERCISE
# ==============================================================================

def test_evaluation_of_synthetic_candidate_sites():
    """Test 15: Exercise M4-03 carrying capacity engine on synthetic candidate sites."""
    dataset = load_himalayan_pilot_dataset()
    sites = dataset.candidate_sites.features
    assert len(sites) == 12
    engine = CarryingCapacityEngine()

    # Test Site 1 (HIM-SITE-001): Gauchar Aerodrome Terrace Flat (180 households capacity)
    site_1 = sites[0]
    # Synthetic sites don't have survey healthcare/shelter; evaluate with overrides
    cap_input_1 = SiteCapacityInput.from_synthetic_feature(
        site_1,
        incoming_households=150,
        overrides={"healthcare_capacity": 200, "shelter_capacity": 180},
    )
    res1 = engine.evaluate(cap_input_1)
    assert res1.effective_capacity_households == 180
    assert res1.capacity_margin_households == 30
    assert res1.feasible is True

    # Test Site 12 (HIM-SITE-012): Batula Pocket Terrace (Bottleneck site, only 18 households capacity)
    site_12 = sites[11]
    cap_input_12 = SiteCapacityInput.from_synthetic_feature(
        site_12,
        incoming_households=50,  # Demand exceeds 18 hh
        overrides={"healthcare_capacity": 50, "shelter_capacity": 50},
    )
    res12 = engine.evaluate(cap_input_12)
    assert res12.effective_capacity_households == 18
    assert res12.capacity_margin_households == -32
    assert res12.feasible is False


# ==============================================================================
# 10. API ENDPOINTS AND ERROR HANDLING
# ==============================================================================

def test_api_evaluate_capacity_payload_endpoint(client):
    """Test 16: POST /api/v1/sites/capacity/evaluate returns structured response envelope."""
    payload = {
        "site_id": "API-SITE-001",
        "site_name": "API Payload Test Site",
        "incoming_households": 50,
        "housing_capacity": 100,
        "water_capacity": 80,
        "sanitation_capacity": 90,
        "healthcare_capacity": 120,
        "shelter_capacity": 110,
    }
    response = client.post("/api/v1/sites/capacity/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["effective_capacity_households"] == 80
    assert data["data"]["limiting_factors"] == ["water"]
    assert data["data"]["feasible"] is True


def test_api_capacity_evaluate_by_id_endpoints(client, mock_db):
    """Test 17: Evaluate database candidate site capacity by ID with overrides."""
    site = CandidateSite(
        id=201,
        name="DB Test Candidate Site",
        district_id=1,
        area_sq_m=50000.0,
        status="approved",
    )
    cap = SiteCapacity(
        site_id=201,
        max_households=100,
        max_population=400,
        allocated_households=10,
        available_households=90,
        water_supply_lpd=35000.0,
        sanitation_units=25,
    )
    site.capacities = [cap]
    site.infrastructures = []

    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = site
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # POST with overrides for healthcare and shelter
        payload = {
            "incoming_households": 60,
            "overrides": {
                "healthcare_capacity": 150,
                "shelter_capacity": 100,
            },
        }
        resp = client.post("/api/v1/sites/201/capacity/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["effective_capacity_households"] == 100
        assert data["data"]["current_occupancy_households"] == 10
        assert data["data"]["available_capacity_households"] == 90
        assert data["data"]["capacity_margin_households"] == 30
        assert data["data"]["feasible"] is True

        # GET capacity endpoint
        resp_get = client.get("/api/v1/sites/201/capacity?incoming_households=10")
        assert resp_get.status_code == 200
        get_data = resp_get.json()
        assert get_data["success"] is True
        # Without overrides, healthcare/shelter are unknown -> indeterminate/infeasible
        assert get_data["data"]["feasible"] is False
        assert "healthcare" in get_data["data"]["unknown_dimensions"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_capacity_invalid_region_profile_returns_structured_error(client):
    """Test 18: Requesting an invalid region profile returns structured HTTP 404 UNKNOWN_REGION_PROFILE without silent fallback."""
    payload = {
        "site_name": "Test Site",
        "incoming_households": 50,
        "housing_capacity": 100,
        "water_capacity": 80,
        "sanitation_capacity": 90,
        "healthcare_capacity": 120,
        "shelter_capacity": 110,
    }
    response = client.post(
        "/api/v1/sites/capacity/evaluate?region_profile_id=nonexistent_region",
        json=payload,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNKNOWN_REGION_PROFILE"
