"""Automated test suite for RakshakGIS Demo & Synthetic Datasets (Chunk M3-02)."""

import json
from pathlib import Path
import pytest

from app.data.synthetic import (
    DETERMINISTIC_SEED,
    PILOT_REGION_PROFILE_ID,
    build_synthetic_dataset,
    get_dataset_metadata,
    get_synthetic_candidate_sites_geojson,
    get_synthetic_hazard_events,
    get_synthetic_villages_geojson,
    load_himalayan_pilot_dataset,
)


def test_synthetic_dataset_loads_successfully():
    """Requirement 1: Dataset loads via loader and contains expected top-level structure."""
    dataset = load_himalayan_pilot_dataset()
    assert dataset is not None
    assert dataset.metadata is not None
    assert dataset.villages is not None
    assert dataset.candidate_sites is not None
    assert dataset.hazard_events is not None


def test_expected_counts_match_specification():
    """Requirement 2: Expected village count is 30–50 and candidate site count is 10–20."""
    dataset = load_himalayan_pilot_dataset()

    village_count = len(dataset.villages.features)
    site_count = len(dataset.candidate_sites.features)
    event_count = len(dataset.hazard_events)

    # Specification bounds: 30–50 villages (prefer ~40), 10–20 sites (prefer ~12)
    assert 30 <= village_count <= 50, f"Village count {village_count} out of range [30, 50]"
    assert village_count == 40

    assert 10 <= site_count <= 20, f"Site count {site_count} out of range [10, 20]"
    assert site_count == 12

    assert event_count == 30
    assert dataset.metadata.village_count == 40
    assert dataset.metadata.candidate_site_count == 12
    assert dataset.metadata.hazard_event_count == 30


def test_ids_are_unique_and_stable():
    """Requirement 3: Entity IDs are unique, non-empty, and strictly deterministic."""
    dataset = load_himalayan_pilot_dataset()

    village_ids = [f.properties.id for f in dataset.villages.features]
    assert len(village_ids) == len(set(village_ids)), "Duplicate village IDs found"
    assert all(vid.startswith("HIM-VILL-") for vid in village_ids)
    assert village_ids[0] == "HIM-VILL-001"
    assert village_ids[-1] == "HIM-VILL-040"

    site_ids = [f.properties.id for f in dataset.candidate_sites.features]
    assert len(site_ids) == len(set(site_ids)), "Duplicate candidate site IDs found"
    assert all(sid.startswith("HIM-SITE-") for sid in site_ids)
    assert site_ids[0] == "HIM-SITE-001"
    assert site_ids[-1] == "HIM-SITE-012"

    event_ids = [e.id for e in dataset.hazard_events]
    assert len(event_ids) == len(set(event_ids)), "Duplicate hazard event IDs found"
    assert all(eid.startswith("HIM-EVT-") for eid in event_ids)


def test_geospatial_coordinates_valid_and_in_pilot_bounding_box():
    """Requirement 4: Coordinates are valid geographic coordinates in Chamoli pilot bounds."""
    dataset = load_himalayan_pilot_dataset()
    bbox = dataset.metadata.geographic_bounding_box

    # Validate villages point coordinates
    for f in dataset.villages.features:
        assert f.geometry.type == "Point"
        lon, lat = f.geometry.coordinates
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0
        assert bbox["min_lon"] <= lon <= bbox["max_lon"], f"Village {f.properties.id} lon {lon} out of pilot bounds"
        assert bbox["min_lat"] <= lat <= bbox["max_lat"], f"Village {f.properties.id} lat {lat} out of pilot bounds"

    # Validate candidate sites polygon coordinates
    for f in dataset.candidate_sites.features:
        assert f.geometry.type == "Polygon"
        rings = f.geometry.coordinates
        assert len(rings) >= 1
        exterior = rings[0]
        assert len(exterior) >= 4, "Polygon must have at least 4 vertices"
        # Verify closed ring condition
        assert exterior[0] == exterior[-1], f"Polygon for {f.properties.id} is not a closed ring"
        for lon, lat in exterior:
            assert bbox["min_lon"] <= lon <= bbox["max_lon"]
            assert bbox["min_lat"] <= lat <= bbox["max_lat"]


def test_village_demographics_and_indicators_integrity():
    """Requirement 5: Demographic metrics are non-negative and physically logical."""
    dataset = load_himalayan_pilot_dataset()

    for f in dataset.villages.features:
        p = f.properties
        assert p.population > 0, f"Village {p.id} population must be positive"
        assert p.households > 0, f"Village {p.id} households must be positive"
        assert p.demographics.elderly_count >= 0
        assert p.demographics.children_count >= 0
        assert p.demographics.disabled_count >= 0
        assert p.demographics.livestock_count >= 0

        # Vulnerable segments cannot exceed total population
        assert (
            p.demographics.elderly_count + p.demographics.children_count
            <= p.population
        ), f"Village {p.id}: elderly + children exceeds total population"
        assert p.demographics.disabled_count <= p.population

        # Vulnerability indicators within [0.0, 1.0]
        v = p.vulnerability
        assert 0.0 <= v.social_vulnerability_index <= 1.0
        assert 0.0 <= v.economic_vulnerability_index <= 1.0
        assert 0.0 <= v.structural_vulnerability_index <= 1.0
        assert 0.0 <= v.road_connectivity_index <= 1.0
        assert 0.0 <= v.poverty_ratio <= 1.0
        assert 0.0 <= v.kuccha_housing_ratio <= 1.0

        # Physical hazard indicators
        h = p.hazards
        assert 800.0 <= h.elevation_m <= 3200.0
        assert 0.0 <= h.slope_deg <= 60.0
        assert h.historical_landslide_count >= 0
        assert h.distance_to_river_m >= 0.0


def test_hazard_events_reference_valid_villages_and_cover_all_hazards():
    """Requirement 6: Hazard events reference existing village IDs and cover all 4 hazard types."""
    dataset = load_himalayan_pilot_dataset()
    valid_village_ids = {f.properties.id for f in dataset.villages.features}

    seen_hazards = set()
    for e in dataset.hazard_events:
        assert e.village_id in valid_village_ids, f"Event {e.id} references non-existent village {e.village_id}"
        assert e.severity in {"low", "moderate", "high", "very_high", "critical"}
        assert e.intensity_value > 0.0
        assert len(e.observed_at) >= 19  # Valid ISO-8601 string
        seen_hazards.add(e.hazard_type)

    # Must cover all 4 required hazard categories
    assert "landslide" in seen_hazards
    assert "rainfall" in seen_hazards
    assert "seismic" in seen_hazards
    assert "flash_flood" in seen_hazards


def test_candidate_sites_contain_suitability_and_capacity_inputs():
    """Requirement 7: Candidate sites contain all required M4 suitability and capacity inputs."""
    dataset = load_himalayan_pilot_dataset()

    for f in dataset.candidate_sites.features:
        p = f.properties
        s = p.suitability
        c = p.capacity

        # Required suitability inputs
        assert s.area_sq_m > 0.0
        assert 0.0 <= s.terrain_slope_deg <= 90.0
        assert s.elevation_m > 0.0
        assert s.hazard_buffer_distance_m >= 0.0
        assert s.road_width_m > 0.0
        assert s.distance_to_highway_km >= 0.0
        assert s.water_supply_lpd_per_capita > 0.0
        assert s.water_source_distance_m >= 0.0
        assert s.distance_to_health_center_km >= 0.0
        assert s.distance_to_school_km >= 0.0
        assert s.distance_to_emergency_km >= 0.0
        assert s.distance_to_market_km >= 0.0
        assert s.distance_to_farmland_km >= 0.0
        assert s.livelihood_potential in {"high", "moderate", "low"}
        assert s.expansion_potential in {"high", "moderate", "low", "none"}

        # Required capacity inputs
        assert c.max_households > 0
        assert c.max_population > 0
        assert c.available_households == c.max_households
        assert c.available_population == c.max_population
        assert c.sanitation_units >= 0


def test_candidate_sites_contain_intentional_rejections_and_constraints():
    """Requirement 8: At least some candidate sites are intentionally unsuitable/constrained for M4 rejection testing."""
    dataset = load_himalayan_pilot_dataset()

    categories = [f.properties.suitability.suitability_category for f in dataset.candidate_sites.features]
    assert "suitable" in categories
    assert "rejected" in categories
    assert "constrained" in categories

    rejection_reasons = [
        f.properties.suitability.rejection_reason
        for f in dataset.candidate_sites.features
        if f.properties.suitability.suitability_category in {"rejected", "constrained"}
    ]
    assert len(rejection_reasons) >= 4

    # 1. Slope limit violation (> 15.0°)
    slope_violations = [
        f for f in dataset.candidate_sites.features
        if f.properties.suitability.terrain_slope_deg > 15.0
    ]
    assert len(slope_violations) >= 2, "Must contain at least 2 slope violation test cases"

    # 2. Hazard buffer violation (< 500.0m)
    buffer_violations = [
        f for f in dataset.candidate_sites.features
        if f.properties.suitability.hazard_buffer_distance_m < 500.0
    ]
    assert len(buffer_violations) >= 1, "Must contain at least 1 hazard buffer violation test case"

    # 3. Water supply deficit (< 70.0 LPD per capita standard)
    water_deficits = [
        f for f in dataset.candidate_sites.features
        if f.properties.suitability.water_supply_lpd_per_capita < 70.0
    ]
    assert len(water_deficits) >= 1, "Must contain at least 1 water deficit test case"

    # 4. Carrying capacity bottleneck
    bottlenecks = [
        f for f in dataset.candidate_sites.features
        if f.properties.capacity.max_households < 25
    ]
    assert len(bottlenecks) >= 1, "Must contain at least 1 capacity bottleneck test case"


def test_synthetic_provenance_and_disclaimer_present_on_all_entities():
    """Requirement 9: Provenance metadata explicitly declares synthetic / demo origin on all entities."""
    dataset = load_himalayan_pilot_dataset()

    # Metadata
    assert dataset.metadata.source_type == "synthetic"
    assert dataset.metadata.generator_seed == DETERMINISTIC_SEED
    assert dataset.metadata.pilot_region_profile == PILOT_REGION_PROFILE_ID
    assert "DEMO / SYNTHETIC" in dataset.metadata.disclaimer

    # Villages
    for f in dataset.villages.features:
        prov = f.properties.provenance
        assert prov.is_synthetic is True
        assert prov.data_source == "DEMO_SYNTHETIC_GENERATOR"
        assert prov.pilot_region == "himalayan_pilot"
        assert "DEMO / SYNTHETIC" in prov.disclaimer

    # Candidate Sites
    for f in dataset.candidate_sites.features:
        prov = f.properties.provenance
        assert prov.is_synthetic is True
        assert prov.data_source == "DEMO_SYNTHETIC_GENERATOR"
        assert prov.pilot_region == "himalayan_pilot"
        assert "DEMO / SYNTHETIC" in prov.disclaimer

    # Hazard Events
    for e in dataset.hazard_events:
        prov = e.provenance
        assert prov.is_synthetic is True
        assert prov.data_source == "DEMO_SYNTHETIC_GENERATOR"
        assert "DEMO / SYNTHETIC" in prov.disclaimer


def test_strict_generation_determinism_and_idempotency():
    """Requirement 10: Repeated generation produces bit-for-bit identical datasets."""
    dataset_1 = build_synthetic_dataset()
    dataset_2 = build_synthetic_dataset()

    dump_1 = dataset_1.model_dump_json(indent=2)
    dump_2 = dataset_2.model_dump_json(indent=2)

    assert dump_1 == dump_2, "Non-deterministic output detected across runs!"


def test_no_real_person_pii_in_dataset():
    """Requirement 11: Dataset contains no real personal names, phone numbers, or private PII."""
    dataset = load_himalayan_pilot_dataset()
    raw_text = dataset.model_dump_json().lower()

    # Verify absence of PII keywords and patterns
    pii_keywords = ["phone", "email", "aadhaar", "ssn", "mobile", "password", "pan_card"]
    for kw in pii_keywords:
        assert f'"{kw}"' not in raw_text, f"Potential PII keyword '{kw}' found in dataset dump"


def test_geojson_dictionary_access_helpers():
    """Requirement 12: High-level dictionary access helpers return valid GeoJSON structures."""
    villages_geojson = get_synthetic_villages_geojson()
    assert villages_geojson["type"] == "FeatureCollection"
    assert len(villages_geojson["features"]) == 40

    sites_geojson = get_synthetic_candidate_sites_geojson()
    assert sites_geojson["type"] == "FeatureCollection"
    assert len(sites_geojson["features"]) == 12

    events_list = get_synthetic_hazard_events()
    assert isinstance(events_list, list)
    assert len(events_list) == 30

    meta = get_dataset_metadata()
    assert meta["dataset_id"] == "rakshakgis_himalayan_pilot_v1"
    assert meta["pilot_region_profile"] == "himalayan_pilot"
