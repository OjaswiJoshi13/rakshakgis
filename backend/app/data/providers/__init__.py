"""RakshakGIS Data Provider Contracts & Adapters Package (Chunk M3-03)."""

from app.data.providers.contracts import (
    BaseDataProvider,
    NormalizedBaseRecord,
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderError,
    ProviderHealth,
    ProviderMode,
    ProviderPayloadError,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
)
from app.data.providers.mock import (
    BaseMockProvider,
    MockFloodProvider,
    MockHazardObservationProvider,
    MockLandslideProvider,
    MockPopulationExposureProvider,
    MockRainfallProvider,
)
from app.data.providers.registry import (
    ProviderNotFoundError,
    ProviderRegistry,
    get_provider,
    get_provider_by_id,
    list_provider_ids,
    list_providers,
    register_provider,
)

__all__ = [
    # Enums
    "SourceCategory",
    "ProviderMode",
    "ProviderHealth",
    # Exceptions
    "ProviderError",
    "ProviderUnavailableError",
    "UnsupportedQueryError",
    "ProviderPayloadError",
    "ProviderNotFoundError",
    # Base Contract
    "BaseDataProvider",
    # Schemas
    "ProviderProvenance",
    "ProviderQuery",
    "ProviderResponse",
    "NormalizedBaseRecord",
    "NormalizedRainfallRecord",
    "NormalizedFloodRecord",
    "NormalizedLandslideRecord",
    "NormalizedHazardObservationRecord",
    "NormalizedPopulationRecord",
    # Mock Adapters
    "BaseMockProvider",
    "MockRainfallProvider",
    "MockFloodProvider",
    "MockLandslideProvider",
    "MockHazardObservationProvider",
    "MockPopulationExposureProvider",
    # Registry
    "ProviderRegistry",
    "get_provider",
    "get_provider_by_id",
    "register_provider",
    "list_providers",
    "list_provider_ids",
]
