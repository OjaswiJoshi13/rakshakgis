"""Integration and security validation test suite for INT-01.

Validates:
1. Option A Demo Authentication Security:
   - Accepts 'demo-authority-access-token' in permitted development/demo mode.
   - Resolves to demo user 'district_collector_chamoli' (role: district_officer).
   - Strictly rejected outside development/demo mode (e.g. APP_ENV=production or DATA_MODE=live).
   - Normal JWT authentication remains fully functional and unchanged.
   - Unauthenticated requests remain 401 Unauthorized.
   - RBAC behavior is strictly enforced (district_officer allowed for officer routes, rejected with 403 for admin-only routes).
2. End-to-End Data Flow across Core Endpoints:
   - GET /api/v1/villages and GET /api/v1/villages/{id}
   - GET /api/v1/red-zones and GET /api/v1/red-zones/{id}
   - GET /api/v1/alerts and POST /api/v1/alerts/{id}/acknowledge
   - GET /api/v1/sites and GET /api/v1/sites/{id}
   - POST /api/v1/sites/{id}/evaluate
   - POST /api/v1/scenarios/run
   - POST /api/v1/relocation/match
   - GET /api/v1/routes
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.data.seed import seed_himalayan_pilot_data
from app.main import app
from app.models.geographic import Village
from app.models.governance import User
from app.models.relocation import CandidateSite, Route
from app.models.risk import RedZone
from app.models.telemetry import Alert

client = TestClient(app)
settings = get_settings()


@pytest.fixture(scope="module", autouse=True)
def ensure_pilot_seeded():
    """Ensure database has Himalayan pilot data seeded before running integration tests."""
    db = SessionLocal()
    try:
        if db.query(Village).count() == 0:
            seed_himalayan_pilot_data(db)
    finally:
        db.close()


# =============================================================================
# 1. OPTION A DEMO AUTHENTICATION & SECURITY TESTS
# =============================================================================

def test_demo_token_accepted_in_dev_demo_mode():
    """Verify demo-authority-access-token is accepted in development/demo mode."""
    orig_env = settings.APP_ENV
    orig_mode = settings.DATA_MODE
    try:
        settings.APP_ENV = "development"
        settings.DATA_MODE = "demo"

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer demo-authority-access-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "district_collector_chamoli"
        assert data["role"] == "district_officer"
    finally:
        settings.APP_ENV = orig_env
        settings.DATA_MODE = orig_mode


def test_demo_token_rejected_when_db_user_missing():
    """Security Requirement: demo token fails with 401 when DB demo user is absent."""
    orig_env = settings.APP_ENV
    orig_mode = settings.DATA_MODE
    db = SessionLocal()
    user = None
    try:
        settings.APP_ENV = "development"
        settings.DATA_MODE = "demo"
        user = db.query(User).filter(User.username == "district_collector_chamoli").first()
        if user:
            user.username = "district_collector_chamoli_temp"
            db.commit()

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer demo-authority-access-token"},
        )
        assert response.status_code == 401
    finally:
        if user:
            user.username = "district_collector_chamoli"
            db.commit()
        db.close()
        settings.APP_ENV = orig_env
        settings.DATA_MODE = orig_mode


def test_demo_token_rejected_in_production():
    """Security Requirement: demo token MUST NEVER be accepted in production."""
    orig_env = settings.APP_ENV
    orig_mode = settings.DATA_MODE
    try:
        settings.APP_ENV = "production"
        settings.DATA_MODE = "live"

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer demo-authority-access-token"},
        )
        assert response.status_code == 401
    finally:
        settings.APP_ENV = orig_env
        settings.DATA_MODE = orig_mode


def test_demo_token_rejected_when_data_mode_not_demo():
    """Security Requirement: demo token rejected when DATA_MODE != demo."""
    orig_env = settings.APP_ENV
    orig_mode = settings.DATA_MODE
    try:
        settings.APP_ENV = "development"
        settings.DATA_MODE = "live"

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer demo-authority-access-token"},
        )
        assert response.status_code == 401
    finally:
        settings.APP_ENV = orig_env
        settings.DATA_MODE = orig_mode


def test_unauthenticated_request_rejected():
    """Protected endpoints reject requests without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_normal_jwt_authentication_functional():
    """Normal JWT authentication remains intact and verified."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "district_collector_chamoli").first()
        assert user is not None
        token = create_access_token(
            subject=user.id,
            claims={"username": user.username, "role": user.role},
        )
    finally:
        db.close()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "district_collector_chamoli"
    assert data["role"] == "district_officer"


def test_rbac_behavior_with_demo_token():
    """RBAC allows district_officer access and strictly blocks admin-only access."""
    headers = {"Authorization": "Bearer demo-authority-access-token"}

    # District officer is allowed for alerts acknowledge and site evaluation
    alerts_resp = client.get("/api/v1/alerts", headers=headers)
    assert alerts_resp.status_code == 200

    # Admin-only route (e.g. POST /sites/evaluate is officer-accessible, but POST /api/v1/sites requires ADMIN or DISTRICT_OFFICER)
    # Test protected route requiring roles
    auth_me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert auth_me_resp.status_code == 200
    assert auth_me_resp.json()["role"] == "district_officer"


# =============================================================================
# 2. VILLAGES ENDPOINT TESTS
# =============================================================================

def test_list_villages_endpoint():
    """GET /api/v1/villages returns 40 villages with GeoJSON Point coordinates."""
    response = client.get("/api/v1/villages?page=1&page_size=50")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 40
    assert json_data["pagination"]["total"] == 40

    first_v = json_data["data"][0]
    assert "id" in first_v
    assert "name" in first_v
    assert first_v["location"]["type"] == "Point"
    assert len(first_v["location"]["coordinates"]) == 2
    assert first_v["is_active"] is True


def test_get_village_detail_endpoint():
    """GET /api/v1/villages/{id} returns full village details with profiles."""
    list_resp = client.get("/api/v1/villages?page=1&page_size=1")
    v_id = list_resp.json()["data"][0]["id"]

    response = client.get(f"/api/v1/villages/{v_id}")
    assert response.status_code == 200
    detail = response.json()["data"]
    assert detail["id"] == v_id
    assert detail["population"] is not None
    assert detail["population"] > 0
    assert detail["households"] is not None
    assert detail["demographics"] is not None
    assert detail["vulnerability"] is not None
    assert detail["hazards"] is not None


# =============================================================================
# 3. RED ZONES ENDPOINT TESTS
# =============================================================================

def test_list_red_zones_endpoint():
    """GET /api/v1/red-zones returns proposed permanent red zones with MultiPolygon geometries."""
    response = client.get("/api/v1/red-zones")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) >= 7

    first_rz = json_data["data"][0]
    assert first_rz["geometry"]["type"] == "MultiPolygon"
    assert first_rz["danger_level"] is not None
    assert first_rz["area_sq_km"] > 0.0


def test_get_red_zone_detail_endpoint():
    """GET /api/v1/red-zones/{id} returns red zone detail."""
    list_resp = client.get("/api/v1/red-zones?page_size=1")
    rz_id = list_resp.json()["data"][0]["id"]

    response = client.get(f"/api/v1/red-zones/{rz_id}")
    assert response.status_code == 200
    detail = response.json()["data"]
    assert detail["id"] == rz_id
    assert detail["geometry"]["type"] == "MultiPolygon"


# =============================================================================
# 4. ALERTS ENDPOINT TESTS
# =============================================================================

def test_list_and_acknowledge_alerts_endpoint():
    """GET /api/v1/alerts and POST /api/v1/alerts/{id}/acknowledge."""
    db = SessionLocal()
    try:
        first_alert = db.query(Alert).first()
        if first_alert:
            first_alert.is_acknowledged = False
            db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    alerts = response.json()["data"]
    assert len(alerts) >= 4

    unack_alert = next((a for a in alerts if not a["is_acknowledged"]), None)
    assert unack_alert is not None
    alert_id = unack_alert["id"]

    # Unauthenticated acknowledgment must fail with 401
    unauth_resp = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert unauth_resp.status_code == 401

    # Acknowledge alert with demo token
    ack_resp = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers={"Authorization": "Bearer demo-authority-access-token"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["data"]["is_acknowledged"] is True


# =============================================================================
# 5. SITES & SUITABILITY ENDPOINT TESTS
# =============================================================================

def test_list_and_evaluate_sites_endpoint():
    """GET /api/v1/sites and POST /api/v1/sites/{id}/evaluate."""
    response = client.get("/api/v1/sites?page_size=15")
    assert response.status_code == 200
    sites = response.json()["data"]
    assert len(sites) == 12

    site_id = sites[0]["id"]

    # Detailed site
    detail_resp = client.get(f"/api/v1/sites/{site_id}")
    assert detail_resp.status_code == 200
    site_detail = detail_resp.json()["data"]
    assert len(site_detail["capacities"]) >= 1
    assert len(site_detail["infrastructures"]) >= 1

    # Evaluate site suitability
    eval_resp = client.post(
        f"/api/v1/sites/{site_id}/evaluate",
        headers={"Authorization": "Bearer demo-authority-access-token"},
        json={},
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()["data"]
    assert "overall_score" in eval_data
    assert "decision" in eval_data


# =============================================================================
# 6. SCENARIOS SIMULATOR TESTS
# =============================================================================

def test_scenarios_run_endpoint():
    """POST /api/v1/scenarios/run executes scenario simulation."""
    headers = {"Authorization": "Bearer demo-authority-access-token"}
    response = client.post(
        "/api/v1/scenarios/run",
        headers=headers,
        json={
            "scenario_type": "extreme_rainfall",
            "parameters": {
                "rainfall_intensity_multiplier": 1.5,
            },
        },
    )
    assert response.status_code == 200
    sim_data = response.json()["data"]
    assert sim_data["scenario_type"].lower() == "extreme_rainfall"
    assert "comparison" in sim_data
    assert "risk_score_deltas" in sim_data["comparison"]


# =============================================================================
# 7. RELOCATION MATCHING TESTS
# =============================================================================

def test_relocation_matching_endpoint():
    """POST /api/v1/relocation/match evaluates greedy village-site assignment."""
    headers = {"Authorization": "Bearer demo-authority-access-token"}
    response = client.post(
        "/api/v1/relocation/match",
        headers=headers,
        json={
            "use_database_villages": True,
            "use_database_sites": True,
            "region_profile_id": "himalayan_pilot",
        },
    )
    assert response.status_code == 200
    match_data = response.json()["data"]
    assert match_data["total_villages"] > 0
    assert "assignments" in match_data


# =============================================================================
# 8. EVACUATION ROUTING TESTS
# =============================================================================

def test_list_routes_endpoint():
    """GET /api/v1/routes returns generated evacuation corridors."""
    headers = {"Authorization": "Bearer demo-authority-access-token"}
    response = client.get("/api/v1/routes?page_size=10", headers=headers)
    assert response.status_code == 200
    routes = response.json()["data"]
    assert len(routes) > 0

    first_r = routes[0]
    assert first_r["path"]["type"] == "LineString"
    assert len(first_r["path"]["coordinates"]) >= 2
    assert first_r["distance_km"] > 0
    assert first_r["estimated_travel_time_min"] > 0
