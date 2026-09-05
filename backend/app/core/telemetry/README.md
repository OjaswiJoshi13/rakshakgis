# Data Source Freshness & Telemetry Subsystem (Chunk M3-13)

This package provides deterministic data source tracking, provider health monitoring, and temporal freshness evaluation for RakshakGIS.

## Architecture

The telemetry subsystem bridges the physical database entities (`DataSource`, `DataIngestionRun`), the M3-03 provider adapters (`BaseDataProvider`, `ProviderRegistry`), and operational monitoring endpoints (`/api/v1/telemetry`).

```
┌─────────────────────────┐       ┌────────────────────────┐
│   Provider Registry     │       │   PostgreSQL Database  │
│   (M3-03 Adapters)      │       │ (DataSource, Runs)     │
└────────────┬────────────┘       └───────────┬────────────┘
             │                                │
             ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│                   TelemetryService                       │
│    - Synchronizes registered adapters with DataSource    │
│    - Queries latest execution & ingestion statistics     │
│    - Sanitizes diagnostic logs (scrubs secrets/tokens)   │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                  FreshnessEvaluator                      │
│    - Evaluates elapsed age against category thresholds   │
│    - Detects future timestamps & clock skew (>60s)       │
│    - Integrates ProviderHealth (HEALTHY/DEGRADED/OFFLINE)│
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│             SourceTelemetrySummary Envelope              │
│       Status: FRESH | STALE | UNAVAILABLE | CLOCK_SKEW   │
└──────────────────────────────────────────────────────────┘
```

## Freshness Semantics & Invariants

1. **Deterministic Evaluation**: Freshness is determined purely as a function of `(last_successful_update, provider_health, category, threshold, as_of_time)`.
2. **Conservative Defaults**:
   - Missing timestamp $\implies$ `UNKNOWN` (never `FRESH`, `is_usable = False`).
   - Unavailable provider $\implies$ `UNAVAILABLE` (`is_usable = False`).
   - Failed ingestion run $\implies$ not fresh (`STALE` or `UNKNOWN`).
   - Corrupted or invalid timestamp string $\implies$ `UNKNOWN` (`is_usable = False`).
   - Future timestamp beyond 60s tolerance $\implies$ `CLOCK_SKEW` (`is_usable = False`).
3. **Configurable Thresholds**:
   - `rainfall`: 3,600s (1 hour)
   - `flood`: 3,600s (1 hour)
   - `landslide`: 86,400s (24 hours)
   - `hazard_observation`: 3,600s (1 hour)
   - `population_exposure`: 604,800s (7 days)
   - Default fallback: 86,400s (24 hours)
4. **Secret Sanitization**:
   - All diagnostic logs, error messages, and telemetry outputs are scrubbed of Bearer tokens, API keys, database credentials, and authorization headers before persistence or display.
5. **Synthetic / Demo Data**:
   - All synthetic and mock sources retain `is_synthetic = True` and statutory disclaimers.
