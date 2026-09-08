"""Telemetry service orchestrating provider health probes, database telemetry records, and freshness evaluations."""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.telemetry.contracts import (
    DEFAULT_THRESHOLDS,
    FreshnessEvaluation,
    FreshnessStatus,
    FreshnessThresholds,
    IngestionRunSummary,
    SourceTelemetrySummary,
    TelemetryOverview,
)
from app.core.telemetry.errors import DataSourceNotFoundError
from app.core.telemetry.evaluator import (
    FreshnessEvaluator,
    parse_timestamp_safe,
)
from app.data.providers.contracts import (
    BaseDataProvider,
    ProviderHealth,
    ProviderMode,
    ProviderQuery,
    SourceCategory,
)
from app.data.providers.registry import (
    ProviderRegistry,
    get_provider_by_id,
    list_providers,
)
from app.models.telemetry import (
    DataIngestionRun,
    DataSource,
)

# Regex patterns for sanitizing sensitive credentials from logs and telemetry
_SECRET_PATTERNS = [
    (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[a-z0-9\-._~+/]+=*", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)\bbearer\s+[a-z0-9\-._~+/]+=*", re.IGNORECASE),
        "Bearer [REDACTED]",
    ),
    (
        re.compile(
            r"""(?i)(["']?(?:api[_-]?key|secret|token|password|passwd|access[_-]?token)["']?\s*[:=]\s*["']?)([^"'\s,;]+)(["']?)"""
        ),
        r"\1[REDACTED]\3",
    ),
    (
        re.compile(r"""(?i)(postgres(?:ql)?://)(?:[^:]+):(?:[^@]+)@"""),
        r"\1[REDACTED]:[REDACTED]@",
    ),
]


def sanitize_log_content(content: Optional[str]) -> Optional[str]:
    """Sanitize secrets, authentication headers, database URIs, and passwords from log strings."""
    if not content:
        return content
    sanitized = content
    for pattern, replacement in _SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class TelemetryService:
    """Service layer managing data source registry synchronization, health monitoring, and freshness."""

    def __init__(
        self,
        evaluator: Optional[FreshnessEvaluator] = None,
        provider_registry: Optional[ProviderRegistry] = None,
    ):
        self.evaluator = evaluator or FreshnessEvaluator()
        self.registry = provider_registry

    def sync_registered_providers(self, db: Session) -> List[DataSource]:
        """Ensure all registered provider adapters in the registry have a corresponding DataSource in the database."""
        providers = self.registry.list_providers() if self.registry else list_providers()
        synced_sources: List[DataSource] = []

        for p in providers:
            # Look up existing data source by name or provider identifier
            source = (
                db.query(DataSource)
                .filter(
                    (DataSource.provider == p.provider_id)
                    | (DataSource.name == p.provider_name)
                )
                .first()
            )

            primary_cat = next(iter(p.supported_categories)) if p.supported_categories else None
            cat_str = primary_cat.value if primary_cat else "unknown"
            default_polling = int(self.evaluator.thresholds.get_threshold_for_category(primary_cat))

            # Verified real statutory & observational feeds vs synthetic simulation feeds
            REAL_PROVIDERS = {
                "ncs_official_seismology",
                "usgs_live_earthquake",
                "open_meteo_live_weather",
                "cwc_live_flood_aff",
                "survey_of_india_cadastral",
                "census_pca_2011",
            }
            is_real = p.provider_id in REAL_PROVIDERS or p.mode.value == "live"
            is_synth = not is_real

            disclaimer = (
                "Verified real observational / statutory data feed."
                if is_real
                else (
                    "DEMO / SYNTHETIC DATASET for SIH Problem Statement 26191. "
                    "Not official statutory or live operational government data."
                )
            )

            metadata = {
                "provider_id": p.provider_id,
                "mode": p.mode.value,
                "is_synthetic": is_synth,
                "supported_categories": [c.value for c in p.supported_categories],
                "supported_regions": list(p.supported_regions),
                "disclaimer": disclaimer,
            }

            if not source:
                source = DataSource(
                    name=p.provider_name,
                    source_type=cat_str,
                    provider=p.provider_id,
                    endpoint_url=f"adapter://{p.provider_id}",
                    is_active=True,
                    polling_interval_seconds=default_polling,
                    metadata_json=metadata,
                )
                db.add(source)
                db.flush()
            else:
                # Update metadata if needed
                curr_meta = dict(source.metadata_json or {})
                curr_meta.update(metadata)
                source.metadata_json = curr_meta
                source.provider = p.provider_id

            synced_sources.append(source)

        # Ensure static statutory datasets are registered as verified non-synthetic sources
        static_statutory_sources = [
            {
                "provider": "survey_of_india_cadastral",
                "name": "Survey of India Cadastral Village Boundaries",
                "source_type": "cadastral_geography",
                "endpoint_url": "static://data/soi_uttarakhand_villages.geojson",
                "metadata": {
                    "provider_id": "survey_of_india_cadastral",
                    "mode": "static_statutory",
                    "is_synthetic": False,
                    "supported_categories": ["cadastral_boundaries", "administrative_geography"],
                    "supported_regions": ["himalayan_pilot", "uttarakhand", "chamoli"],
                    "disclaimer": "Official Survey of India (SOI) administrative village boundary polygons.",
                },
            },
            {
                "provider": "census_pca_2011",
                "name": "Census of India 2011 Primary Census Abstract",
                "source_type": "demographic_exposure",
                "endpoint_url": "static://data/census_2011_pca_chamoli.csv",
                "metadata": {
                    "provider_id": "census_pca_2011",
                    "mode": "static_statutory",
                    "is_synthetic": False,
                    "supported_categories": ["demographics", "vulnerability"],
                    "supported_regions": ["himalayan_pilot", "uttarakhand", "chamoli"],
                    "disclaimer": "Official Ministry of Home Affairs / Office of Registrar General Census 2011 PCA demographics.",
                },
            },
        ]

        for s_def in static_statutory_sources:
            src = (
                db.query(DataSource)
                .filter(
                    (DataSource.provider == s_def["provider"])
                    | (DataSource.name == s_def["name"])
                )
                .first()
            )
            if not src:
                src = DataSource(
                    name=s_def["name"],
                    source_type=s_def["source_type"],
                    provider=s_def["provider"],
                    endpoint_url=s_def["endpoint_url"],
                    is_active=True,
                    polling_interval_seconds=86400 * 30,
                    metadata_json=s_def["metadata"],
                )
                db.add(src)
                db.flush()
            else:
                curr_meta = dict(src.metadata_json or {})
                curr_meta.update(s_def["metadata"])
                src.metadata_json = curr_meta
                src.provider = s_def["provider"]
            synced_sources.append(src)

        db.commit()
        return synced_sources

    def resolve_source(
        self, db: Session, identifier: Union[int, str]
    ) -> DataSource:
        """Resolve a DataSource entity by primary key ID, provider_id, or name."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            source = db.query(DataSource).filter(DataSource.id == int(identifier)).first()
            if source:
                return source

        if isinstance(identifier, str):
            source = (
                db.query(DataSource)
                .filter(
                    (DataSource.provider == identifier)
                    | (DataSource.name == identifier)
                )
                .first()
            )
            if source:
                return source

        raise DataSourceNotFoundError(
            f"Data source with identifier '{identifier}' was not found.",
            source_id=str(identifier),
        )

    def _resolve_provider_for_source(
        self, source: DataSource
    ) -> Optional[BaseDataProvider]:
        """Attempt to find a registered provider adapter corresponding to a DataSource."""
        provider_id = (source.metadata_json or {}).get("provider_id") or source.provider
        if self.registry:
            try:
                return self.registry.get_by_id(provider_id)
            except Exception:
                pass
        try:
            return get_provider_by_id(provider_id)
        except Exception:
            return None

    def get_source_telemetry(
        self,
        db: Session,
        source: DataSource,
        as_of_time: Optional[datetime] = None,
    ) -> SourceTelemetrySummary:
        """Calculate complete operational telemetry summary for a single DataSource."""
        provider_adapter = self._resolve_provider_for_source(source)

        # 1. Probe provider health
        if provider_adapter:
            try:
                health = provider_adapter.check_health()
            except Exception:
                health = ProviderHealth.UNAVAILABLE
            mode = provider_adapter.mode
            provider_id = provider_adapter.provider_id
            supported_cats = provider_adapter.supported_categories
            category = next(iter(supported_cats)) if supported_cats else None
        else:
            health = ProviderHealth.HEALTHY if source.is_active else ProviderHealth.UNAVAILABLE
            mode = ProviderMode.MOCK
            provider_id = source.provider
            try:
                category = SourceCategory(source.source_type)
            except (ValueError, TypeError):
                category = None

        # 2. Query ingestion runs
        latest_run = (
            db.query(DataIngestionRun)
            .filter(DataIngestionRun.data_source_id == source.id)
            .order_by(DataIngestionRun.started_at.desc(), DataIngestionRun.id.desc())
            .first()
        )

        latest_successful_run = (
            db.query(DataIngestionRun)
            .filter(
                DataIngestionRun.data_source_id == source.id,
                DataIngestionRun.status == "success",
            )
            .order_by(DataIngestionRun.completed_at.desc(), DataIngestionRun.id.desc())
            .first()
        )

        # 3. Aggregate total ingested and failed records
        run_stats = (
            db.query(
                func.coalesce(func.sum(DataIngestionRun.records_ingested), 0),
                func.coalesce(func.sum(DataIngestionRun.records_failed), 0),
            )
            .filter(DataIngestionRun.data_source_id == source.id)
            .first()
        )
        total_ingested = int(run_stats[0]) if run_stats else 0
        total_failed = int(run_stats[1]) if run_stats else 0

        # 4. Determine last successful and attempted update timestamps
        meta = dict(source.metadata_json or {})
        if "disclaimer" not in meta:
            meta["disclaimer"] = (
                "DEMO / SYNTHETIC DATASET for SIH Problem Statement 26191. "
                "Not official statutory or live operational government data."
            )
        explicit_last_success = meta.get("last_successful_update")
        if latest_successful_run and latest_successful_run.completed_at:
            last_successful = latest_successful_run.completed_at
        elif explicit_last_success:
            last_successful = parse_timestamp_safe(explicit_last_success)
        else:
            last_successful = None

        last_attempted = (
            latest_run.started_at
            if latest_run
            else parse_timestamp_safe(meta.get("last_attempted_update"))
        )

        latest_status = latest_run.status if latest_run else None

        # Custom threshold override from DB polling interval or metadata
        custom_thresh = (
            float(source.polling_interval_seconds)
            if source.polling_interval_seconds and source.polling_interval_seconds > 0
            else meta.get("freshness_threshold_seconds")
        )

        # 5. Evaluate Freshness
        evaluation = self.evaluator.evaluate(
            last_successful_update=last_successful,
            provider_health=health,
            category=category,
            custom_threshold_seconds=custom_thresh,
            as_of_time=as_of_time,
            latest_run_status=latest_status,
        )

        # 6. Extract region association
        region_id = meta.get("region_id")
        if not region_id and provider_adapter and provider_adapter.supported_regions:
            region_id = next(iter(provider_adapter.supported_regions))

        return SourceTelemetrySummary(
            source_id=source.id,
            name=source.name,
            source_type=source.source_type,
            provider=source.provider,
            provider_id=provider_id,
            category=category,
            provider_mode=mode,
            provider_health=health,
            freshness=evaluation,
            last_successful_update=last_successful,
            last_attempted_update=last_attempted,
            latest_run_status=latest_status,
            is_synthetic=meta.get("is_synthetic", True),
            is_active=source.is_active,
            endpoint_url=source.endpoint_url,
            polling_interval_seconds=source.polling_interval_seconds,
            region_id=region_id,
            records_ingested_total=total_ingested,
            records_failed_total=total_failed,
            metadata_json=meta,
        )

    def list_sources_telemetry(
        self,
        db: Session,
        category: Optional[SourceCategory] = None,
        region_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        as_of_time: Optional[datetime] = None,
    ) -> List[SourceTelemetrySummary]:
        """List operational telemetry for all data sources with optional filters."""
        # Ensure default providers are present in DB
        self.sync_registered_providers(db)

        query = db.query(DataSource)
        if is_active is not None:
            query = query.filter(DataSource.is_active == is_active)

        sources = query.order_by(DataSource.id.asc()).all()
        results: List[SourceTelemetrySummary] = []

        for s in sources:
            summary = self.get_source_telemetry(db, s, as_of_time=as_of_time)
            if category and summary.category != category:
                continue
            if region_id and summary.region_id != region_id:
                continue
            results.append(summary)

        return results

    def get_overview(
        self,
        db: Session,
        as_of_time: Optional[datetime] = None,
    ) -> TelemetryOverview:
        """Compute aggregate platform-wide telemetry health metrics."""
        summaries = self.list_sources_telemetry(db, as_of_time=as_of_time)
        eval_time = as_of_time or datetime.now(timezone.utc)

        return TelemetryOverview(
            total_sources=len(summaries),
            healthy_count=sum(
                1 for s in summaries if s.provider_health == ProviderHealth.HEALTHY
            ),
            degraded_count=sum(
                1 for s in summaries if s.provider_health == ProviderHealth.DEGRADED
            ),
            unavailable_count=sum(
                1 for s in summaries if s.provider_health == ProviderHealth.UNAVAILABLE
            ),
            fresh_count=sum(
                1 for s in summaries if s.freshness.status == FreshnessStatus.FRESH
            ),
            stale_count=sum(
                1 for s in summaries if s.freshness.status == FreshnessStatus.STALE
            ),
            unknown_count=sum(
                1 for s in summaries if s.freshness.status in (FreshnessStatus.UNKNOWN, FreshnessStatus.CLOCK_SKEW)
            ),
            synthetic_count=sum(1 for s in summaries if s.is_synthetic),
            evaluated_at=eval_time,
        )

    def record_ingestion_run(
        self,
        db: Session,
        source_id: int,
        status: str,
        records_ingested: int = 0,
        records_failed: int = 0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        log_details: Optional[str] = None,
    ) -> DataIngestionRun:
        """Record an ingestion run execution with sanitized logs and updated timestamp."""
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not source:
            raise DataSourceNotFoundError(
                f"Data source with ID {source_id} was not found.",
                source_id=str(source_id),
            )

        start_time = started_at or datetime.now(timezone.utc)
        sanitized_log = sanitize_log_content(log_details)

        run = DataIngestionRun(
            data_source_id=source.id,
            status=status,
            records_ingested=records_ingested,
            records_failed=records_failed,
            started_at=start_time,
            completed_at=completed_at,
            log_details=sanitized_log,
        )
        db.add(run)

        # Update source metadata
        curr_meta = dict(source.metadata_json or {})
        curr_meta["last_attempted_update"] = start_time.isoformat()
        if status == "success" and completed_at:
            curr_meta["last_successful_update"] = completed_at.isoformat()
        source.metadata_json = curr_meta

        db.commit()
        db.refresh(run)
        return run

    def probe_and_sync_source(
        self,
        db: Session,
        identifier: Union[int, str],
        as_of_time: Optional[datetime] = None,
    ) -> SourceTelemetrySummary:
        """Probe provider health and deterministically record an ingestion run for mock adapters."""
        source = self.resolve_source(db, identifier)
        provider = self._resolve_provider_for_source(source)

        start_time = as_of_time or datetime.now(timezone.utc)

        if not provider:
            # Source exists in DB without registered adapter
            self.record_ingestion_run(
                db=db,
                source_id=source.id,
                status="failed",
                records_ingested=0,
                records_failed=0,
                started_at=start_time,
                completed_at=start_time,
                log_details="No provider adapter registered for source.",
            )
            return self.get_source_telemetry(db, source, as_of_time=as_of_time)

        # Probe health
        try:
            health = provider.check_health()
        except Exception as exc:
            health = ProviderHealth.UNAVAILABLE
            sanitized_err = sanitize_log_content(str(exc))
            self.record_ingestion_run(
                db=db,
                source_id=source.id,
                status="failed",
                records_ingested=0,
                records_failed=0,
                started_at=start_time,
                completed_at=start_time,
                log_details=f"Provider health check failed: {sanitized_err}",
            )
            return self.get_source_telemetry(db, source, as_of_time=as_of_time)

        if health == ProviderHealth.UNAVAILABLE:
            self.record_ingestion_run(
                db=db,
                source_id=source.id,
                status="failed",
                records_ingested=0,
                records_failed=0,
                started_at=start_time,
                completed_at=start_time,
                log_details="Provider health check reported UNAVAILABLE.",
            )
            return self.get_source_telemetry(db, source, as_of_time=as_of_time)

        # For healthy mock adapters, perform a query and record successful sync
        try:
            cat = next(iter(provider.supported_categories))
            reg = next(iter(provider.supported_regions)) if provider.supported_regions else None
            query = ProviderQuery(category=cat, region_id=reg, limit=10)
            resp = provider.fetch_data(query)

            completion_time = datetime.now(timezone.utc)
            self.record_ingestion_run(
                db=db,
                source_id=source.id,
                status="success",
                records_ingested=resp.total_count,
                records_failed=0,
                started_at=start_time,
                completed_at=completion_time,
                log_details=f"Successfully synced {resp.total_count} records from {provider.provider_name}.",
            )
        except Exception as exc:
            sanitized_err = sanitize_log_content(str(exc))
            completion_time = datetime.now(timezone.utc)
            self.record_ingestion_run(
                db=db,
                source_id=source.id,
                status="failed",
                records_ingested=0,
                records_failed=1,
                started_at=start_time,
                completed_at=completion_time,
                log_details=f"Sync fetch failed: {sanitized_err}",
            )

        return self.get_source_telemetry(db, source, as_of_time=as_of_time)
