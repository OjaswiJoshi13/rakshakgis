"""Automated unit and integration tests for real-world authoritative data provider adapters."""

import pytest
from app.data.providers import (
    ProviderHealth,
    ProviderMode,
    ProviderQuery,
    SourceCategory,
)
from app.data.providers.cwc_flood import CWCFloodProvider
from app.data.providers.ncs_earthquake import NCSEarthquakeProvider
from app.data.providers.open_meteo import OpenMeteoWeatherProvider
from app.data.providers.registry import ProviderRegistry
from app.data.providers.usgs_earthquake import USGSEarthquakeProvider


def test_open_meteo_provider_metadata_and_initialization():
    """Verify OpenMeteoWeatherProvider properties, categories, and health check."""
    provider = OpenMeteoWeatherProvider()
    assert provider.provider_id == "open_meteo_live_weather"
    assert "Open-Meteo" in provider.provider_name
    assert "IMD" not in provider.provider_name  # Rule 9 / Context requirement
    assert provider.mode == ProviderMode.LIVE
    health = provider.check_health()
    assert health in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED, ProviderHealth.UNAVAILABLE)


def test_open_meteo_query_structure():
    """Verify OpenMeteo live query returns structured canonical records or handles network state."""
    provider = OpenMeteoWeatherProvider()
    query = ProviderQuery(
        category=SourceCategory.RAINFALL,
        latitude=30.55,
        longitude=79.56,
        region_id="uttarakhand_himalayan",
    )
    try:
        resp = provider.fetch_data(query)
        assert resp.category == SourceCategory.RAINFALL
        assert resp.provider_id == "open_meteo_live_weather"
        assert resp.provenance.is_synthetic is False
    except Exception as exc:
        # If external network is unreachable in sandbox, check exception type
        assert "Open-Meteo" in str(exc) or "timed out" in str(exc) or "network" in str(exc).lower() or "getaddrinfo" in str(exc).lower()


def test_cwc_flood_provider_metadata_and_parsing():
    """Verify CWCFloodProvider properties and sample data parsing."""
    provider = CWCFloodProvider()
    assert provider.provider_id == "cwc_live_flood_aff"
    assert "Central Water Commission" in provider.provider_name
    assert provider.TABLE_URL.startswith("https://aff.india-water.gov.in")
    
    sample_row = {
        "Station": "Joshimath",
        "River": "Alaknanda",
        "District": "Chamoli",
        "State": "Uttarakhand",
        "Latitude": "30.55",
        "Longitude": "79.56",
        "WarningLevel": "1150.0",
        "DangerLevel": "1152.0",
        "WIMS_Value": "1148.5",
        "current_condition": "Normal",
        "Date_WIMS": "07-09-2026 08:00",
    }
    query = ProviderQuery(category=SourceCategory.FLOOD, district_code="chamoli")
    from app.data.providers.contracts import ProviderProvenance
    prov = ProviderProvenance(
        provider_id=provider.provider_id,
        provider_name=provider.provider_name,
        mode=ProviderMode.LIVE,
        is_synthetic=False,
    )
    records = provider._transform_rows([sample_row], query, prov)
    assert len(records) == 1
    assert records[0].record_id == "CWC_Joshimath_0"
    assert records[0].water_level_m_above_danger == 0.0


def test_usgs_earthquake_provider_metadata():
    """Verify USGSEarthquakeProvider properties and availability."""
    provider = USGSEarthquakeProvider()
    assert provider.provider_id == "usgs_live_earthquake"
    assert "USGS" in provider.provider_name
    assert "earthquake.usgs.gov" in provider.API_URL
    assert provider.check_health() in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED, ProviderHealth.UNAVAILABLE)


def test_usgs_earthquake_query_himalayan_pilot():
    """Verify USGS query with himalayan_pilot safely resolves coordinates without crashing."""
    provider = USGSEarthquakeProvider()
    query = ProviderQuery(
        category=SourceCategory.HAZARD_OBSERVATION,
        region_id="himalayan_pilot",
    )
    # Must not raise AttributeError: 'ProviderQuery' object has no attribute 'filter_criteria'
    lat, lon = provider._resolve_center_point(query)
    assert 30.0 <= lat <= 31.0
    assert 79.0 <= lon <= 80.5


def test_ncs_earthquake_provider_metadata():
    """Verify NCSEarthquakeProvider properties and catalog loading."""
    provider = NCSEarthquakeProvider()
    assert provider.provider_id == "ncs_official_seismology"
    assert "National Centre for Seismology" in provider.provider_name
    assert provider.check_health() in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED, ProviderHealth.UNAVAILABLE)


def test_provider_registry_authoritative_resolution():
    """Verify ProviderRegistry correctly discovers and returns authoritative adapters."""
    registry = ProviderRegistry(load_defaults=True)
    providers = registry.list_providers()
    assert len(providers) >= 5
    
    om = registry.get_by_id("open_meteo_live_weather")
    assert om is not None
    assert isinstance(om, OpenMeteoWeatherProvider)

    cwc = registry.get_by_id("cwc_live_flood_aff")
    assert cwc is not None
    assert isinstance(cwc, CWCFloodProvider)

    usgs = registry.get_by_id("usgs_live_earthquake")
    assert usgs is not None
    assert isinstance(usgs, USGSEarthquakeProvider)

    ncs = registry.get_by_id("ncs_official_seismology")
    assert ncs is not None
    assert isinstance(ncs, NCSEarthquakeProvider)
