"""Focused automated tests for Chunk M4-04: Relocation Matching & Assignment Engine."""

from typing import Optional
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user, require_roles, UserRole
from app.core.relocation.capacity.contracts import SiteCapacityInput
from app.core.relocation.matching import (
    AssignmentStatus,
    InvalidMatchingInputError,
    MatchingSiteCandidate,
    RejectionReasonCode,
    RelocationMatchingEngine,
    VillageDemandInput,
    calculate_haversine_distance_km,
    compute_matching_rank_score,
    compute_proximity_score,
)
from app.core.relocation.suitability.contracts import SiteSuitabilityInput
from app.data.synthetic.loader import load_himalayan_pilot_dataset
from app.models.geographic import Village
from app.models.governance import User
from app.models.relocation import CandidateSite, RelocationAssignment, SiteCapacity


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    session = MagicMock()
    return session


def make_village(
    village_id: str = "V-001",
    village_name: str = "Test Village Alpha",
    priority_score: float = 85.0,
    priority_band: str = "immediate",
    incoming_hh: int = 50,
    incoming_pop: int = 200,
    coords: tuple = (79.0, 30.0),
) -> VillageDemandInput:
    """Helper to create a valid VillageDemandInput."""
    return VillageDemandInput(
        village_id=village_id,
        village_name=village_name,
        priority_score=priority_score,
        priority_band=priority_band,
        incoming_households=incoming_hh,
        incoming_population=incoming_pop,
        location=coords,
    )


def make_candidate_site(
    site_id: str = "S-001",
    site_name: str = "Safe Plateau Site",
    slope_deg: float = 6.0,
    buffer_m: float = 1200.0,
    max_hh: int = 200,
    avail_hh: Optional[int] = None,
    coords: tuple = (79.05, 30.02),
    status: str = "approved",
    water_lpd: float = 80.0,
    has_unknown_capacity: bool = False,
) -> MatchingSiteCandidate:
    """Helper to create a valid MatchingSiteCandidate."""
    available = max_hh if avail_hh is None else avail_hh
    occupancy = max_hh - available

    suit_input = SiteSuitabilityInput(
        site_id=site_id,
        name=site_name,
        terrain_slope_deg=slope_deg,
        hazard_buffer_distance_m=buffer_m,
        max_households=max_hh,
        available_households=available,
        road_width_m=6.0,
        water_supply_lpd_per_capita=water_lpd,
        distance_to_highway_km=1.0,
        distance_to_health_center_km=2.0,
        distance_to_school_km=1.5,
        distance_to_emergency_km=2.5,
        livelihood_potential="high",
        expansion_potential="high",
    )

    cap_input = SiteCapacityInput(
        site_id=site_id,
        site_name=site_name,
        incoming_households=0,
        current_occupancy_households=occupancy,
        household_size=4.0,
        housing_capacity=max_hh,
        water_capacity=max_hh,
        sanitation_capacity=max_hh,
        healthcare_capacity=None if has_unknown_capacity else max_hh + 50,
        shelter_capacity=None if has_unknown_capacity else max_hh + 50,
    )

    return MatchingSiteCandidate(
        site_id=site_id,
        site_name=site_name,
        location=coords,
        status=status,
        suitability_input=suit_input,
        capacity_input=cap_input,
    )


# ==============================================================================
# 1. ONE VILLAGE -> ONE FEASIBLE SITE
# ==============================================================================

def test_single_village_matches_to_single_feasible_site():
    """Test 1: A single prioritized village matches to a single safe, viable candidate site."""
    engine = RelocationMatchingEngine()
    village = make_village(village_id="V-101", priority_score=90.0, incoming_hh=40)
    site = make_candidate_site(site_id="S-101", avail_hh=100)

    result = engine.match(villages=[village], sites=[site])

    assert result.total_villages == 1
    assert result.assigned_villages_count == 1
    assert result.unassigned_villages_count == 0
    assert result.total_households_allocated == 40
    assert result.site_remaining_capacities["S-101"] == 60  # 100 - 40

    assignment = result.assignments[0]
    assert assignment.status == AssignmentStatus.ASSIGNED
    assert assignment.assigned_site_id == "S-101"
    assert assignment.available_capacity_before == 100
    assert assignment.available_capacity_after == 60
    assert assignment.distance_km is not None
    assert "Selected top-ranked site" in assignment.selection_reason


# ==============================================================================
# 2. MULTIPLE VILLAGES -> DETERMINISTIC PRIORITY ORDERING
# ==============================================================================

def test_multiple_villages_ordered_by_descending_priority():
    """Test 2: Villages are processed strictly in descending order of relocation priority."""
    engine = RelocationMatchingEngine()
    # Provided in arbitrary order: 45, 95, 75
    v1 = make_village(village_id="V-LOW", priority_score=45.0, incoming_hh=20)
    v2 = make_village(village_id="V-HIGH", priority_score=95.0, incoming_hh=30)
    v3 = make_village(village_id="V-MED", priority_score=75.0, incoming_hh=25)

    site = make_candidate_site(site_id="S-LARGE", avail_hh=200)

    result = engine.match(villages=[v1, v2, v3], sites=[site])

    assert [a.village_id for a in result.assignments] == ["V-HIGH", "V-MED", "V-LOW"]
    assert result.assigned_villages_count == 3


# ==============================================================================
# 3. COMPETITION FOR LIMITED CAPACITY
# ==============================================================================

def test_multiple_villages_competing_for_limited_capacity():
    """Test 3: Higher priority village secures allocation; lower priority village cannot when capacity is exhausted."""
    engine = RelocationMatchingEngine()
    # Total site capacity is 60 households
    site = make_candidate_site(site_id="S-LIMITED", avail_hh=60)

    v_high = make_village(village_id="V-HIGH", priority_score=92.0, incoming_hh=40)
    v_low = make_village(village_id="V-LOW", priority_score=60.0, incoming_hh=40)

    result = engine.match(villages=[v_low, v_high], sites=[site])

    # v_high processed first -> gets 40, leaving 20. v_low needs 40 -> insufficient capacity (unassigned)
    assert result.assignments[0].village_id == "V-HIGH"
    assert result.assignments[0].status == AssignmentStatus.ASSIGNED
    assert result.assignments[0].available_capacity_after == 20

    assert result.assignments[1].village_id == "V-LOW"
    assert result.assignments[1].status == AssignmentStatus.UNASSIGNED
    assert result.assignments[1].unassigned_code == RejectionReasonCode.INSUFFICIENT_CAPACITY
    assert "insufficient remaining capacity" in result.assignments[1].unassigned_reason.lower()


# ==============================================================================
# 4. CAPACITY RESERVATION DYNAMICS
# ==============================================================================

def test_capacity_reservation_after_each_assignment():
    """Test 4: Each assignment decrements available capacity dynamically without mutating persisted state."""
    engine = RelocationMatchingEngine()
    site = make_candidate_site(site_id="S-SHARED", avail_hh=100)

    v1 = make_village(village_id="V-1", priority_score=90.0, incoming_hh=30)
    v2 = make_village(village_id="V-2", priority_score=80.0, incoming_hh=40)
    v3 = make_village(village_id="V-3", priority_score=70.0, incoming_hh=20)

    result = engine.match(villages=[v1, v2, v3], sites=[site])

    assert result.assignments[0].available_capacity_before == 100
    assert result.assignments[0].available_capacity_after == 70

    assert result.assignments[1].available_capacity_before == 70
    assert result.assignments[1].available_capacity_after == 30

    assert result.assignments[2].available_capacity_before == 30
    assert result.assignments[2].available_capacity_after == 10

    assert result.site_remaining_capacities["S-SHARED"] == 10


# ==============================================================================
# 5. SITE BECOMING INFEASIBLE AFTER EARLIER ASSIGNMENTS
# ==============================================================================

def test_site_becomes_infeasible_and_subsequent_village_diverts_to_alternate_site():
    """Test 5: Once a site is exhausted, the next village dynamically diverts to an alternate feasible site."""
    engine = RelocationMatchingEngine()
    site_a = make_candidate_site(site_id="S-A", site_name="Site Alpha", slope_deg=2.0, coords=(79.01, 30.01), avail_hh=50)
    site_b = make_candidate_site(site_id="S-B", site_name="Site Beta", slope_deg=12.0, coords=(79.25, 30.25), avail_hh=80)

    v1 = make_village(village_id="V-1", priority_score=95.0, incoming_hh=50)
    v2 = make_village(village_id="V-2", priority_score=85.0, incoming_hh=40)

    result = engine.match(villages=[v1, v2], sites=[site_a, site_b])

    # V-1 gets Site A (exhausting it to 0)
    assert result.assignments[0].assigned_site_id == "S-A"
    assert result.assignments[0].available_capacity_after == 0

    # V-2 sees Site A as exhausted -> allocates to Site B
    assert result.assignments[1].assigned_site_id == "S-B"
    assert result.assignments[1].available_capacity_after == 40

    # Audit for V-2 shows Site A rejected due to insufficient capacity
    audit_a = next(a for a in result.assignments[1].evaluated_candidates if a.site_id == "S-A")
    assert audit_a.is_feasible is False
    assert audit_a.rejection_code == RejectionReasonCode.INSUFFICIENT_CAPACITY


# ==============================================================================
# 6. UNSAFE M4-02 SITE REJECTED
# ==============================================================================

def test_unsafe_site_failing_m4_02_hard_constraint_rejected():
    """Test 6: Site violating M4-02 slope safety constraint is rejected with UNSAFE_SITE."""
    engine = RelocationMatchingEngine()
    # Slope 28 degrees exceeds 15 degree threshold
    unsafe_site = make_candidate_site(site_id="S-STEEP", slope_deg=28.0, avail_hh=100)
    village = make_village(village_id="V-1", incoming_hh=30)

    result = engine.match(villages=[village], sites=[unsafe_site])

    assert result.assignments[0].status == AssignmentStatus.UNASSIGNED
    assert result.assignments[0].unassigned_code == RejectionReasonCode.UNSAFE_SITE

    audit = result.assignments[0].evaluated_candidates[0]
    assert audit.is_feasible is False
    assert audit.rejection_code == RejectionReasonCode.UNSAFE_SITE
    assert any("slope" in r.lower() for r in audit.rejection_reasons)


# ==============================================================================
# 7. INSUFFICIENT M4-03 CAPACITY REJECTED
# ==============================================================================

def test_site_with_insufficient_m4_03_capacity_rejected():
    """Test 7: Site with insufficient capacity is rejected with INSUFFICIENT_CAPACITY."""
    engine = RelocationMatchingEngine()
    small_site = make_candidate_site(site_id="S-SMALL", avail_hh=25)
    large_village = make_village(village_id="V-LARGE", incoming_hh=70)

    result = engine.match(villages=[large_village], sites=[small_site])

    assert result.assignments[0].status == AssignmentStatus.UNASSIGNED
    audit = result.assignments[0].evaluated_candidates[0]
    assert audit.is_feasible is False
    assert audit.rejection_code == RejectionReasonCode.INSUFFICIENT_CAPACITY
    assert audit.capacity_margin == -45


# ==============================================================================
# 8. UNKNOWN CRITICAL CAPACITY REJECTED
# ==============================================================================

def test_site_with_unknown_capacity_never_treated_as_unlimited():
    """Test 8: Site with unknown/unspecified critical capacity dimension is rejected with UNKNOWN_CAPACITY."""
    engine = RelocationMatchingEngine()
    unknown_site = make_candidate_site(site_id="S-UNKNOWN", has_unknown_capacity=True)
    village = make_village(village_id="V-1", incoming_hh=20)

    result = engine.match(villages=[village], sites=[unknown_site])

    assert result.assignments[0].status == AssignmentStatus.UNASSIGNED
    audit = result.assignments[0].evaluated_candidates[0]
    assert audit.is_feasible is False
    assert audit.rejection_code == RejectionReasonCode.UNKNOWN_CAPACITY
    assert any("unknown" in r.lower() and "missing" in r.lower() for r in audit.rejection_reasons)


# ==============================================================================
# 9. VILLAGE CORRECTLY RETURNED AS UNASSIGNED
# ==============================================================================

def test_village_returned_as_unassigned_when_no_site_feasible():
    """Test 9: Village is cleanly marked UNASSIGNED when all candidate sites fail constraints."""
    engine = RelocationMatchingEngine()
    site_steep = make_candidate_site(site_id="S-1", slope_deg=35.0, avail_hh=100)
    site_buffer = make_candidate_site(site_id="S-2", buffer_m=100.0, avail_hh=100)
    site_small = make_candidate_site(site_id="S-3", avail_hh=10)

    village = make_village(village_id="V-ALL-FAIL", incoming_hh=50)

    result = engine.match(villages=[village], sites=[site_steep, site_buffer, site_small])

    assignment = result.assignments[0]
    assert assignment.status == AssignmentStatus.UNASSIGNED
    assert assignment.assigned_site_id is None
    assert len(assignment.evaluated_candidates) == 3
    assert len(assignment.unassigned_reason) > 0


# ==============================================================================
# 10. DETERMINISTIC TIE-BREAKING
# ==============================================================================

def test_deterministic_tie_breaking_for_villages_and_sites():
    """Test 10: Deterministic tie-breaking on village IDs and site IDs."""
    engine = RelocationMatchingEngine()
    # Villages with identical priority score
    v_b = make_village(village_id="VILLAGE-B", priority_score=80.0, incoming_hh=10)
    v_a = make_village(village_id="VILLAGE-A", priority_score=80.0, incoming_hh=10)

    # Identical sites
    site_2 = make_candidate_site(site_id="SITE-2", coords=(79.1, 30.1), avail_hh=100)
    site_1 = make_candidate_site(site_id="SITE-1", coords=(79.1, 30.1), avail_hh=100)

    result = engine.match(villages=[v_b, v_a], sites=[site_2, site_1])

    # Village A must be processed first (alphabetical ID tie-breaker)
    assert result.assignments[0].village_id == "VILLAGE-A"
    assert result.assignments[1].village_id == "VILLAGE-B"

    # Both should break ties deterministically to SITE-1
    assert result.assignments[0].assigned_site_id == "SITE-1"


# ==============================================================================
# 11. DETERMINISTIC REPEATED EXECUTION
# ==============================================================================

def test_deterministic_repeated_execution():
    """Test 11: 50 repeated executions produce identical assignments, rankings, and capacity values."""
    engine = RelocationMatchingEngine()
    v1 = make_village(village_id="V-1", priority_score=90.0, incoming_hh=30)
    v2 = make_village(village_id="V-2", priority_score=75.0, incoming_hh=40)
    s1 = make_candidate_site(site_id="S-1", avail_hh=60)
    s2 = make_candidate_site(site_id="S-2", avail_hh=60)

    baseline = engine.match(villages=[v1, v2], sites=[s1, s2])

    for _ in range(50):
        run = engine.match(villages=[v1, v2], sites=[s1, s2])
        assert [a.assigned_site_id for a in run.assignments] == [a.assigned_site_id for a in baseline.assignments]
        assert [a.available_capacity_after for a in run.assignments] == [a.available_capacity_after for a in baseline.assignments]
        assert run.site_remaining_capacities == baseline.site_remaining_capacities


# ==============================================================================
# 12. SPATIAL DISTANCE AND PROXIMITY RANKING
# ==============================================================================

def test_haversine_distance_and_proximity_ranking():
    """Test 12: Distance calculation and proximity scoring prioritize nearby feasible sites."""
    coord_v = (78.0, 30.0)
    coord_near = (78.05, 30.02)  # ~5.3 km away
    coord_far = (78.40, 30.30)   # ~50+ km away

    dist_near = calculate_haversine_distance_km(coord_v, coord_near)
    dist_far = calculate_haversine_distance_km(coord_v, coord_far)
    assert dist_near < dist_far
    assert dist_near > 0

    prox_near = compute_proximity_score(dist_near)
    prox_far = compute_proximity_score(dist_far)
    assert prox_near > prox_far

    rank_near = compute_matching_rank_score(80.0, dist_near)
    rank_far = compute_matching_rank_score(80.0, dist_far)
    assert rank_near > rank_far


# ==============================================================================
# 13. EXPLAINABILITY AUDIT PAYLOAD
# ==============================================================================

def test_explainability_payload_completeness():
    """Test 13: The matching result contains full audit breakdown and human-readable provenance."""
    engine = RelocationMatchingEngine()
    v = make_village(village_id="V-AUDIT", priority_score=88.0, incoming_hh=35)
    s_good = make_candidate_site(site_id="S-GOOD", avail_hh=100)
    s_bad = make_candidate_site(site_id="S-BAD", slope_deg=30.0, avail_hh=100)

    result = engine.match(villages=[v], sites=[s_good, s_bad])

    assignment = result.assignments[0]
    assert len(assignment.evaluated_candidates) == 2
    assert assignment.evaluated_candidates[0].site_id in ("S-GOOD", "S-BAD")
    assert assignment.selection_reason is not None
    assert result.governance_notice is not None
    assert "DECISION SUPPORT ONLY" in result.governance_notice


# ==============================================================================
# 14. INPUT VALIDATION (NaN, INFINITY, NEGATIVE)
# ==============================================================================

def test_input_validation_rejects_nan_infinity_and_negative():
    """Test 14: Input validation rejects invalid values with InvalidMatchingInputError."""
    with pytest.raises(InvalidMatchingInputError):
        VillageDemandInput(
            village_id="V-INVALID",
            village_name="Negative Households",
            priority_score=50.0,
            incoming_households=-10,
        )

    with pytest.raises(InvalidMatchingInputError):
        VillageDemandInput(
            village_id="V-INVALID",
            village_name="NaN Priority",
            priority_score=float("nan"),
            incoming_households=10,
        )

    with pytest.raises(InvalidMatchingInputError):
        VillageDemandInput(
            village_id="V-INVALID",
            village_name="Score Above 100",
            priority_score=150.0,
            incoming_households=10,
        )


# ==============================================================================
# 15. SYNTHETIC HIMALAYAN PILOT BATCH MATCHING
# ==============================================================================

def test_synthetic_himalayan_pilot_dataset_batch_matching():
    """Test 15: Run relocation matching against synthetic Himalayan pilot dataset."""
    dataset = load_himalayan_pilot_dataset()
    engine = RelocationMatchingEngine()

    # Load 5 sample villages from synthetic fixtures
    v_features = dataset.villages.features[:5]
    villages = [
        VillageDemandInput.from_synthetic_feature(f, priority_score=70.0 + idx * 5.0)
        for idx, f in enumerate(v_features)
    ]

    # Load 4 sample candidate sites with override capacities populated
    s_features = dataset.candidate_sites.features[:4]
    sites = [
        MatchingSiteCandidate.from_synthetic_feature(
            f, overrides={"healthcare_capacity": 150, "shelter_capacity": 150}
        )
        for f in s_features
    ]

    result = engine.match(villages=villages, sites=sites)

    assert result.total_villages == 5
    assert len(result.assignments) == 5
    assert result.total_households_allocated + result.total_households_unassigned == result.total_households_demanded


# ==============================================================================
# 16. API: POST /api/v1/relocation/match
# ==============================================================================

def test_api_relocation_match_endpoint(client):
    """Test 16: POST /api/v1/relocation/match returns structured ResponseEnvelope with matching result."""
    payload = {
        "villages": [
            {
                "village_id": "API-V-01",
                "village_name": "API Village 1",
                "priority_score": 85.0,
                "incoming_households": 30,
            }
        ],
        "sites": [
            {
                "site_id": "API-S-01",
                "site_name": "API Candidate Site 1",
                "status": "approved",
                "suitability_input": {
                    "name": "API Site 1",
                    "terrain_slope_deg": 5.0,
                    "hazard_buffer_distance_m": 1000.0,
                    "max_households": 100,
                    "available_households": 100,
                },
                "capacity_input": {
                    "site_name": "API Site 1",
                    "incoming_households": 0,
                    "housing_capacity": 100,
                    "water_capacity": 100,
                    "sanitation_capacity": 100,
                    "healthcare_capacity": 100,
                    "shelter_capacity": 100,
                },
            }
        ],
    }

    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        response = client.post("/api/v1/relocation/match", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["assigned_villages_count"] == 1
        assert data["data"]["assignments"][0]["assigned_site_id"] == "API-S-01"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_api_relocation_match_unauthenticated_returns_401(client):
    """Test that POST /api/v1/relocation/match without auth credentials returns HTTP 401."""
    response = client.post("/api/v1/relocation/match", json={"villages": [], "sites": []})
    assert response.status_code == 401


# ==============================================================================
# 17. API: PERSISTENCE (POST /assignments, GET /assignments)
# ==============================================================================

def test_api_relocation_assignment_persistence(client, mock_db):
    """Test 17: Persisting and retrieving relocation assignments with auth dependency."""
    # Mock current user as DISTRICT_OFFICER
    officer = User(id=10, username="test_officer", role="district_officer", is_active=True)
    village = Village(id=1, name="Joshimath Ward 1", block_id=1, location="POINT(79.5 30.5)")
    site = CandidateSite(id=2, name="Pipalkoti Safe Terrace", district_id=1, location="POINT(79.4 30.4)")
    cap = SiteCapacity(site_id=2, max_households=100, allocated_households=0, available_households=100)
    site.capacities = [cap]

    mock_db.query.return_value.filter.return_value.first.side_effect = [village, site, village, site]

    assignment_record = RelocationAssignment(
        id=501,
        village_id=1,
        candidate_site_id=2,
        assigned_households=30,
        assigned_population=120,
        status="approved",
        approved_by_officer_id=10,
    )
    assignment_record.village = village
    assignment_record.site = site

    mock_db.refresh = lambda obj: None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        # POST /api/v1/relocation/assignments
        create_payload = {
            "village_id": 1,
            "candidate_site_id": 2,
            "assigned_households": 30,
            "assigned_population": 120,
            "status": "approved",
        }
        resp = client.post("/api/v1/relocation/assignments", json=create_payload)
        assert resp.status_code == 201
        res_data = resp.json()
        assert res_data["success"] is True
        assert res_data["data"]["assigned_households"] == 30
        assert res_data["data"]["village_name"] == "Joshimath Ward 1"

        # GET /api/v1/relocation/assignments/{id}
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = assignment_record
        mock_db.query.return_value = mock_query

        get_resp = client.get("/api/v1/relocation/assignments/501")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["success"] is True
        assert get_data["data"]["id"] == 501
        assert get_data["data"]["status"] == "approved"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 18. API: INVALID REGION PROFILE RETURNS 404
# ==============================================================================

def test_api_matching_invalid_region_profile_returns_404(client):
    """Test 18: Requesting an unknown region profile ID returns structured HTTP 404 UNKNOWN_REGION_PROFILE."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        payload = {
            "region_profile_id": "nonexistent_profile_xyz",
            "villages": [
                {
                    "village_id": "V-1",
                    "village_name": "Test Village",
                    "priority_score": 50.0,
                    "incoming_households": 10,
                }
            ],
            "sites": [],
        }
        response = client.post("/api/v1/relocation/match", json=payload)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNKNOWN_REGION_PROFILE"
    finally:
        app.dependency_overrides.pop(get_current_user, None)



# ==============================================================================
# 19. EXACT LINEAR PROXIMITY FORMULA VERIFICATION
# ==============================================================================

def test_exact_linear_proximity_formula_and_boundary_conditions():
    """Test 19: Exact linear proximity formula max(0.0, 100.0 - 2.0 * d_km) and clamp [0, 100]."""
    # At 0 km -> 100.0
    assert compute_proximity_score(0.0) == 100.0
    # At 10 km -> 80.0
    assert compute_proximity_score(10.0) == 80.0
    # At 25 km -> 50.0
    assert compute_proximity_score(25.0) == 50.0
    # At 50 km -> 0.0
    assert compute_proximity_score(50.0) == 0.0
    # Beyond 50 km -> 0.0
    assert compute_proximity_score(55.0) == 0.0
    assert compute_proximity_score(120.0) == 0.0

    # None and NaN/Inf return None
    assert compute_proximity_score(None) is None
    assert compute_proximity_score(float("nan")) is None
    assert compute_proximity_score(float("inf")) is None

    # Negative distance raises ValueError
    with pytest.raises(ValueError):
        compute_proximity_score(-5.0)


# ==============================================================================
# 20. EXACT RANK-SCORE FORMULA AND MISSING COORDINATES FALLBACK
# ==============================================================================

def test_exact_rank_score_formula_and_missing_coordinates():
    """Test 20: rank_score = 0.70 * suitability + 0.30 * proximity (or suitability if missing coords)."""
    # When coordinates exist: suit=70.0, d=10.0km -> prox=80.0
    # Expected: 0.70 * 70.0 + 0.30 * 80.0 = 49.0 + 24.0 = 73.0
    score = compute_matching_rank_score(suitability_score=70.0, distance_km=10.0)
    assert score == 73.0

    # When coordinates are absent (distance_km is None):
    # Expected: rank_score = suitability_score = 70.0
    score_no_coords = compute_matching_rank_score(suitability_score=70.0, distance_km=None)
    assert score_no_coords == 70.0


# ==============================================================================
# 21. EXACT DETERMINISTIC SITE TIE-BREAKING ORDER
# ==============================================================================

def test_exact_site_tie_breaking_order():
    """Test 21: Exact sort order (-rank_score, -suitability_score, distance_km, str(site_id))."""
    from app.core.relocation.matching.ranking import sort_feasible_candidates

    c1 = {"site_id": "SITE-B", "rank_score": 75.0, "suitability_score": 70.0, "distance_km": 10.0}
    c2 = {"site_id": "SITE-A", "rank_score": 75.0, "suitability_score": 70.0, "distance_km": 10.0}
    # Identical scores and distance -> alphabetical site_id wins (SITE-A first)
    sorted_res = sort_feasible_candidates([c1, c2])
    assert sorted_res[0]["site_id"] == "SITE-A"
    assert sorted_res[1]["site_id"] == "SITE-B"

    # Higher rank score wins
    c3 = {"site_id": "SITE-C", "rank_score": 80.0, "suitability_score": 70.0, "distance_km": 10.0}
    sorted_res2 = sort_feasible_candidates([c1, c3])
    assert sorted_res2[0]["site_id"] == "SITE-C"

    # Identical rank score, higher suitability score wins
    c4 = {"site_id": "SITE-D", "rank_score": 75.0, "suitability_score": 72.0, "distance_km": 15.0}
    sorted_res3 = sort_feasible_candidates([c1, c4])
    assert sorted_res3[0]["site_id"] == "SITE-D"

    # Identical rank score, identical suitability score, closer distance wins
    c5 = {"site_id": "SITE-E", "rank_score": 75.0, "suitability_score": 70.0, "distance_km": 5.0}
    sorted_res4 = sort_feasible_candidates([c1, c5])
    assert sorted_res4[0]["site_id"] == "SITE-E"


def test_exact_rank_score_micro_difference_without_rounding_bias():
    """Test that micro-differences (< 0.00005) in rank_score are respected without rounding bias."""
    from app.core.relocation.matching.ranking import sort_feasible_candidates

    # c1 has rank_score 70.00004, c2 has rank_score 70.00001
    # Under round(..., 4), both would be 70.0000 creating an artificial tie where SITE-A would win.
    # With unrounded float comparison, SITE-B must win because 70.00004 > 70.00001.
    c1 = {"site_id": "SITE-B", "rank_score": 70.00004, "suitability_score": 70.0, "distance_km": 10.0}
    c2 = {"site_id": "SITE-A", "rank_score": 70.00001, "suitability_score": 70.0, "distance_km": 10.0}

    sorted_res = sort_feasible_candidates([c1, c2])
    assert sorted_res[0]["site_id"] == "SITE-B"
    assert sorted_res[1]["site_id"] == "SITE-A"


def test_site_with_positive_capacity_below_20_is_not_rejected_by_hard_constraint():
    """Test that a site with positive capacity below 20 (e.g. 12) passes M4-02 hard safety gate (> 0).

    It is then evaluated against village demand:
    - Village with 10 households: fits and gets assigned.
    - Subsequent village with 5 households: fails on capacity sufficiency (margin = -3), NOT hard constraint.
    """
    engine = RelocationMatchingEngine()
    # Site with capacity 12 (below 20, but > 0)
    site_small = make_candidate_site(site_id="S-CAP-12", max_hh=12, avail_hh=12)

    v1 = make_village(village_id="V-1", priority_score=90.0, incoming_hh=10)
    v2 = make_village(village_id="V-2", priority_score=80.0, incoming_hh=5)

    result = engine.match(villages=[v1, v2], sites=[site_small])

    # V-1 successfully gets assigned
    assert result.assignments[0].status == AssignmentStatus.ASSIGNED
    assert result.assignments[0].assigned_site_id == "S-CAP-12"
    assert result.assignments[0].available_capacity_before == 12
    assert result.assignments[0].available_capacity_after == 2

    # V-2 gets UNASSIGNED due to INSUFFICIENT_CAPACITY (not UNSAFE_SITE)
    assert result.assignments[1].status == AssignmentStatus.UNASSIGNED
    audit_v2 = result.assignments[1].evaluated_candidates[0]
    assert audit_v2.is_feasible is False
    assert audit_v2.rejection_code == RejectionReasonCode.INSUFFICIENT_CAPACITY
    assert audit_v2.capacity_margin == -3


# ==============================================================================
# 22. REJECTION TAXONOMY: LOW_SUITABILITY REJECTION
# ==============================================================================

def test_low_suitability_rejection_code():
    """Test 22: Site passing hard safety constraints but with overall score < 40.0 is rejected with LOW_SUITABILITY."""
    from app.core.relocation.suitability.contracts import SiteSuitabilityResult, SuitabilityDecision

    engine = RelocationMatchingEngine()
    precomputed = SiteSuitabilityResult(
        site_id="S-LOW-SUIT",
        site_name="Low Suitability Site",
        decision=SuitabilityDecision.UNSUITABLE,
        overall_score=35.0,
        is_eligible=True,
        hard_constraints=[],
        criteria_scores={},
        limiting_factors=[],
        governance_notice="PILOT ONLY",
    )
    low_suit_site = MatchingSiteCandidate(
        site_id="S-LOW-SUIT",
        site_name="Low Suitability Site",
        initial_available_capacity=50,
        precomputed_suitability=precomputed,
    )
    village = make_village(village_id="V-1", incoming_hh=20)

    result = engine.match(villages=[village], sites=[low_suit_site])
    assignment = result.assignments[0]
    assert assignment.status == AssignmentStatus.UNASSIGNED
    audit = assignment.evaluated_candidates[0]
    assert audit.is_feasible is False
    assert audit.rejection_code == RejectionReasonCode.LOW_SUITABILITY


# ==============================================================================
# 23. REJECTION TAXONOMY: SITE_UNAVAILABLE REJECTION
# ==============================================================================

def test_site_unavailable_rejection_code():
    """Test 23: Inactive or rejected site in registry is rejected with SITE_UNAVAILABLE."""
    engine = RelocationMatchingEngine()
    inactive_site = make_candidate_site(site_id="S-INACTIVE", status="inactive")
    rejected_site = make_candidate_site(site_id="S-REJECTED", status="rejected")
    village = make_village(village_id="V-1", incoming_hh=15)

    result = engine.match(villages=[village], sites=[inactive_site, rejected_site])
    audits = result.assignments[0].evaluated_candidates
    assert len(audits) == 2
    assert all(a.is_feasible is False for a in audits)
    assert all(a.rejection_code == RejectionReasonCode.SITE_UNAVAILABLE for a in audits)


# ==============================================================================
# 24. API: MATCH ENDPOINT IS PURE EVALUATION (ZERO DB MUTATION)
# ==============================================================================

def test_api_match_pure_evaluation_zero_database_mutation(client, mock_db):
    """Test 24: POST /api/v1/relocation/match is purely analytical with zero DB mutations."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        payload = {
            "villages": [
                {
                    "village_id": "V-PURE-1",
                    "village_name": "Pure Evaluation Village",
                    "priority_score": 90.0,
                    "incoming_households": 20,
                }
            ],
            "sites": [
                {
                    "site_id": "S-PURE-1",
                    "site_name": "Pure Evaluation Site",
                    "initial_available_capacity": 50,
                    "suitability_input": {
                        "name": "Pure Site",
                        "terrain_slope_deg": 5.0,
                        "hazard_buffer_distance_m": 1000.0,
                        "max_households": 100,
                        "available_households": 100,
                    },
                }
            ],
        }
        resp = client.post("/api/v1/relocation/match", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        # Assert zero database mutations occurred on mock_db
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.flush.assert_not_called()
        mock_db.delete.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 25. API: GET /api/v1/relocation/assignments (LIST, FILTER, PAGINATE)
# ==============================================================================

def test_api_list_relocation_assignments_filtering_and_pagination(client, mock_db):
    """Test 25: GET /api/v1/relocation/assignments supports auth, filtering, and pagination."""
    officer = User(id=10, username="test_officer", role="district_officer", is_active=True)
    village = Village(id=1, name="Joshimath Ward 1", block_id=1)
    site = CandidateSite(id=2, name="Pipalkoti Safe Terrace", district_id=1)

    r1 = RelocationAssignment(
        id=101,
        village_id=1,
        candidate_site_id=2,
        assigned_households=25,
        assigned_population=100,
        status="approved",
    )
    r1.village = village
    r1.site = site

    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [r1]

    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        resp = client.get(
            "/api/v1/relocation/assignments?village_id=1&candidate_site_id=2&status=approved&page=1&page_size=10"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == 101
        assert data["data"][0]["village_name"] == "Joshimath Ward 1"
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

