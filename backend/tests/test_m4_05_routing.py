"""Focused automated tests for Chunk M4-05: Evacuation & Access Routing Engine."""

import math
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user, get_db, require_roles, UserRole
from app.core.relocation.routing import (
    BaseRoadNetworkProvider,
    EvacuationRoutingEngine,
    HazardAwareRouteEvaluator,
    HazardExposureDetail,
    InsufficientRoutingDataError,
    InvalidRouteInputError,
    RoadNetwork,
    RoadNode,
    RoadSegmentEdge,
    RouteExplainability,
    RouteQuery,
    RouteResult,
    RouteSegment,
    RouteStatus,
    RouteType,
    SegmentHazardStatus,
    SyntheticHimalayanRoadProvider,
    haversine_distance_km,
)
from app.models.geographic import Village
from app.models.governance import User
from app.models.relocation import CandidateSite, RelocationAssignment, Route
from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint, LineString as ShapelyLineString


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    return MagicMock()


# ==============================================================================
# 1-5. INPUT VALIDATION TESTS
# ==============================================================================

def test_01_invalid_longitude_out_of_bounds():
    """Test 01: Longitude outside [-180, 180] raises validation error."""
    with pytest.raises(ValueError, match="Longitude must be between"):
        RouteQuery(origin=(195.0, 30.5), destination=(79.5, 30.5))

    with pytest.raises(ValueError, match="Longitude must be between"):
        RouteQuery(origin=(-195.0, 30.5), destination=(79.5, 30.5))


def test_02_invalid_latitude_out_of_bounds():
    """Test 02: Latitude outside [-90, 90] raises validation error."""
    with pytest.raises(ValueError, match="Latitude must be between"):
        RouteQuery(origin=(79.5, 95.0), destination=(79.5, 30.5))

    with pytest.raises(ValueError, match="Latitude must be between"):
        RouteQuery(origin=(79.5, -95.0), destination=(79.5, 30.5))


def test_03_nan_coordinates_rejected():
    """Test 03: NaN coordinates are rejected with validation error."""
    with pytest.raises(ValueError, match="Coordinates must be finite numbers"):
        RouteQuery(origin=(float("nan"), 30.5), destination=(79.5, 30.5))

    with pytest.raises(ValueError, match="Coordinates must be finite numbers"):
        RouteQuery(origin=(79.5, 30.5), destination=(79.5, float("nan")))


def test_04_infinite_coordinates_rejected():
    """Test 04: Infinite coordinates are rejected with validation error."""
    with pytest.raises(ValueError, match="Coordinates must be finite numbers"):
        RouteQuery(origin=(float("inf"), 30.5), destination=(79.5, 30.5))

    with pytest.raises(ValueError, match="Coordinates must be finite numbers"):
        RouteQuery(origin=(79.5, 30.5), destination=(79.5, float("-inf")))


def test_05_invalid_negative_metric_on_segment():
    """Test 05: Negative distance on RouteSegment raises validation error."""
    with pytest.raises(Exception):
        RouteSegment(
            segment_id="SEG-NEG",
            from_node="A",
            to_node="B",
            geometry=[(79.5, 30.5), (79.6, 30.6)],
            distance_km=-4.5,
        )


# ==============================================================================
# 6-10. BASIC ROUTING TESTS
# ==============================================================================

def test_06_single_origin_destination_connected_network():
    """Test 06: Basic connected network resolves feasible route."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    # Sunil (79.5575, 30.5347) to Joshimath Hub (79.5650, 30.5550)
    query = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.5650, 30.5550),
        require_alternative=False,
    )
    res = engine.route(query)
    assert res.status == RouteStatus.FEASIBLE
    assert res.primary_route is not None
    assert res.primary_route.distance_km > 0.0
    assert len(res.primary_route.segments) >= 1


def test_07_route_geometry_based_on_actual_road_segments():
    """Test 07: Generated route geometry matches sequential road segment coordinates."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    query = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.5650, 30.5550),
        require_alternative=False,
    )
    res = engine.route(query)
    primary = res.primary_route
    assert primary is not None
    # Continuous coordinates
    assert len(primary.geometry) >= 2
    # First point matches the start segment origin
    assert primary.geometry[0] == primary.segments[0].geometry[0]
    # Last point matches the end segment destination
    assert primary.geometry[-1] == primary.segments[-1].geometry[-1]


def test_08_correct_route_distance():
    """Test 08: Route distance_km strictly equals the sum of segment distance_km."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    query = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.4300, 30.4300),  # Pipalkoti
        require_alternative=False,
    )
    res = engine.route(query)
    primary = res.primary_route
    assert primary is not None
    expected_sum = sum(s.distance_km for s in primary.segments)
    assert round(primary.distance_km, 2) == round(expected_sum, 2)
    assert primary.distance_km > 0.0


def test_09_correct_travel_time_calculation_when_data_exists():
    """Test 09: Estimated travel time is calculated from segment distances and speeds."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    query = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.5650, 30.5550),
        require_alternative=False,
    )
    res = engine.route(query)
    primary = res.primary_route
    assert primary is not None
    assert primary.estimated_time_minutes is not None
    expected_time = sum(s.estimated_time_minutes for s in primary.segments if s.estimated_time_minutes is not None)
    assert round(primary.estimated_time_minutes, 1) == round(expected_time, 1)


def test_10_deterministic_route_selection():
    """Test 10: Multiple calls with identical input select identical road segments."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    query = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.4300, 30.4300),
        require_alternative=False,
    )
    r1 = engine.route(query)
    r2 = engine.route(query)
    assert r1.primary_route is not None and r2.primary_route is not None
    assert r1.primary_route.distance_km == r2.primary_route.distance_km
    assert [s.segment_id for s in r1.primary_route.segments] == [s.segment_id for s in r2.primary_route.segments]


# ==============================================================================
# 11-15. HAZARD-AWARE ROUTING TESTS
# ==============================================================================

def test_11_blocked_hazard_segment_is_excluded():
    """Test 11: Explicitly blocked segment is completely excluded from safe primary route."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    # Block the valley segment SEG-VALLEY-02
    hazard_ctx = {"blocked_segment_ids": ["SEG-VALLEY-02"]}
    query = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        hazard_context=hazard_ctx,
        require_alternative=False,
    )
    res = engine.route(query)
    assert res.status == RouteStatus.FEASIBLE
    assert res.primary_route is not None
    used_seg_ids = {s.segment_id.replace("_rev", "") for s in res.primary_route.segments}
    assert "SEG-VALLEY-02" not in used_seg_ids


def test_12_hazardous_segment_receives_configured_penalty():
    """Test 12: Segment near a high hazard receives configured penalty added to cost."""
    # Place a high landslide near SEG-VALLEY-02 (79.525, 30.525)
    hazard_events = [
        {
            "id": "EVT-HIGH-LS",
            "hazard_type": "landslide",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [79.5250, 30.5250]},
            "description": "Active slope displacement zone",
        }
    ]
    evaluator = HazardAwareRouteEvaluator(hazard_events=hazard_events)
    edge = RoadSegmentEdge(
        segment_id="SEG-TEST-1",
        from_node="A",
        to_node="B",
        distance_km=4.0,
        geometry=[(79.5200, 30.5200), (79.5300, 30.5300)],
    )
    evaluated = evaluator.evaluate_segment(edge)
    assert evaluated.hazard_status == SegmentHazardStatus.PENALIZED
    assert evaluated.hazard_penalty > 0.0
    # For high severity, penalty is 1.5 * distance (4.0 * 1.5 = 6.0)
    assert evaluated.hazard_penalty == 6.0


def test_13_route_avoids_penalized_blocked_path_when_safer_alternative_cheaper():
    """Test 13: When valley corridor is blocked, route detours to Upper Ridge Bypass."""
    # Base route without hazard takes valley highway (shorter)
    engine_clear = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q_clear = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        require_alternative=False,
    )
    res_clear = engine_clear.route(q_clear)
    assert res_clear.primary_route is not None
    clear_segs = {s.segment_id.replace("_rev", "") for s in res_clear.primary_route.segments}
    assert "SEG-VALLEY-02" in clear_segs

    # With blocked valley segment, engine diverts to bypass corridor
    engine_hazard = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q_hazard = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        hazard_context={"blocked_segment_ids": ["SEG-VALLEY-02"]},
        require_alternative=False,
    )
    res_hazard = engine_hazard.route(q_hazard)
    assert res_hazard.primary_route is not None
    hazard_segs = {s.segment_id.replace("_rev", "") for s in res_hazard.primary_route.segments}
    assert "SEG-VALLEY-02" not in hazard_segs
    assert "SEG-BYPASS-02" in hazard_segs or "SEG-BYPASS-03" in hazard_segs


def test_14_explainability_lists_hazard_penalties():
    """Test 14: Explainability audit lists penalties applied to traversed segments."""
    hazard_events = [
        {
            "id": "EVT-RAIN-1",
            "hazard_type": "rainfall",
            "severity": "moderate",
            "location": {"type": "Point", "coordinates": [79.5500, 30.5450]},
            "description": "Localized water accumulation",
        }
    ]
    engine = EvacuationRoutingEngine(
        road_provider=SyntheticHimalayanRoadProvider(),
        hazard_evaluator=HazardAwareRouteEvaluator(hazard_events=hazard_events),
    )
    q = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.5350, 30.5350),
        require_alternative=False,
    )
    res = engine.route(q)
    assert res.primary_route is not None
    exp = res.primary_route.explainability
    assert len(exp.penalties_applied) >= 1
    assert "penalty" in exp.penalties_applied[0]


def test_15_blocked_segment_rejection_reason_is_present():
    """Test 15: Explainability contains explicit list of blocked corridors avoided."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        hazard_context={"blocked_segment_ids": ["SEG-VALLEY-03"]},
        require_alternative=False,
    )
    res = engine.route(q)
    assert res.primary_route is not None
    exp = res.primary_route.explainability
    assert any("SEG-VALLEY-03" in b for b in exp.blocked_segments_avoided)


# ==============================================================================
# 16-18. MISSING DATA SAFETY TESTS
# ==============================================================================

def test_16_missing_road_network_returns_insufficient_data():
    """Test 16: An empty or unreachable road network returns INSUFFICIENT_DATA."""
    class EmptyRoadProvider(BaseRoadNetworkProvider):
        def get_road_network(self, region_profile_id: str, bounding_box=None) -> RoadNetwork:
            return RoadNetwork()

    engine = EvacuationRoutingEngine(road_provider=EmptyRoadProvider())
    q = RouteQuery(origin=(79.5, 30.5), destination=(79.6, 30.6))
    res = engine.route(q)
    assert res.status == RouteStatus.INSUFFICIENT_DATA
    assert res.primary_route is None


def test_17_missing_hazard_data_does_not_silently_become_safe():
    """Test 17: Route computed with empty hazard data explicitly tracks uncertainty."""
    engine = EvacuationRoutingEngine(
        road_provider=SyntheticHimalayanRoadProvider(),
        hazard_evaluator=HazardAwareRouteEvaluator(hazard_events=[]),
    )
    q = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.5650, 30.5550),
        require_alternative=False,
    )
    res = engine.route(q)
    assert res.primary_route is not None
    assert len(res.primary_route.explainability.uncertainty_notes) >= 1


def test_18_missing_travel_time_data_returns_none_rather_than_fabricated():
    """Test 18: Segments without speed attributes yield estimated_time_minutes = None."""
    class NoSpeedRoadProvider(BaseRoadNetworkProvider):
        def get_road_network(self, region_profile_id: str, bounding_box=None) -> RoadNetwork:
            net = RoadNetwork()
            net.add_node(RoadNode(node_id="N1", location=(79.0, 30.0)))
            net.add_node(RoadNode(node_id="N2", location=(79.01, 30.01)))
            net.add_segment(
                RoadSegmentEdge(
                    segment_id="SEG-NOSPEED",
                    from_node="N1",
                    to_node="N2",
                    distance_km=2.0,
                    speed_kmh=None,  # Missing speed!
                    geometry=[(79.0, 30.0), (79.01, 30.01)],
                )
            )
            return net

    engine = EvacuationRoutingEngine(road_provider=NoSpeedRoadProvider())
    q = RouteQuery(origin=(79.0, 30.0), destination=(79.01, 30.01), require_alternative=False)
    res = engine.route(q)
    assert res.primary_route is not None
    assert res.primary_route.estimated_time_minutes is None


# ==============================================================================
# 19-21. ALTERNATIVE ROUTE TESTS
# ==============================================================================

def test_19_valid_alternative_route_generated():
    """Test 19: System successfully generates a secondary alternative route."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        require_alternative=True,
    )
    res = engine.route(q)
    assert res.status == RouteStatus.FEASIBLE
    assert res.primary_route is not None
    assert res.alternative_route is not None
    assert res.alternative_route.route_type == RouteType.ALTERNATIVE


def test_20_alternative_differs_from_primary():
    """Test 20: Alternative route uses genuinely distinct road segments from primary."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        require_alternative=True,
    )
    res = engine.route(q)
    p_segs = {s.segment_id.replace("_rev", "") for s in res.primary_route.segments}
    a_segs = {s.segment_id.replace("_rev", "") for s in res.alternative_route.segments}

    # They should not be identical
    assert p_segs != a_segs


def test_21_no_feasible_alternative_explicitly_reported():
    """Test 21: When only a single chokepoint corridor exists, alternative is explicitly None."""
    class SingleCorridorProvider(BaseRoadNetworkProvider):
        def get_road_network(self, region_profile_id: str, bounding_box=None) -> RoadNetwork:
            net = RoadNetwork()
            net.add_node(RoadNode(node_id="A", location=(79.1, 30.1)))
            net.add_node(RoadNode(node_id="B", location=(79.2, 30.2)))
            net.add_segment(
                RoadSegmentEdge(
                    segment_id="SEG-SOLO",
                    from_node="A",
                    to_node="B",
                    distance_km=5.0,
                    geometry=[(79.1, 30.1), (79.2, 30.2)],
                )
            )
            return net

    engine = EvacuationRoutingEngine(road_provider=SingleCorridorProvider())
    q = RouteQuery(origin=(79.1, 30.1), destination=(79.2, 30.2), require_alternative=True)
    res = engine.route(q)
    assert res.primary_route is not None
    assert res.alternative_route is None
    assert "NO_FEASIBLE_ALTERNATIVE" in res.primary_route.explainability.alternative_status


# ==============================================================================
# 22-24. M4-04 RELOCATION ASSIGNMENT INTEGRATION TESTS
# ==============================================================================

def test_22_route_generated_from_valid_relocation_assignment(client, mock_db):
    """Test 22: Route evaluated from a valid relocation assignment looks up village and site."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)

    v = Village(id=10, name="Sunil Village")
    v.location = from_shape(ShapelyPoint(79.5575, 30.5347), srid=4326)

    s = CandidateSite(id=20, name="Pipalkoti Safe Center")
    s.location = from_shape(ShapelyPoint(79.4300, 30.4300), srid=4326)

    assign = RelocationAssignment(
        id=99,
        village_id=10,
        candidate_site_id=20,
        assigned_households=30,
        assigned_population=120,
    )
    assign.village = v
    assign.site = s

    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = assign

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        resp = client.post("/api/v1/routes/generate", json={"assignment_id": 99})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "feasible"
        assert data["data"]["assignment_id"] == 99
        assert data["data"]["origin_village_name"] == "Sunil Village"
        assert data["data"]["destination_site_name"] == "Pipalkoti Safe Center"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_23_invalid_missing_assignment_rejected(client, mock_db):
    """Test 23: Nonexistent assignment ID returns 404 error."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        resp = client.post("/api/v1/routes/generate", json={"assignment_id": 9999})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_24_route_generation_does_not_mutate_assignment(client, mock_db):
    """Test 24: POST /routes/generate is purely analytical with zero DB mutations."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)

    v = Village(id=10, name="Sunil")
    v.location = from_shape(ShapelyPoint(79.5575, 30.5347), srid=4326)
    s = CandidateSite(id=20, name="Pipalkoti")
    s.location = from_shape(ShapelyPoint(79.4300, 30.4300), srid=4326)

    assign = RelocationAssignment(id=101, village_id=10, candidate_site_id=20, assigned_households=15, assigned_population=60)
    assign.village = v
    assign.site = s

    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = assign

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        resp = client.post("/api/v1/routes/generate", json={"assignment_id": 101})
        assert resp.status_code == 200

        # Assert zero database mutations on mock_db
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.flush.assert_not_called()
        mock_db.delete.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 25-27. 50-RUN REPEATED DETERMINISM TESTS
# ==============================================================================

def test_25_repeated_identical_input_returns_identical_primary_route():
    """Test 25: 50 repeated executions return identical primary route geometry and distance."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5575, 30.5347),
        destination=(79.4300, 30.4300),
        require_alternative=False,
    )
    first_res = engine.route(q)
    ref_distance = first_res.primary_route.distance_km
    ref_segs = [s.segment_id for s in first_res.primary_route.segments]
    ref_geom = first_res.primary_route.geometry

    for _ in range(50):
        r = engine.route(q)
        assert r.primary_route.distance_km == ref_distance
        assert [s.segment_id for s in r.primary_route.segments] == ref_segs
        assert r.primary_route.geometry == ref_geom


def test_26_repeated_identical_input_returns_identical_alternative():
    """Test 26: 50 repeated executions return identical alternative route."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        require_alternative=True,
    )
    first_res = engine.route(q)
    ref_alt_dist = first_res.alternative_route.distance_km
    ref_alt_segs = [s.segment_id for s in first_res.alternative_route.segments]

    for _ in range(50):
        r = engine.route(q)
        assert r.alternative_route.distance_km == ref_alt_dist
        assert [s.segment_id for s in r.alternative_route.segments] == ref_alt_segs


def test_27_stable_graph_tie_breaking():
    """Test 27: Graph tie-breaking key guarantees stable node order for equal cost edges."""
    class SymmetricalRoadProvider(BaseRoadNetworkProvider):
        def get_road_network(self, region_profile_id: str, bounding_box=None) -> RoadNetwork:
            net = RoadNetwork()
            net.add_node(RoadNode(node_id="START", location=(79.0, 30.0)))
            net.add_node(RoadNode(node_id="BRANCH_B", location=(79.01, 30.01)))
            net.add_node(RoadNode(node_id="BRANCH_A", location=(79.01, 29.99)))
            net.add_node(RoadNode(node_id="END", location=(79.02, 30.0)))

            # Two equal-cost paths: START->BRANCH_A->END (5.0 + 5.0) and START->BRANCH_B->END (5.0 + 5.0)
            net.add_segment(RoadSegmentEdge(segment_id="SEG-A1", from_node="START", to_node="BRANCH_A", distance_km=5.0, geometry=[(79.0, 30.0), (79.01, 29.99)]))
            net.add_segment(RoadSegmentEdge(segment_id="SEG-A2", from_node="BRANCH_A", to_node="END", distance_km=5.0, geometry=[(79.01, 29.99), (79.02, 30.0)]))
            net.add_segment(RoadSegmentEdge(segment_id="SEG-B1", from_node="START", to_node="BRANCH_B", distance_km=5.0, geometry=[(79.0, 30.0), (79.01, 30.01)]))
            net.add_segment(RoadSegmentEdge(segment_id="SEG-B2", from_node="BRANCH_B", to_node="END", distance_km=5.0, geometry=[(79.01, 30.01), (79.02, 30.0)]))
            return net

    engine = EvacuationRoutingEngine(road_provider=SymmetricalRoadProvider())
    q = RouteQuery(origin=(79.0, 30.0), destination=(79.02, 30.0), require_alternative=False)

    ref_choice = [s.segment_id for s in engine.route(q).primary_route.segments]
    # Because BRANCH_A < BRANCH_B lexicographically, BRANCH_A must consistently win
    assert ref_choice == ["SEG-A1", "SEG-A2"]

    for _ in range(50):
        res = engine.route(q)
        assert [s.segment_id for s in res.primary_route.segments] == ["SEG-A1", "SEG-A2"]


# ==============================================================================
# 28-32. API INTEGRATION TESTS
# ==============================================================================

def test_28_api_authenticated_generate_request_success(client):
    """Test 28: Authenticated request to POST /api/v1/routes/generate returns 200."""
    officer = User(id=5, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        payload = {
            "origin": [79.5575, 30.5347],
            "destination": [79.4300, 30.4300],
            "require_alternative": True,
        }
        resp = client.post("/api/v1/routes/generate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "feasible"
        assert data["data"]["primary_route"] is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_29_api_unauthenticated_returns_401(client):
    """Test 29: Unauthenticated request returns 401 Unauthorized."""
    resp = client.post(
        "/api/v1/routes/generate",
        json={"origin": [79.5575, 30.5347], "destination": [79.4300, 30.4300]},
    )
    assert resp.status_code == 401


def test_30_api_invalid_input_returns_validation_error(client):
    """Test 30: Invalid coordinate input returns 422 validation error."""
    officer = User(id=5, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        # Invalid latitude (120 > 90)
        payload = {"origin": [79.5575, 120.0], "destination": [79.4300, 30.4300]}
        resp = client.post("/api/v1/routes/generate", json=payload)
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_31_api_insufficient_data_returns_structured_domain_response(client):
    """Test 31: Out of range coordinates return INSUFFICIENT_DATA status gracefully."""
    officer = User(id=5, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        # Coordinates in Delhi (far outside Himalayan pilot road network)
        payload = {"origin": [77.2090, 28.6139], "destination": [77.2500, 28.6500]}
        resp = client.post("/api/v1/routes/generate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "insufficient_data"
        assert data["data"]["primary_route"] is None
        assert "exceeds threshold" in data["data"]["unassigned_reason"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_32_api_openapi_route_registration(client):
    """Test 32: Routing endpoints are registered in OpenAPI schema without collisions."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = schema.get("paths", {})
    assert "/api/v1/routes/generate" in paths
    assert "/api/v1/routes" in paths
    assert "/api/v1/routes/{id}" in paths


# ==============================================================================
# 33-34. SYNTHETIC PILOT SCENARIO TESTS
# ==============================================================================

def test_33_synthetic_himalayan_routing_scenario_end_to_end():
    """Test 33: End-to-end execution of Himalayan pilot routing from Sunil to Pipalkoti."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())
    q = RouteQuery(
        origin=(79.5575, 30.5347),  # Sunil
        destination=(79.4300, 30.4300),  # Pipalkoti
        require_alternative=True,
    )
    res = engine.route(q)
    assert res.status == RouteStatus.FEASIBLE
    assert res.primary_route is not None
    assert res.primary_route.distance_km > 15.0
    assert res.primary_route.estimated_time_minutes is not None
    assert res.alternative_route is not None


def test_34_hazard_aware_route_differs_from_naive_shortest_base_path():
    """Test 34: Active hazard HIM-EVT-001 cuts off valley highway, diverting route to Upper Ridge Bypass."""
    engine = EvacuationRoutingEngine(road_provider=SyntheticHimalayanRoadProvider())

    # Baseline: No hazard -> Valley highway is chosen because it is shorter (18.7 km vs 21.2 km)
    q_base = RouteQuery(
        origin=(79.5650, 30.5550),
        destination=(79.4300, 30.4300),
        require_alternative=False,
    )
    res_base = engine.route(q_base)
    assert res_base.primary_route is not None
    base_segs = [s.segment_id.replace("_rev", "") for s in res_base.primary_route.segments]
    assert "SEG-VALLEY-02" in base_segs
    assert "SEG-BYPASS-02" not in base_segs
    base_dist = res_base.primary_route.distance_km

    # Hazard active: Landslide HIM-EVT-001 blocks valley segment SEG-VALLEY-02
    hazard_events = [
        {
            "id": "HIM-EVT-001",
            "hazard_type": "landslide",
            "severity": "critical",
            "location": {"type": "Point", "coordinates": [79.5250, 30.5250]},
            "description": "Rain-triggered rotational debris slump; 120m highway cut off.",
        }
    ]
    hazard_engine = EvacuationRoutingEngine(
        road_provider=SyntheticHimalayanRoadProvider(),
        hazard_evaluator=HazardAwareRouteEvaluator(hazard_events=hazard_events),
    )
    res_hazard = hazard_engine.route(q_base)
    assert res_hazard.primary_route is not None
    hazard_segs = [s.segment_id.replace("_rev", "") for s in res_hazard.primary_route.segments]

    # The hazard-aware route strictly bypasses the blocked valley road and uses the upper bypass
    assert "SEG-VALLEY-02" not in hazard_segs
    assert "SEG-BYPASS-02" in hazard_segs
    # The safe bypass road is physically longer than the naive valley route
    assert res_hazard.primary_route.distance_km > base_dist
    assert any("HIM-EVT-001" in b for b in res_hazard.primary_route.explainability.blocked_segments_avoided)


# ==============================================================================
# 35. ROUTE PERSISTENCE AND RETRIEVAL API
# ==============================================================================

def test_35_api_route_persistence_and_retrieval(client, mock_db):
    """Test 35: POST /api/v1/routes stores a route and GET /api/v1/routes/{id} retrieves it."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)

    v = Village(id=10, name="Sunil")
    s = CandidateSite(id=20, name="Pipalkoti")

    mock_db.query.return_value.filter.return_value.first.side_effect = [v, s]

    created_route = Route(
        id=77,
        name="Sunil to Pipalkoti Primary Evacuation",
        origin_village_id=10,
        destination_site_id=20,
        distance_km=21.2,
        estimated_travel_time_min=42.0,
        route_type="evacuation",
        is_blocked=False,
    )
    created_route.path = from_shape(ShapelyLineString([(79.5575, 30.5347), (79.4300, 30.4300)]), srid=4326)
    created_route.origin_village = v
    created_route.destination_site = s

    # When add/commit called
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        create_payload = {
            "name": "Sunil to Pipalkoti Primary Evacuation",
            "origin_village_id": 10,
            "destination_site_id": 20,
            "path": {
                "type": "LineString",
                "coordinates": [[79.5575, 30.5347], [79.4300, 30.4300]],
            },
            "distance_km": 21.2,
            "estimated_travel_time_min": 42.0,
            "route_type": "evacuation",
        }
        resp = client.post("/api/v1/routes", json=create_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True

        # Now test GET /api/v1/routes/{id}
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = created_route
        get_resp = client.get("/api/v1/routes/77")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["success"] is True
        assert get_data["data"]["id"] == 77
        assert get_data["data"]["origin_village_name"] == "Sunil"
        assert get_data["data"]["distance_km"] == 21.2
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
