"""Pydantic schemas for data source telemetry, freshness, and ingestion run API endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.telemetry.contracts import FreshnessStatus


class FreshnessEvaluationRead(BaseModel):
    """Schema representing evaluated freshness and usability."""

    model_config = ConfigDict(from_attributes=True)

    status: FreshnessStatus
    age_seconds: Optional[float] = None
    threshold_seconds: float
    is_usable: bool
    reason: str
    evaluated_at: datetime


class DataIngestionRunRead(BaseModel):
    """Schema for an individual ingestion run record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    data_source_id: int
    status: str
    records_ingested: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    log_details: Optional[str] = None


class DataSourceTelemetryRead(BaseModel):
    """Schema representing operational telemetry for a data source."""

    model_config = ConfigDict(from_attributes=True)

    source_id: int
    name: str
    source_type: str
    provider: str
    provider_id: Optional[str] = None
    category: Optional[str] = None
    provider_mode: str
    provider_health: str
    freshness: FreshnessEvaluationRead
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


class DataSourceDetailRead(DataSourceTelemetryRead):
    """Detailed data source telemetry with recent ingestion runs and metadata."""

    recent_runs: List[DataIngestionRunRead] = Field(default_factory=list)
    metadata_json: Optional[Dict[str, Any]] = None


class TelemetryOverviewRead(BaseModel):
    """Aggregated platform-wide data source health and freshness overview."""

    model_config = ConfigDict(from_attributes=True)

    total_sources: int
    healthy_count: int
    degraded_count: int
    unavailable_count: int
    fresh_count: int
    stale_count: int
    unknown_count: int
    synthetic_count: int
    evaluated_at: datetime
