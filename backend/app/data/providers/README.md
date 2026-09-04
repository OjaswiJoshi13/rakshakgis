# RakshakGIS Data Provider Adapters & Interfaces (Chunk M3-03)

This package establishes the provider abstraction foundation for ingesting external and environmental data sources into RakshakGIS.

> [!IMPORTANT]
> **SYNTHETIC / DEMO PROVIDER NOTICE**
> The default adapters in this package operate exclusively on deterministic synthetic fixtures (from Chunk M3-02) for SIH Problem Statement 26191. They do NOT connect to external networks or live vendor APIs, and mock outputs are NOT official government data.

---

## 1. Why Provider Adapters Exist

Provider adapters decouple the RakshakGIS ingestion pipeline and risk analysis modules from the volatile interfaces, proprietary data formats, authentication flows, and network latency of external data sources (e.g. IMD weather stations, CWC river gauges, GSI landslide reports, Sentinel satellite rasters, and Census demographics).

By programming against a uniform `BaseDataProvider` contract:
- Downstream ingestion and processing code remains stable even if external vendor APIs change.
- Automated tests, CI pipelines, and local development run reliably offline with deterministic fixtures.
- Live APIs can be introduced incrementally without modifying core database schemas or analytical engines.

---

## 2. Mock vs Future Live Providers

| Feature | Mock Adapters (`ProviderMode.MOCK`) | Future Live Adapters (`ProviderMode.LIVE`) |
| :--- | :--- | :--- |
| **Network Access** | Completely offline (0 network calls). | Connects to external HTTPS/REST/WFS endpoints. |
| **Credentials** | Zero API keys, tokens, or credentials needed. | Managed via environment variables or secret vaults. |
| **Data Source** | Deterministic M3-02 synthetic fixtures. | Live telemetry, satellite feeds, or agency portals. |
| **Determinism** | 100% deterministic, repeatable queries. | Real-time time-series streams. |
| **Provenance** | Explicitly marked `is_synthetic: true` with disclaimer. | Marked `is_synthetic: false` with live agency attribution. |

---

## 3. How to Implement a Future Live Provider

To add a new live provider (e.g. for IMD Automatic Weather Stations):

1. **Subclass `BaseDataProvider`**:
   ```python
   from app.data.providers.contracts import BaseDataProvider, ProviderMode, SourceCategory, ProviderResponse, ProviderQuery

   class LiveIMDRainfallProvider(BaseDataProvider):
       @property
       def provider_id(self) -> str:
           return "live_imd_aws_rainfall"

       @property
       def provider_name(self) -> str:
           return "Live IMD AWS Rainfall API Adapter"

       @property
       def supported_categories(self) -> Set[SourceCategory]:
           return {SourceCategory.RAINFALL}

       @property
       def supported_regions(self) -> Set[str]:
           return {"himalayan_pilot", "riverine_template", "coastal_template"}

       @property
       def mode(self) -> ProviderMode:
           return ProviderMode.LIVE

       def check_health(self) -> ProviderHealth:
           # Ping endpoint or check token validity
           return ProviderHealth.HEALTHY

       def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedRainfallRecord]:
           # 1. Validate query (categories and region)
           # 2. Call external HTTP endpoint using requests/httpx
           # 3. Transform external vendor JSON to NormalizedRainfallRecord
           # 4. Return ProviderResponse
           ...
   ```

2. **Register with the Registry**:
   ```python
   from app.data.providers import register_provider
   register_provider(LiveIMDRainfallProvider(), set_default_for_categories=True)
   ```

---

## 4. Strict Separation of Concerns

> [!WARNING]
> **NO RISK LOGIC IN ADAPTERS**
> Provider adapters are responsible **solely** for data ingestion, connection management, protocol translation, and normalization into typed records. They must **never** perform multi-hazard composite risk calculations, Red Zone demarcation, vulnerability scoring, or relocation site matching. Those responsibilities belong strictly to downstream analytical engines (Chunks M3-05 to M4-06).
