"""Deterministic mock data source adapters implementing provider contracts for RakshakGIS."""

from typing import List, Optional, Set
from app.data.providers.contracts import (
    BaseDataProvider,
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderHealth,
    ProviderMode,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
)
from app.data.synthetic.constants import (
    PILOT_DISTRICT_CODE,
    PILOT_REGION_PROFILE_ID,
    SYNTHETIC_DISCLAIMER,
)
from app.data.synthetic.loader import (
    load_himalayan_pilot_dataset,
)


class BaseMockProvider(BaseDataProvider):
    """Common foundation for deterministic mock adapters consuming M3-02 fixtures."""

    def __init__(self, is_healthy: bool = True):
        self._is_healthy = is_healthy

    @property
    def mode(self) -> ProviderMode:
        return ProviderMode.MOCK

    @property
    def supported_regions(self) -> Set[str]:
        return {PILOT_REGION_PROFILE_ID}

    def check_health(self) -> ProviderHealth:
        if not self._is_healthy:
            return ProviderHealth.UNAVAILABLE
        return ProviderHealth.HEALTHY

    def _validate_query(self, query: ProviderQuery) -> None:
        """Validate query parameters against supported category, region, and provider availability."""
        if self.check_health() != ProviderHealth.HEALTHY:
            raise ProviderUnavailableError(
                f"Provider '{self.provider_id}' is currently unavailable/offline.",
                provider_id=self.provider_id,
            )

        if query.category not in self.supported_categories:
            raise UnsupportedQueryError(
                f"Provider '{self.provider_id}' does not support category '{query.category.value}'. "
                f"Supported: {[c.value for c in self.supported_categories]}",
                provider_id=self.provider_id,
            )

        if query.region_id and query.region_id not in self.supported_regions:
            raise UnsupportedQueryError(
                f"Provider '{self.provider_id}' does not support region '{query.region_id}'. "
                f"Supported: {list(self.supported_regions)}",
                provider_id=self.provider_id,
            )

        if query.district_code and query.district_code != PILOT_DISTRICT_CODE:
            raise UnsupportedQueryError(
                f"Provider '{self.provider_id}' only supports pilot district '{PILOT_DISTRICT_CODE}', "
                f"got '{query.district_code}'.",
                provider_id=self.provider_id,
            )

    def _create_provenance(self) -> ProviderProvenance:
        return ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=self.mode,
            is_synthetic=True,
            region_id=PILOT_REGION_PROFILE_ID,
            disclaimer=SYNTHETIC_DISCLAIMER,
        )


# =====================================================================
# 1. Mock Rainfall Provider
# =====================================================================


class MockRainfallProvider(BaseMockProvider):
    """Mock provider simulating IMD automated weather station precipitation readings."""

    @property
    def provider_id(self) -> str:
        return "mock_imd_rainfall"

    @property
    def provider_name(self) -> str:
        return "Mock IMD Meteorological Rainfall Adapter"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.RAINFALL}

    def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedRainfallRecord]:
        self._validate_query(query)

        dataset = load_himalayan_pilot_dataset()
        raw_events = [e for e in dataset.hazard_events if e.hazard_type == "rainfall"]

        # Apply deterministic filters
        if query.village_id:
            raw_events = [e for e in raw_events if e.village_id == query.village_id]

        if query.start_time:
            raw_events = [e for e in raw_events if e.observed_at >= query.start_time]

        if query.end_time:
            raw_events = [e for e in raw_events if e.observed_at <= query.end_time]

        # Sort deterministically
        raw_events.sort(key=lambda e: (e.observed_at, e.id))

        if query.limit:
            raw_events = raw_events[: query.limit]

        provenance = self._create_provenance()
        records: List[NormalizedRainfallRecord] = []

        for e in raw_events:
            rain_val = float(e.intensity_value)
            records.append(
                NormalizedRainfallRecord(
                    record_id=f"REC-{e.id}",
                    observed_at=e.observed_at,
                    location_coordinates=e.location.coordinates,
                    provenance=provenance,
                    village_id=e.village_id,
                    village_name=e.village_name,
                    rainfall_24h_mm=rain_val,
                    severity=e.severity,
                    is_heavy_rain=rain_val >= 64.5,
                    is_very_heavy_rain=rain_val >= 115.5,
                    description=e.description,
                )
            )

        return ProviderResponse[NormalizedRainfallRecord](
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=query.category,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )


# =====================================================================
# 2. Mock Flood Provider
# =====================================================================


class MockFloodProvider(BaseMockProvider):
    """Mock provider simulating Central Water Commission (CWC) river gauge / flood data."""

    @property
    def provider_id(self) -> str:
        return "mock_cwc_flood"

    @property
    def provider_name(self) -> str:
        return "Mock Central Water Commission (CWC) Hydrological Adapter"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.FLOOD}

    def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedFloodRecord]:
        self._validate_query(query)

        dataset = load_himalayan_pilot_dataset()
        raw_events = [e for e in dataset.hazard_events if e.hazard_type == "flash_flood"]

        if query.village_id:
            raw_events = [e for e in raw_events if e.village_id == query.village_id]

        if query.start_time:
            raw_events = [e for e in raw_events if e.observed_at >= query.start_time]

        if query.end_time:
            raw_events = [e for e in raw_events if e.observed_at <= query.end_time]

        raw_events.sort(key=lambda e: (e.observed_at, e.id))

        if query.limit:
            raw_events = raw_events[: query.limit]

        provenance = self._create_provenance()
        records: List[NormalizedFloodRecord] = []

        for e in raw_events:
            records.append(
                NormalizedFloodRecord(
                    record_id=f"REC-{e.id}",
                    observed_at=e.observed_at,
                    location_coordinates=e.location.coordinates,
                    provenance=provenance,
                    village_id=e.village_id,
                    village_name=e.village_name,
                    flood_type="flash_flood",
                    water_level_m_above_danger=float(e.intensity_value),
                    severity=e.severity,
                    description=e.description,
                )
            )

        return ProviderResponse[NormalizedFloodRecord](
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=query.category,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )


# =====================================================================
# 3. Mock Landslide Provider
# =====================================================================


class MockLandslideProvider(BaseMockProvider):
    """Mock provider simulating Geological Survey of India (GSI) landslide incident records."""

    @property
    def provider_id(self) -> str:
        return "mock_gsi_landslide"

    @property
    def provider_name(self) -> str:
        return "Mock Geological Survey of India (GSI) Landslide Adapter"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.LANDSLIDE}

    def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedLandslideRecord]:
        self._validate_query(query)

        dataset = load_himalayan_pilot_dataset()
        raw_events = [e for e in dataset.hazard_events if e.hazard_type == "landslide"]

        if query.village_id:
            raw_events = [e for e in raw_events if e.village_id == query.village_id]

        if query.start_time:
            raw_events = [e for e in raw_events if e.observed_at >= query.start_time]

        if query.end_time:
            raw_events = [e for e in raw_events if e.observed_at <= query.end_time]

        raw_events.sort(key=lambda e: (e.observed_at, e.id))

        if query.limit:
            raw_events = raw_events[: query.limit]

        provenance = self._create_provenance()
        records: List[NormalizedLandslideRecord] = []

        for e in raw_events:
            is_blocked = "blocked" in (e.description or "").lower()
            records.append(
                NormalizedLandslideRecord(
                    record_id=f"REC-{e.id}",
                    observed_at=e.observed_at,
                    location_coordinates=e.location.coordinates,
                    provenance=provenance,
                    village_id=e.village_id,
                    village_name=e.village_name,
                    debris_volume_cu_m=float(e.intensity_value),
                    severity=e.severity,
                    road_blocked=is_blocked,
                    description=e.description,
                )
            )

        return ProviderResponse[NormalizedLandslideRecord](
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=query.category,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )


# =====================================================================
# 4. Mock Multi-Hazard Telemetry Provider
# =====================================================================


class MockHazardObservationProvider(BaseMockProvider):
    """Mock provider simulating integrated in-situ multi-hazard telemetry streams."""

    @property
    def provider_id(self) -> str:
        return "mock_multi_hazard_telemetry"

    @property
    def provider_name(self) -> str:
        return "Mock In-Situ Multi-Hazard Sensor Telemetry Adapter"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.HAZARD_OBSERVATION}

    def fetch_data(
        self, query: ProviderQuery
    ) -> ProviderResponse[NormalizedHazardObservationRecord]:
        self._validate_query(query)

        dataset = load_himalayan_pilot_dataset()
        raw_events = list(dataset.hazard_events)

        if query.village_id:
            raw_events = [e for e in raw_events if e.village_id == query.village_id]

        if query.start_time:
            raw_events = [e for e in raw_events if e.observed_at >= query.start_time]

        if query.end_time:
            raw_events = [e for e in raw_events if e.observed_at <= query.end_time]

        raw_events.sort(key=lambda e: (e.observed_at, e.id))

        if query.limit:
            raw_events = raw_events[: query.limit]

        provenance = self._create_provenance()
        records: List[NormalizedHazardObservationRecord] = []

        for e in raw_events:
            records.append(
                NormalizedHazardObservationRecord(
                    record_id=f"REC-{e.id}",
                    observed_at=e.observed_at,
                    location_coordinates=e.location.coordinates,
                    provenance=provenance,
                    hazard_type=e.hazard_type,
                    village_id=e.village_id,
                    village_name=e.village_name,
                    severity=e.severity,
                    intensity_value=float(e.intensity_value),
                    intensity_unit=e.intensity_unit,
                    description=e.description,
                )
            )

        return ProviderResponse[NormalizedHazardObservationRecord](
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=query.category,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )


# =====================================================================
# 5. Mock Population & Exposure Provider
# =====================================================================


class MockPopulationExposureProvider(BaseMockProvider):
    """Mock provider simulating Census and District Demographics exposure feeds."""

    @property
    def provider_id(self) -> str:
        return "mock_census_demographics"

    @property
    def provider_name(self) -> str:
        return "Mock Census & District Demographics Exposure Adapter"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.POPULATION_EXPOSURE}

    def fetch_data(
        self, query: ProviderQuery
    ) -> ProviderResponse[NormalizedPopulationRecord]:
        self._validate_query(query)

        dataset = load_himalayan_pilot_dataset()
        raw_villages = list(dataset.villages.features)

        if query.village_id:
            raw_villages = [
                v for v in raw_villages if v.properties.id == query.village_id
            ]

        raw_villages.sort(key=lambda v: v.properties.id)

        if query.limit:
            raw_villages = raw_villages[: query.limit]

        provenance = self._create_provenance()
        records: List[NormalizedPopulationRecord] = []

        for v in raw_villages:
            p = v.properties
            d = p.demographics
            records.append(
                NormalizedPopulationRecord(
                    village_id=p.id,
                    village_name=p.name,
                    region_code=p.region_code,
                    district_code=p.district_code,
                    block_code=p.block_code,
                    location_coordinates=v.geometry.coordinates,
                    total_population=p.population,
                    households=p.households,
                    elderly_count=d.elderly_count,
                    children_count=d.children_count,
                    disabled_count=d.disabled_count,
                    livestock_count=d.livestock_count,
                    provenance=provenance,
                )
            )

        return ProviderResponse[NormalizedPopulationRecord](
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=query.category,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )
