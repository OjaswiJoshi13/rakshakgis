"""Contracts, data schemas, and domain models for data source telemetry and freshness."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.data.providers.contracts import (
    ProviderHealth,
    ProviderMode,
    SourceCategory,
)


class FreshnessStatus(str, Enum):
    """Categorical classification of data source temporal freshness."""

    FRESH = "fresh"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    CLOCK_SKEW = "clock_skew"
    UNKNOWN = "unknown"


class FreshnessThresholds(BaseModel):
    """Configurable freshness thresholds in seconds across conceptual categories."""

    model_config = ConfigDict(frozen=True)

    rainfall_seconds: float = Field(
        default=3600.0,  # 1 hour (meteorological AWS telemetry cadence)
        ge=1.0,
        description="Maximum freshness age for rainfall readings.",
    )
    flood_seconds: float = Field(
        default=3600.0,  # 1 hour (hydrological river gauge cadence)
        ge=1.0,
        description="Maximum freshness age for hydrological flood readings.",
    )
    landslide_seconds: float = Field(
        default=86400.0,  # 24 hours (daily geological survey/slope observation)
        ge=1.0,
        description="Maximum freshness age for landslide observations.",
    )
    hazard_observation_seconds: float = Field(
        default=3600.0,  # 1 hour (in-situ multi-hazard sensor feeds)
        ge=1.0,
        description="Maximum freshness age for sensor observations.",
    )
    population_exposure_seconds: float = Field(
        default=604800.0,  # 7 days (demographic and census exposure cycles)
        ge=1.0,
        description="Maximum freshness age for population exposure records.",
    )
    default_seconds: float = Field(
        default=86400.0,  # 24 hours fallback
        ge=1.0,
        description="Default freshness threshold fallback.",
    )
    clock_skew_tolerance_seconds: float = Field(
        default=60.0,  # 60s clock skew tolerance
        ge=0.0,
        description="Maximum acceptable future timestamp drift before flagging clock skew.",
    )

    def get_threshold_for_category(
        self, category: Optional[SourceCategory]
    ) -> float:
        """Resolve the appropriate freshness threshold for a given category."""
        if category == SourceCategory.RAINFALL:
            return self.rainfall_seconds
        elif category == SourceCategory.FLOOD:
            return self.flood_seconds
        elif category == SourceCategory.LANDSLIDE:
            return self.landslide_seconds
        elif category == SourceCategory.HAZARD_OBSERVATION:
            return self.hazard_observation_seconds
        elif category == SourceCategory.POPULATION_EXPOSURE:
            return self.population_exposure_seconds
        return self.default_seconds


DEFAULT_THRESHOLDS = FreshnessThresholds()


class FreshnessEvaluation(BaseModel):
    """Deterministic evaluation of a data source's temporal freshness and usability."""

    model_config = ConfigDict(frozen=True)

    status: FreshnessStatus
    age_seconds: Optional[float] = None
    threshold_seconds: float
    is_usable: bool
    reason: str
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class IngestionRunSummary(BaseModel):
    """Sanitized summary of an automated or manual ingestion batch run."""

    model_config = ConfigDict(frozen=True)

    run_id: int
    data_source_id: int
    status: str  # in_progress, success, failed, partial
    records_received: int
    records_accepted: int
    records_rejected: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    log_summary: Optional[str] = None


class SourceTelemetrySummary(BaseModel):
    """Operational telemetry summary for a registered data source."""

    model_config = ConfigDict(frozen=True)

    source_id: int
    name: str
    source_type: str
    provider: str
    provider_id: Optional[str] = None
    category: Optional[SourceCategory] = None
    provider_mode: ProviderMode = ProviderMode.MOCK
    provider_health: ProviderHealth = ProviderHealth.HEALTHY
    freshness: FreshnessEvaluation
    last_successful_update: Optional[datetime] = None
    last_attempted_update: Optional[datetime] = None
    latest_run_status: Optional[str] = None
    is_synthetic: bool = True
    is_active: bool = True
    endpoint_url: Optional[str] = None
    polling_interval_seconds: Optional[int] = None
    region_id: Optional[str] = None
    records_ingested_total: int = 0
    records_failed_total: int = 0
    metadata_json: Optional[Dict[str, Any]] = None


class TelemetryOverview(BaseModel):
    """High-level telemetry health overview across all data sources."""

    model_config = ConfigDict(frozen=True)

    total_sources: int
    healthy_count: int
    degraded_count: int
    unavailable_count: int
    fresh_count: int
    stale_count: int
    unknown_count: int
    synthetic_count: int
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
