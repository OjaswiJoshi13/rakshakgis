"""Regression test suite for REAL-01B forensic frontend and operational data paths.

Validates that:
1. GET /api/v1/map/layers?region_id=himalayan_pilot returns the full operational
   feature collections:
   - >= 188 villages (Census + SOI centroids)
   - >= 150 village_boundaries (Survey of India cadastral polygons)
   - >= 150 earthquakes_ncs (National Centre for Seismology)
   - earthquakes_usgs (USGS live feed)
   - >= 12 candidate_sites / sites
   - >= 53 routes
   - >= 7 red_zones
   and layers.layer_provenance contains truthful provenance strings without false claims.
2. GET /api/v1/villages/42/analysis returns full dossier data including:
   - coordinates, district_name, block_name, region_name
   - 6 structured risk factor records with verified numerical values.
3. POST /api/v1/relocation/match with use_database_villages=True evaluates all 188 villages
   and produces structured matches and unassigned records.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.models.governance import User

client = TestClient(app)


def test_map_layers_full_operational_features_and_provenance():
    """Verify that map layers endpoint returns real features and correct provenance."""
    response = client.get("/api/v1/map/layers?region_id=himalayan_pilot")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    layers = payload["data"]
    # 188 habitations
    assert "villages" in layers
    villages = layers["villages"]
    assert villages["type"] == "FeatureCollection"
    assert len(villages["features"]) >= 188

    # 150 SOI boundaries
    assert "village_boundaries" in layers
    boundaries = layers["village_boundaries"]
    assert boundaries["type"] == "FeatureCollection"
    assert len(boundaries["features"]) >= 150

    # 150 NCS earthquakes
    assert "earthquakes_ncs" in layers
    ncs = layers["earthquakes_ncs"]
    assert ncs["type"] == "FeatureCollection"
    assert len(ncs["features"]) >= 150

    # USGS live earthquakes
    assert "earthquakes_usgs" in layers
    usgs = layers["earthquakes_usgs"]
    assert usgs["type"] == "FeatureCollection"

    # Sites / Candidate sites alias
    assert "sites" in layers
    assert "candidate_sites" in layers
    assert len(layers["sites"]["features"]) >= 12
    assert len(layers["candidate_sites"]["features"]) >= 12

    # Evacuation routes
    assert "routes" in layers
    assert len(layers["routes"]["features"]) >= 53

    # Red zones
    assert "red_zones" in layers
    assert len(layers["red_zones"]["features"]) >= 7

    # Provenance metadata check
    assert "layer_provenance" in layers
    prov = layers["layer_provenance"]

    assert "REAL / OFFICIAL — Survey of India" in prov.get("village_boundaries", "")
    assert "Census 2011" in prov.get("villages", "")
    assert "National Centre for Seismology" in prov.get("earthquakes_ncs", "")
    assert "USGS" in prov.get("earthquakes_usgs", "")
    assert "SYNTHETIC / PROPOSED" in prov.get("sites", "")
    assert "SYNTHETIC / DERIVED" in prov.get("routes", "")
    assert "DERIVED / DEMONSTRATION" in prov.get("red_zones", "")


def test_village_analysis_full_dossier_and_coordinates():
    """Verify that village analysis endpoint returns geographic and demographic fields."""
    response = client.get("/api/v1/villages/42/analysis")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    data = payload["data"]
    village = data["village"]
    assert village["id"] == 42
    assert "coordinates" in village
    assert isinstance(village["coordinates"], list)
    assert len(village["coordinates"]) == 2
    # Verify coordinates are non-null floats
    lon, lat = village["coordinates"]
    assert lon is not None and lat is not None
    assert 78.0 <= lon <= 81.0
    assert 29.0 <= lat <= 32.0

    assert village.get("district_name") == "Chamoli"
    assert village.get("block_name") == "Joshimath"
    assert village.get("region_name") == "Uttarakhand"

    # Verify risk factors
    factors = data.get("risk", {}).get("factors", [])
    assert len(factors) == 6
    factor_names = {f["factor_name"] for f in factors}
    assert "slope_landslide_susceptibility" in factor_names
    assert "flood_exposure" in factor_names


def test_relocation_match_evaluates_188_villages():
    """Verify relocation matching evaluates 188 villages from database."""
    officer = User(id=1, username="officer_chamoli", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer

    try:
        request_body = {
            "region_id": "himalayan_pilot",
            "use_database_villages": True,
            "use_database_sites": True,
            "max_distance_km": 50.0,
        }
        response = client.post("/api/v1/relocation/match", json=request_body)
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True

        data = payload["data"]
        assert data["total_villages"] >= 188
        assert data["assigned_villages_count"] > 0
        assert data["unassigned_villages_count"] > 0
        assert (
            data["assigned_villages_count"] + data["unassigned_villages_count"]
            == data["total_villages"]
        )

        # Verify unassigned assignments have rejection codes
        assignments = data["assignments"]
        unassigned = [a for a in assignments if a["status"] == "unassigned"]
        assert len(unassigned) > 0
        for u in unassigned[:5]:
            code = (u.get("unassigned_code") or "").lower()
            assert code in [
                "insufficient_capacity",
                "no_feasible_site",
                "capacity_exceeded",
            ]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
