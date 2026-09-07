"""Tests for newly implemented REST endpoints across regions, risk, GIS, governance, and reports."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_regions_endpoint():
    """GET /api/v1/regions returns configured regions."""
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    reg = data["data"][0]
    assert "id" in reg
    assert "code" in reg
    assert "name" in reg
    assert "village_count" in reg


def test_get_region_detail_endpoint():
    """GET /api/v1/regions/{id} returns region detail."""
    response = client.get("/api/v1/regions/uttarakhand_himalayan")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["code"] == "uttarakhand_himalayan"
    assert "districts" in data["data"]


def test_map_layers_endpoint():
    """GET /api/v1/map/layers returns GeoJSON FeatureCollections."""
    response = client.get("/api/v1/map/layers")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    layers = data["data"]
    assert "villages" in layers
    assert layers["villages"]["type"] == "FeatureCollection"
    assert "red_zones" in layers
    assert "sites" in layers
    assert "hazards" in layers


def test_village_risk_and_analysis_endpoints():
    """GET /api/v1/villages/{id}/risk and /analysis return structured assessment."""
    # Find a village first
    v_resp = client.get("/api/v1/villages?page=1&page_size=1")
    assert v_resp.status_code == 200
    v_list = v_resp.json()["data"]
    assert len(v_list) > 0
    village_id = v_list[0]["id"]

    # 1. Test /risk
    risk_resp = client.get(f"/api/v1/villages/{village_id}/risk")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()
    assert risk_data["success"] is True
    assert "risk_score" in risk_data["data"]
    assert "factors" in risk_data["data"]

    # 2. Test /analysis
    analysis_resp = client.get(f"/api/v1/villages/{village_id}/analysis")
    assert analysis_resp.status_code == 200
    analysis_data = analysis_resp.json()
    assert analysis_data["success"] is True
    assert "village" in analysis_data["data"]
    assert "population" in analysis_data["data"]
    assert "vulnerability" in analysis_data["data"]
    assert "risk" in analysis_data["data"]
    assert "red_zone" in analysis_data["data"]


def test_risk_summary_and_recalculate():
    """GET /api/v1/risk/summary and POST /api/v1/risk/recalculate execute correctly."""
    # Summary
    sum_resp = client.get("/api/v1/risk/summary")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert sum_data["success"] is True
    assert "total_villages_assessed" in sum_data["data"]
    assert "risk_distribution" in sum_data["data"]

    # Recalculate
    recalc_resp = client.post(
        "/api/v1/risk/recalculate",
        json={
            "region_id": "himalayan_pilot",
            "rainfall_multiplier": 1.5,
            "flood_surge_mm": 50.0,
        },
    )
    assert recalc_resp.status_code == 200
    recalc_data = recalc_resp.json()
    assert recalc_data["success"] is True
    assert recalc_data["data"]["villages_recomputed"] > 0


def test_gis_search_endpoint():
    """GET /api/v1/gis/search returns matches across entities."""
    response = client.get("/api/v1/gis/search?q=Joshimath")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    first_result = data["data"][0]
    assert "entity_type" in first_result
    assert "name" in first_result


def test_governance_and_audit_endpoints():
    """POST and GET /api/v1/governance/decisions and GET /api/v1/audit/logs."""
    # 1. Post decision
    post_resp = client.post(
        "/api/v1/governance/decisions",
        json={
            "decision_type": "evacuation_order",
            "target_entity_type": "village",
            "target_entity_id": 42,
            "action_taken": "Issued Pre-emptive Evacuation Warning",
            "rationale": "Extreme rainfall alert exceeds dynamic safety threshold.",
            "overridden_recommendation": False,
        },
    )
    assert post_resp.status_code == 201
    post_data = post_resp.json()
    assert post_data["success"] is True
    assert "id" in post_data["data"]

    # 2. List decisions
    list_resp = client.get("/api/v1/governance/decisions")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["success"] is True
    assert len(list_data["data"]) >= 1

    # 3. List audit logs
    audit_resp = client.get("/api/v1/audit/logs")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["success"] is True
    assert len(audit_data["data"]) >= 1


def test_reports_endpoints():
    """GET /api/v1/reports/{type} generates structured reports."""
    for r_type in ["action_plan", "risk_assessment", "site_dossier", "audit_report"]:
        resp = client.get(f"/api/v1/reports/{r_type}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["report_type"] == r_type
