"""Abstract provider contracts, typed normalized schemas, and exception hierarchy for RakshakGIS."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, List, Optional, Set, Tuple, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class SourceCategory(str, Enum):
    """Conceptual data source categories supported by provider adapters."""

    RAINFALL = "rainfall"
    FLOOD = "flood"
    LANDSLIDE = "landslide"
    HAZARD_OBSERVATION = "hazard_observation"
    POPULATION_EXPOSURE = "population_exposure"


class ProviderMode(str, Enum):
    """Operational mode of the data provider."""

    MOCK = "mock"
    LIVE = "live"


class ProviderHealth(str, Enum):
    """Health status reported by provider availability checks."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


# =====================================================================
# Exception Hierarchy
# =====================================================================


class ProviderError(Exception):
    """Base exception for all provider adapter failures."""

    def __init__(self, message: str, provider_id: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider_id = provider_id

    def __str__(self) -> str:
        if self.provider_id:
            return f"[{self.provider_id}] {self.message}"
        return self.message


class ProviderUnavailableError(ProviderError):
    """Raised when a provider service cannot be reached, is degraded, or is offline."""

    pass


class UnsupportedQueryError(ProviderError):
    """Raised when a query requests an unsupported category, region, or filter parameter."""

    pass


class ProviderPayloadError(ProviderError):
    """Raised when provider data fails contract validation or is corrupted."""

    pass


# =====================================================================
# Query & Provenance Schemas
# =====================================================================


class ProviderProvenance(BaseModel):
    """Metadata tracking provider identity, synthetic nature, and legal disclaimer."""

    model_config = ConfigDict(frozen=True)

    provider_id: str
    provider_name: str
    mode: ProviderMode
    is_synthetic: bool = True
    region_id: Optional[str] = None
    disclaimer: str = (
        "DEMO / SYNTHETIC DATASET for SIH Problem Statement 26191. "
        "Not official statutory or live operational government data."
    )


class ProviderQuery(BaseModel):
    """Normalized query parameters passed to provider adapters."""

    model_config = ConfigDict(frozen=True)

    category: SourceCategory
    region_id: Optional[str] = None
    district_code: Optional[str] = None
    village_id: Optional[str] = None
    start_time: Optional[str] = None  # ISO 8601 string
    end_time: Optional[str] = None    # ISO 8601 string
    limit: Optional[int] = Field(default=None, ge=1)


# =====================================================================
# Normalized Observation & Demographic Records
# =====================================================================


class NormalizedBaseRecord(BaseModel):
    """Base schema for normalized spatio-temporal observation records."""

    model_config = ConfigDict(frozen=True)

    record_id: str
    observed_at: str  # ISO 8601 timestamp string
    location_coordinates: Tuple[float, float]  # [longitude, latitude] in WGS84
    provenance: ProviderProvenance


class NormalizedRainfallRecord(NormalizedBaseRecord):
    """Normalized precipitation observation record."""

    village_id: Optional[str] = None
    village_name: Optional[str] = None
    rainfall_24h_mm: float = Field(..., ge=0.0)
    severity: str  # "moderate", "high", "very_high", "critical"
    is_heavy_rain: bool = False       # >= 64.5 mm (IMD threshold)
    is_very_heavy_rain: bool = False  # >= 115.5 mm (IMD threshold)
    description: Optional[str] = None


class NormalizedFloodRecord(NormalizedBaseRecord):
    """Normalized hydrological flood or flash flood observation record."""

    village_id: Optional[str] = None
    village_name: Optional[str] = None
    flood_type: str = "flash_flood"
    water_level_m_above_danger: float = Field(..., ge=0.0)
    severity: str
    description: Optional[str] = None


class NormalizedLandslideRecord(NormalizedBaseRecord):
    """Normalized landslide incident or slope failure observation record."""

    village_id: Optional[str] = None
    village_name: Optional[str] = None
    debris_volume_cu_m: float = Field(..., ge=0.0)
    severity: str
    road_blocked: bool = False
    description: Optional[str] = None


class NormalizedHazardObservationRecord(NormalizedBaseRecord):
    """Generalized multi-hazard sensor observation record."""

    hazard_type: str  # "landslide", "rainfall", "seismic", "flash_flood"
    village_id: Optional[str] = None
    village_name: Optional[str] = None
    severity: str
    intensity_value: float = Field(..., ge=0.0)
    intensity_unit: str
    description: Optional[str] = None


class NormalizedPopulationRecord(BaseModel):
    """Normalized demographic and vulnerability exposure record."""

    model_config = ConfigDict(frozen=True)

    village_id: str
    village_name: str
    region_code: str
    district_code: str
    block_code: str
    location_coordinates: Tuple[float, float]
    total_population: int = Field(..., ge=0)
    households: int = Field(..., ge=0)
    elderly_count: int = Field(..., ge=0)
    children_count: int = Field(..., ge=0)
    disabled_count: int = Field(..., ge=0)
    livestock_count: int = Field(..., ge=0)
    provenance: ProviderProvenance


# =====================================================================
# Response Envelope
# =====================================================================

T = TypeVar("T")


class ProviderResponse(BaseModel, Generic[T]):
    """Standardized envelope returned by all provider adapters."""

    model_config = ConfigDict(frozen=True)

    provider_id: str
    provider_name: str
    category: SourceCategory
    query: ProviderQuery
    records: List[T]
    total_count: int
    provenance: ProviderProvenance


# =====================================================================
# Base Provider Contract (Abstract Base Class)
# =====================================================================


class BaseDataProvider(ABC):
    """Abstract interface defining the contract for all data source adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique stable identifier for this provider adapter (e.g. 'mock_imd_rainfall')."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable display name for this provider."""
        pass

    @property
    @abstractmethod
    def supported_categories(self) -> Set[SourceCategory]:
        """Set of conceptual source categories supported by this adapter."""
        pass

    @property
    @abstractmethod
    def supported_regions(self) -> Set[str]:
        """Set of region profile IDs supported by this adapter (e.g. {'himalayan_pilot'})."""
        pass

    @property
    @abstractmethod
    def mode(self) -> ProviderMode:
        """Operational mode (MOCK or LIVE)."""
        pass

    @abstractmethod
    def check_health(self) -> ProviderHealth:
        """Perform a liveness/health probe of the provider."""
        pass

    @abstractmethod
    def fetch_data(self, query: ProviderQuery) -> ProviderResponse:
        """Fetch and return normalized records matching the query parameters.

        Raises:
            UnsupportedQueryError: If query requests an unsupported category, region, or filter.
            ProviderUnavailableError: If provider is offline or degraded.
            ProviderPayloadError: If returned data is corrupted or fails validation.
        """
        pass
