"""Automated unit and API integration tests for candidate relocation sites (M4-01)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from app.main import app
from app.core.database import get_db
from app.api.deps import UserRole, get_current_user
from app.models.governance import User
from app.models.geographic import District
from app.models.relocation import CandidateSite, SiteCapacity, Infrastructure
from app.schemas.sites import GeoJSONPoint, GeoJSONPolygon
from app.core.security import create_access_token


def make_mock_site(
    site_id: int = 1,
    name: str = "Safe Ridge Site 1",
    district_id: int = 101,
    status: str = "proposed",
    elevation_m: float = 500.0,
    area_sq_m: float = 10000.0,
    terrain_slope_deg: float = 5.0,
):
    """Helper to construct a mock CandidateSite model instance."""
    site = CandidateSite(
        id=site_id,
        name=name,
        district_id=district_id,
        location=GeoJSONPoint(type="Point", coordinates=(78.1, 30.1)),
        boundary=GeoJSONPolygon(
            type="Polygon",
            coordinates=[[[78.1, 30.1], [78.11, 30.1], [78.11, 30.11], [78.1, 30.11], [78.1, 30.1]]],
        ),
        area_sq_m=area_sq_m,
        terrain_slope_deg=terrain_slope_deg,
        elevation_m=elevation_m,
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    site.capacities = [
        SiteCapacity(
            id=1,
            site_id=site_id,
            max_households=100,
            max_population=500,
            allocated_households=0,
            allocated_population=0,
            available_households=100,
            available_population=500,
            water_supply_lpd=50000.0,
            sanitation_units=20,
            updated_at=datetime.now(timezone.utc),
        )
    ]
    infra_infra = Infrastructure(
        id=1,
        site_id=site_id,
        name="Primary Helipad",
        infra_type="helipad",
        status="operational",
        location=GeoJSONPoint(type="Point", coordinates=(78.105, 30.105)),
        capacity_description="Supports heavy transport helicopters",
        created_at=datetime.now(timezone.utc),
    )
    site.infrastructures = [infra_infra]
    return site


@pytest.fixture
def mock_db():
    """Provide a mocked SQLAlchemy database session."""
    session = MagicMock()
    return session


@pytest.fixture
def admin_user():
    """Mock Admin User model instance."""
    return User(
        id=1,
        username="test_admin",
        email="admin@rakshakgis.gov.in",
        hashed_password="hash",
        full_name="Admin Officer",
        role=UserRole.ADMIN.value,
        is_active=True,
    )


@pytest.fixture
def viewer_user():
    """Mock Viewer User model instance."""
    return User(
        id=2,
        username="test_viewer",
        email="viewer@rakshakgis.gov.in",
        hashed_password="hash",
        full_name="Viewer User",
        role=UserRole.VIEWER.value,
        is_active=True,
    )


@pytest.fixture
def admin_headers(admin_user):
    """Auth headers containing access token for Admin user."""
    token = create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(viewer_user):
    """Auth headers containing access token for Viewer user."""
    token = create_access_token(subject=viewer_user.id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Unit & Endpoint Tests for Candidate Relocation Sites
# ==============================================================================


def test_list_candidate_sites_empty(client, mock_db):
    """Test GET /api/v1/sites when no sites exist in database."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sites")
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["pagination"]["total"] == 0
        assert res["pagination"]["page"] == 1
        assert res["pagination"]["page_size"] == 20
        assert res["pagination"]["total_pages"] == 1
        assert res["data"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_list_candidate_sites_with_data_and_pagination(client, mock_db):
    """Test GET /api/v1/sites returning paginated items and spatial GeoJSON Point conversion."""
    site1 = make_mock_site(1, "Safe Ridge Site 1")
    site2 = make_mock_site(2, "Safe Ridge Site 2")

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = 2
    mock_query.all.return_value = [site1, site2]
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sites?page=1&page_size=2")
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["pagination"]["total"] == 2
        assert len(res["data"]) == 2
        assert res["data"][0]["name"] == "Safe Ridge Site 1"
        assert res["data"][0]["location"]["type"] == "Point"
        assert res["data"][0]["location"]["coordinates"] == [78.1, 30.1]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_list_candidate_sites_supported_filters(client, mock_db):
    """Test GET /api/v1/sites with domain filters (district, status, elevation, area, search)."""
    site = make_mock_site(10, "Hilltop Safe Zone", district_id=5, status="active", elevation_m=1200.0)

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [site]
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        url = "/api/v1/sites?district_id=5&status=active&min_elevation_m=1000&max_elevation_m=1500&search=Hilltop"
        response = client.get(url)
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert len(res["data"]) == 1
        assert res["data"][0]["name"] == "Hilltop Safe Zone"
        assert res["data"][0]["status"] == "active"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_candidate_site_by_id_success(client, mock_db):
    """Test GET /api/v1/sites/{id} retrieving detailed site with loaded relationships."""
    site = make_mock_site(42, "Valley Safe Site Alpha")

    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = site
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sites/42")
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        data = res["data"]
        assert data["id"] == 42
        assert data["name"] == "Valley Safe Site Alpha"
        assert data["location"]["type"] == "Point"
        assert data["boundary"]["type"] == "Polygon"
        assert len(data["capacities"]) == 1
        assert data["capacities"][0]["max_households"] == 100
        assert len(data["infrastructures"]) == 1
        assert data["infrastructures"][0]["name"] == "Primary Helipad"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_candidate_site_by_id_not_found(client, mock_db):
    """Test GET /api/v1/sites/{id} returns HTTP 404 NotFoundError for non-existent ID."""
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sites/999999")
        assert response.status_code == 404
        res = response.json()
        assert res["success"] is False
        assert res["error"]["code"] == "NOT_FOUND"
        assert res["error"]["status_code"] == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_candidate_site_authorized(client, mock_db, admin_user, admin_headers):
    """Test POST /api/v1/sites creates a candidate site when authorized."""
    district = District(id=10, code="DIST10", name="Test District", region_id=1)
    new_site = make_mock_site(100, "New Resilient Shelter Site", district_id=10)

    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = admin_user

    mock_district_query = MagicMock()
    mock_district_query.filter.return_value.first.return_value = district

    mock_site_query = MagicMock()
    mock_site_query.options.return_value = mock_site_query
    mock_site_query.filter.return_value.first.return_value = new_site

    def query_side_effect(model):
        if model == User:
            return mock_user_query
        elif model == District:
            return mock_district_query
        return mock_site_query

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "name": "New Resilient Shelter Site",
            "district_id": 10,
            "location": {"type": "Point", "coordinates": [78.22, 30.33]},
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [[78.22, 30.33], [78.23, 30.33], [78.23, 30.34], [78.22, 30.34], [78.22, 30.33]]
                ],
            },
            "area_sq_m": 12000.0,
            "terrain_slope_deg": 5.2,
            "elevation_m": 600.0,
            "status": "proposed",
        }
        response = client.post("/api/v1/sites", json=payload, headers=admin_headers)
        assert response.status_code == 201
        res = response.json()
        assert res["success"] is True
        assert res["data"]["name"] == "New Resilient Shelter Site"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_candidate_site_unauthorized(client):
    """Test POST /api/v1/sites without authentication returns HTTP 401 Unauthorized."""
    payload = {
        "name": "Unauthorized Site Attempt",
        "district_id": 10,
        "location": {"type": "Point", "coordinates": [78.1, 30.1]},
    }
    response = client.post("/api/v1/sites", json=payload)
    assert response.status_code == 401
    res = response.json()
    assert res["success"] is False
    assert res["error"]["code"] == "UNAUTHORIZED"


def test_create_candidate_site_forbidden_role(client, mock_db, viewer_user, viewer_headers):
    """Test POST /api/v1/sites with insufficient role (Viewer) returns HTTP 403 Forbidden."""
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = viewer_user
    mock_db.query.return_value = mock_user_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "name": "Forbidden Site Attempt",
            "district_id": 10,
            "location": {"type": "Point", "coordinates": [78.1, 30.1]},
        }
        response = client.post("/api/v1/sites", json=payload, headers=viewer_headers)
        assert response.status_code == 403
        res = response.json()
        assert res["success"] is False
        assert res["error"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_candidate_site_nonexistent_district(client, mock_db, admin_user, admin_headers):
    """Test POST /api/v1/sites with non-existent district returns HTTP 404 NotFoundError."""
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = admin_user

    mock_district_query = MagicMock()
    mock_district_query.filter.return_value.first.return_value = None

    def query_side_effect(model):
        if model == User:
            return mock_user_query
        return mock_district_query

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "name": "Invalid District Site",
            "district_id": 999999,
            "location": {"type": "Point", "coordinates": [78.1, 30.1]},
        }
        response = client.post("/api/v1/sites", json=payload, headers=admin_headers)
        assert response.status_code == 404
        res = response.json()
        assert res["success"] is False
        assert res["error"]["code"] == "NOT_FOUND"
        assert res["error"]["status_code"] == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_candidate_site_invalid_spatial_geometry(client, mock_db, admin_user, admin_headers):
    """Test POST /api/v1/sites rejects out-of-bounds coordinates or unclosed polygons (422)."""
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = admin_user
    mock_db.query.return_value = mock_user_query

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Out-of-bounds longitude (200.0)
        payload_bad_coord = {
            "name": "Out of Bounds Site",
            "district_id": 10,
            "location": {"type": "Point", "coordinates": [200.0, 30.0]},
        }
        res1 = client.post("/api/v1/sites", json=payload_bad_coord, headers=admin_headers)
        assert res1.status_code == 422

        # Unclosed polygon ring
        payload_unclosed_poly = {
            "name": "Unclosed Polygon Site",
            "district_id": 10,
            "location": {"type": "Point", "coordinates": [78.0, 30.0]},
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [[78.0, 30.0], [78.1, 30.0], [78.1, 30.1], [78.0, 30.2]]  # Unclosed!
                ],
            },
        }
        res2 = client.post("/api/v1/sites", json=payload_unclosed_poly, headers=admin_headers)
        assert res2.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_update_candidate_site_authorized(client, mock_db, admin_user, admin_headers):
    """Test PATCH /api/v1/sites/{id} partially updates site attributes."""
    existing_site = make_mock_site(5, "Original Site Name")

    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = admin_user

    mock_site_query = MagicMock()
    mock_site_query.filter.return_value.first.return_value = existing_site
    mock_site_query.options.return_value = mock_site_query

    def query_side_effect(model):
        if model == User:
            return mock_user_query
        return mock_site_query

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "name": "Updated Safe Zone Beta",
            "status": "approved",
            "elevation_m": 750.0,
        }
        response = client.patch("/api/v1/sites/5", json=payload, headers=admin_headers)
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["data"]["id"] == 5
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_delete_candidate_site_authorized(client, mock_db, admin_user, admin_headers):
    """Test DELETE /api/v1/sites/{id} deletes candidate site when authorized."""
    existing_site = make_mock_site(12, "Site To Delete")

    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = admin_user

    mock_site_query = MagicMock()
    mock_site_query.filter.return_value.first.return_value = existing_site

    def query_side_effect(model):
        if model == User:
            return mock_user_query
        return mock_site_query

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.delete("/api/v1/sites/12", headers=admin_headers)
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["data"]["deleted"] is True
        assert res["data"]["id"] == 12
    finally:
        app.dependency_overrides.pop(get_db, None)
