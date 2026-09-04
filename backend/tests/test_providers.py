"""Automated test suite for RakshakGIS Data Provider Contracts & Adapters (Chunk M3-03)."""

import pytest
from app.data.providers import (
    BaseDataProvider,
    MockFloodProvider,
    MockHazardObservationProvider,
    MockLandslideProvider,
    MockPopulationExposureProvider,
    MockRainfallProvider,
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderHealth,
    ProviderMode,
    ProviderNotFoundError,
    ProviderQuery,
    ProviderRegistry,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
    get_provider,
    get_provider_by_id,
    list_provider_ids,
    list_providers,
)


def test_provider_registry_initializes_with_all_mock_adapters():
    """Requirement 1: Registry discovers and registers standard mock providers."""
    providers = list_providers()
    assert len(providers) >= 5

    provider_ids = list_provider_ids()
    assert "mock_imd_rainfall" in provider_ids
    assert "mock_cwc_flood" in provider_ids
    assert "mock_gsi_landslide" in provider_ids
    assert "mock_multi_hazard_telemetry" in provider_ids
    assert "mock_census_demographics" in provider_ids


def test_provider_contract_attributes_and_mode():
    """Requirement 2: Provider contract properties are exposed correctly."""
    rainfall_p = get_provider_by_id("mock_imd_rainfall")
    assert rainfall_p.provider_id == "mock_imd_rainfall"
    assert "IMD" in rainfall_p.provider_name
    assert SourceCategory.RAINFALL in rainfall_p.supported_categories
    assert "himalayan_pilot" in rainfall_p.supported_regions
    assert rainfall_p.mode == ProviderMode.MOCK
    assert rainfall_p.check_health() == ProviderHealth.HEALTHY


def test_mock_rainfall_provider_returns_deterministic_data():
    """Requirement 3: Mock rainfall provider fetches and normalizes precipitation records."""
    rainfall_p = get_provider(SourceCategory.RAINFALL)
    query = ProviderQuery(
        category=SourceCategory.RAINFALL,
        region_id="himalayan_pilot",
    )

    response = rainfall_p.fetch_data(query)
    assert response is not None
    assert response.provider_id == "mock_imd_rainfall"
    assert response.category == SourceCategory.RAINFALL
    assert response.total_count == 8  # 8 synthetic rainfall events
    assert len(response.records) == 8

    # Verify typed record properties
    for rec in response.records:
        assert isinstance(rec, NormalizedRainfallRecord)
        assert rec.rainfall_24h_mm > 0.0
        assert rec.village_id is not None
        assert rec.village_id.startswith("HIM-VILL-")
        assert len(rec.location_coordinates) == 2
        assert rec.is_heavy_rain == (rec.rainfall_24h_mm >= 64.5)
        assert rec.is_very_heavy_rain == (rec.rainfall_24h_mm >= 115.5)
        assert rec.provenance.is_synthetic is True
        assert rec.provenance.provider_id == "mock_imd_rainfall"


def test_mock_rainfall_provider_filters():
    """Requirement 4: Mock rainfall provider respects village and date range filters."""
    rainfall_p = get_provider(SourceCategory.RAINFALL)

    # Village filter
    query_village = ProviderQuery(
        category=SourceCategory.RAINFALL,
        village_id="HIM-VILL-002",  # Ravigram
    )
    resp_v = rainfall_p.fetch_data(query_village)
    assert resp_v.total_count == 1
    assert resp_v.records[0].village_id == "HIM-VILL-002"
    assert resp_v.records[0].village_name == "Ravigram"
    assert resp_v.records[0].rainfall_24h_mm == 142.5

    # Limit filter
    query_limit = ProviderQuery(
        category=SourceCategory.RAINFALL,
        limit=3,
    )
    resp_l = rainfall_p.fetch_data(query_limit)
    assert resp_l.total_count == 3
    assert len(resp_l.records) == 3


def test_mock_flood_provider_returns_normalized_records():
    """Requirement 5: Mock flood provider fetches and normalizes hydrological records."""
    flood_p = get_provider(SourceCategory.FLOOD)
    query = ProviderQuery(category=SourceCategory.FLOOD)

    response = flood_p.fetch_data(query)
    assert response.total_count == 6
    assert len(response.records) == 6

    for rec in response.records:
        assert isinstance(rec, NormalizedFloodRecord)
        assert rec.water_level_m_above_danger > 0.0
        assert rec.flood_type == "flash_flood"
        assert rec.severity in {"moderate", "high", "very_high", "critical"}
        assert rec.village_id is not None


def test_mock_landslide_provider_returns_normalized_records():
    """Requirement 6: Mock landslide provider fetches and normalizes slope failure records."""
    landslide_p = get_provider(SourceCategory.LANDSLIDE)
    query = ProviderQuery(category=SourceCategory.LANDSLIDE)

    response = landslide_p.fetch_data(query)
    assert response.total_count == 10
    assert len(response.records) == 10

    for rec in response.records:
        assert isinstance(rec, NormalizedLandslideRecord)
        assert rec.debris_volume_cu_m > 0.0
        assert isinstance(rec.road_blocked, bool)
        assert rec.provenance.is_synthetic is True


def test_mock_multi_hazard_telemetry_provider():
    """Requirement 7: Mock hazard telemetry provider returns multi-hazard stream."""
    haz_p = get_provider(SourceCategory.HAZARD_OBSERVATION)
    query = ProviderQuery(category=SourceCategory.HAZARD_OBSERVATION)

    response = haz_p.fetch_data(query)
    assert response.total_count == 30

    hazard_types = {r.hazard_type for r in response.records}
    assert "landslide" in hazard_types
    assert "rainfall" in hazard_types
    assert "seismic" in hazard_types
    assert "flash_flood" in hazard_types

    for rec in response.records:
        assert isinstance(rec, NormalizedHazardObservationRecord)
        assert rec.intensity_value > 0.0
        assert rec.intensity_unit is not None


def test_mock_population_exposure_provider():
    """Requirement 8: Mock population provider fetches normalized demographic records."""
    pop_p = get_provider(SourceCategory.POPULATION_EXPOSURE)
    query = ProviderQuery(category=SourceCategory.POPULATION_EXPOSURE)

    response = pop_p.fetch_data(query)
    assert response.total_count == 40

    for rec in response.records:
        assert isinstance(rec, NormalizedPopulationRecord)
        assert rec.total_population > 0
        assert rec.households > 0
        assert rec.elderly_count + rec.children_count <= rec.total_population
        assert rec.district_code == "chamoli"
        assert rec.provenance.is_synthetic is True


def test_repeated_queries_are_strictly_idempotent():
    """Requirement 9: Identical queries produce bit-for-bit identical outputs."""
    rainfall_p = get_provider(SourceCategory.RAINFALL)
    query = ProviderQuery(category=SourceCategory.RAINFALL)

    resp1 = rainfall_p.fetch_data(query)
    resp2 = rainfall_p.fetch_data(query)

    assert resp1.model_dump_json() == resp2.model_dump_json()


def test_unsupported_category_raises_explicit_error():
    """Requirement 10: Requesting an unsupported category raises UnsupportedQueryError."""
    rainfall_p = MockRainfallProvider()
    bad_query = ProviderQuery(category=SourceCategory.FLOOD)

    with pytest.raises(UnsupportedQueryError) as exc_info:
        rainfall_p.fetch_data(bad_query)

    assert "does not support category 'flood'" in str(exc_info.value)
    assert exc_info.value.provider_id == "mock_imd_rainfall"


def test_unsupported_region_raises_explicit_error():
    """Requirement 11: Requesting an unsupported region raises UnsupportedQueryError."""
    rainfall_p = MockRainfallProvider()
    bad_query = ProviderQuery(
        category=SourceCategory.RAINFALL,
        region_id="unsupported_coastal_region",
    )

    with pytest.raises(UnsupportedQueryError) as exc_info:
        rainfall_p.fetch_data(bad_query)

    assert "does not support region 'unsupported_coastal_region'" in str(exc_info.value)


def test_provider_unavailable_behavior():
    """Requirement 12: An offline or degraded provider raises ProviderUnavailableError."""
    offline_p = MockRainfallProvider(is_healthy=False)
    assert offline_p.check_health() == ProviderHealth.UNAVAILABLE

    query = ProviderQuery(category=SourceCategory.RAINFALL)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        offline_p.fetch_data(query)

    assert "currently unavailable/offline" in str(exc_info.value)
    assert exc_info.value.provider_id == "mock_imd_rainfall"


def test_unknown_provider_id_raises_provider_not_found():
    """Requirement 13: Querying an unregistered provider ID raises ProviderNotFoundError."""
    with pytest.raises(ProviderNotFoundError):
        get_provider_by_id("non_existent_provider_id")


def test_provider_registry_isolation():
    """Requirement 14: Custom registry instances can be created without affecting global state."""
    custom_registry = ProviderRegistry(load_defaults=False)
    assert custom_registry.count() == 0
    assert custom_registry.list_provider_ids() == []

    # Register only rainfall
    custom_registry.register(MockRainfallProvider())
    assert custom_registry.count() == 1
    assert custom_registry.get_by_category(SourceCategory.RAINFALL) is not None

    with pytest.raises(ProviderNotFoundError):
        custom_registry.get_by_category(SourceCategory.FLOOD)

    # Global registry is unaffected
    assert len(list_provider_ids()) >= 5


def test_no_real_person_pii_in_provider_responses():
    """Requirement 15: Mock responses contain zero real-person PII."""
    for cat in [
        SourceCategory.RAINFALL,
        SourceCategory.FLOOD,
        SourceCategory.LANDSLIDE,
        SourceCategory.HAZARD_OBSERVATION,
        SourceCategory.POPULATION_EXPOSURE,
    ]:
        provider = get_provider(cat)
        resp = provider.fetch_data(ProviderQuery(category=cat))
        raw_json = resp.model_dump_json().lower()

        for pii in ["phone", "email", "aadhaar", "ssn", "mobile", "password"]:
            assert f'"{pii}"' not in raw_json, f"Potential PII field '{pii}' found in response for {cat}"
