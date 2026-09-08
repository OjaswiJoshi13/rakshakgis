"""Unit and integration tests for semantic region resolution, real GIS layers, and DB-backed relocation matching."""

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.regions import resolve_region_scope, apply_region_scope_to_village_query
from app.models.geographic import Village
from app.main import app

client = TestClient(app)


def test_resolve_region_scope_himalayan_pilot():
    """Verify himalayan_pilot alias resolves to Uttarakhand/Chamoli scope."""
    db = SessionLocal()
    try:
        scope = resolve_region_scope(db, "himalayan_pilot")
        assert scope is not None
        assert scope.is_empty is False
        assert len(scope.district_ids) >= 1
        assert len(scope.region_ids) >= 1
    finally:
        db.close()


def test_resolve_region_scope_empty_or_none():
    """Verify None and empty strings return None scope (no filtering)."""
    db = SessionLocal()
    try:
        assert resolve_region_scope(db, None) is None
        assert resolve_region_scope(db, "") is None
        assert resolve_region_scope(db, "   ") is None
    finally:
        db.close()


def test_resolve_region_scope_unrecognized():
    """Verify unrecognized region identifier returns is_empty=True without leaking data."""
    db = SessionLocal()
    try:
        scope = resolve_region_scope(db, "nonexistent_antarctica_zone")
        assert scope is not None
        assert scope.is_empty is True
        assert len(scope.region_ids) == 0
        assert len(scope.district_ids) == 0

        # When applied to query, should return exactly 0 records
        q = db.query(Village)
        q = apply_region_scope_to_village_query(q, scope)
        assert q.count() == 0
    finally:
        db.close()


def test_map_layers_himalayan_pilot_real_data():
    """GET /api/v1/map/layers?region_id=himalayan_pilot returns real GIS layers."""
    response = client.get("/api/v1/map/layers?region_id=himalayan_pilot")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    layers = data["data"]
    # 188 habitations
    assert "villages" in layers
    assert len(layers["villages"]["features"]) >= 40

    # 150 Survey of India cadastral boundary polygons
    assert "village_boundaries" in layers
    assert len(layers["village_boundaries"]["features"]) >= 140

    # NCS Official Seismology catalog earthquakes
    assert "earthquakes_ncs" in layers
    assert len(layers["earthquakes_ncs"]["features"]) >= 100

    # USGS Real-Time earthquakes
    assert "earthquakes_usgs" in layers
    assert layers["earthquakes_usgs"]["type"] == "FeatureCollection"


def test_villages_himalayan_pilot_endpoint():
    """GET /api/v1/villages?region_id=himalayan_pilot returns full pilot habitations."""
    response = client.get("/api/v1/villages?region_id=himalayan_pilot&page=1&page_size=100")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["pagination"]["total"] == 188
    assert len(data["data"]) == 100


def test_risk_summary_himalayan_pilot_endpoint():
    """GET /api/v1/risk/summary?region_id=himalayan_pilot assesses all 188 villages."""
    response = client.get("/api/v1/risk/summary?region_id=himalayan_pilot")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    summary = data["data"]
    assert summary["total_villages_assessed"] == 188
    assert summary["total_population"] > 50000
    assert summary["average_risk_score"] > 0.0


def test_relocation_matching_database_backed():
    """POST /api/v1/relocation/match with DB data evaluates 188 villages and assigns feasible havens."""
    from app.core.security import create_access_token
    from app.models.governance import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "district_collector_chamoli").first()
        if not user:
            user = db.query(User).first()
        token = create_access_token(subject=user.id)
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "use_database_villages": True,
        "use_database_sites": True,
        "region_profile_id": "himalayan_pilot",
    }
    response = client.post("/api/v1/relocation/match", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert "assignments" in result
    assert len(result["assignments"]) == 188

    assigned = [a for a in result["assignments"] if a["status"] == "assigned"]
    unassigned = [a for a in result["assignments"] if a["status"] == "unassigned"]

    assert len(assigned) > 0, "At least one village should be assigned to candidate havens"
    assert len(unassigned) > 0, "Capacity-constrained villages should be marked unassigned"

    # Verify unassigned items have statutory rejection reasons and codes
    first_unassigned = unassigned[0]
    assert first_unassigned["unassigned_code"] is not None
    assert first_unassigned["unassigned_reason"] is not None
