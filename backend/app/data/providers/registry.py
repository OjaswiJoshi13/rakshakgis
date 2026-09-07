"""Central registry and resolution for data source provider adapters in RakshakGIS."""

import threading
from typing import Dict, List, Optional, Set

from app.data.providers.contracts import (
    BaseDataProvider,
    ProviderError,
    SourceCategory,
)
from app.data.providers.mock import (
    MockFloodProvider,
    MockHazardObservationProvider,
    MockLandslideProvider,
    MockPopulationExposureProvider,
    MockRainfallProvider,
)


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider cannot be found by ID or category."""

    pass


class ProviderRegistry:
    """Thread-safe registry for discovering and resolving data providers."""

    def __init__(self, load_defaults: bool = True):
        self._lock = threading.RLock()
        self._providers_by_id: Dict[str, BaseDataProvider] = {}
        self._default_by_category: Dict[SourceCategory, BaseDataProvider] = {}

        if load_defaults:
            self._load_default_mock_providers()

    def _load_default_mock_providers(self) -> None:
        """Register the standard deterministic mock adapters."""
        defaults = [
            MockRainfallProvider(),
            MockFloodProvider(),
            MockLandslideProvider(),
            MockHazardObservationProvider(),
            MockPopulationExposureProvider(),
        ]
        for p in defaults:
            self.register(p, set_default_for_categories=True)

        self._load_authoritative_providers()

    def _load_authoritative_providers(self) -> None:
        """Register live and static authoritative data providers."""
        try:
            from app.core.config import get_settings
            from app.data.providers.cwc_flood import CWCFloodProvider
            from app.data.providers.ncs_earthquake import NCSEarthquakeProvider
            from app.data.providers.open_meteo import OpenMeteoWeatherProvider
            from app.data.providers.usgs_earthquake import USGSEarthquakeProvider

            settings = get_settings()
            make_default = settings.DATA_MODE in ["live", "full_data"]

            live_providers = [
                OpenMeteoWeatherProvider(),
                CWCFloodProvider(),
                USGSEarthquakeProvider(),
                NCSEarthquakeProvider(),
            ]
            for p in live_providers:
                self.register(p, set_default_for_categories=make_default)
        except Exception as exc:
            import logging
            logging.getLogger("rakshakgis.providers").warning("Could not load authoritative providers: %s", exc)


    def register(
        self, provider: BaseDataProvider, set_default_for_categories: bool = True
    ) -> None:
        """Register a provider adapter."""
        with self._lock:
            self._providers_by_id[provider.provider_id] = provider
            if set_default_for_categories:
                for cat in provider.supported_categories:
                    self._default_by_category[cat] = provider

    def get_by_id(self, provider_id: str) -> BaseDataProvider:
        """Retrieve a registered provider by its unique identifier."""
        with self._lock:
            if provider_id not in self._providers_by_id:
                raise ProviderNotFoundError(
                    f"No provider registered with ID '{provider_id}'.",
                    provider_id=provider_id,
                )
            return self._providers_by_id[provider_id]

    def get_by_category(
        self, category: SourceCategory, region_id: Optional[str] = None
    ) -> BaseDataProvider:
        """Resolve a suitable provider for a given source category and optional region."""
        with self._lock:
            # First check if default provider for category supports the region
            default_p = self._default_by_category.get(category)
            if default_p:
                if region_id is None or region_id in default_p.supported_regions:
                    return default_p

            # Fallback: find any provider supporting this category and region
            for p in self._providers_by_id.values():
                if category in p.supported_categories:
                    if region_id is None or region_id in p.supported_regions:
                        return p

            raise ProviderNotFoundError(
                f"No provider found supporting category '{category.value}'"
                + (f" for region '{region_id}'" if region_id else "")
                + "."
            )

    def list_providers(self) -> List[BaseDataProvider]:
        """Return all registered providers."""
        with self._lock:
            return list(self._providers_by_id.values())

    def list_provider_ids(self) -> List[str]:
        """Return IDs of all registered providers."""
        with self._lock:
            return list(self._providers_by_id.keys())

    def count(self) -> int:
        """Return the number of registered providers."""
        with self._lock:
            return len(self._providers_by_id)


# Global singleton registry
_GLOBAL_REGISTRY = ProviderRegistry(load_defaults=True)


def get_provider(
    category: SourceCategory, region_id: Optional[str] = None
) -> BaseDataProvider:
    """Resolve the default provider adapter for a category and optional region."""
    return _GLOBAL_REGISTRY.get_by_category(category, region_id)


def get_provider_by_id(provider_id: str) -> BaseDataProvider:
    """Retrieve a provider adapter by its unique identifier."""
    return _GLOBAL_REGISTRY.get_by_id(provider_id)


def register_provider(
    provider: BaseDataProvider, set_default_for_categories: bool = True
) -> None:
    """Register a provider adapter with the global registry."""
    _GLOBAL_REGISTRY.register(provider, set_default_for_categories)


def list_providers() -> List[BaseDataProvider]:
    """List all provider adapters currently registered in the global registry."""
    return _GLOBAL_REGISTRY.list_providers()


def list_provider_ids() -> List[str]:
    """List all registered provider IDs."""
    return _GLOBAL_REGISTRY.list_provider_ids()
