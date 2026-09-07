"""API v1 Data Source Freshness & Telemetry router."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.telemetry.contracts import (
    FreshnessStatus,
    SourceCategory,
)
from app.core.telemetry.errors import DataSourceNotFoundError
from app.core.telemetry.service import TelemetryService
from app.models.telemetry import (
    DataIngestionRun,
    DataSource,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationMetadata,
    ResponseEnvelope,
)
from app.schemas.telemetry import (
    DataIngestionRunRead,
    DataSourceDetailRead,
    DataSourceTelemetryRead,
    TelemetryOverviewRead,
)

telemetry_router = APIRouter()
_telemetry_service = TelemetryService()


@telemetry_router.get(
    "/overview",
    response_model=ResponseEnvelope[TelemetryOverviewRead],
    summary="Platform telemetry overview",
    description="Retrieve high-level summary counts of registered data sources, health states, and freshness.",
)
def get_telemetry_overview(
    db: Session = Depends(get_db),
):
    """Retrieve platform-wide telemetry overview."""
    overview = _telemetry_service.get_overview(db)
    return ResponseEnvelope(success=True, data=overview)


@telemetry_router.get(
    "/sources",
    response_model=PaginatedResponse[DataSourceTelemetryRead],
    summary="List data source telemetry",
    description="Retrieve paginated list of registered data sources with provider health and deterministic freshness status.",
)
def list_data_sources(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    category: Optional[SourceCategory] = Query(None, description="Filter by source category"),
    region_id: Optional[str] = Query(None, description="Filter by region identifier"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """List data sources with operational telemetry and freshness."""
    all_summaries = _telemetry_service.list_sources_telemetry(
        db=db,
        category=category,
        region_id=region_id,
        is_active=is_active,
    )

    total = len(all_summaries)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = all_summaries[start_idx:end_idx]

    pagination = PaginationMetadata(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )

    return PaginatedResponse(
        success=True,
        data=paged_items,
        pagination=pagination,
    )


@telemetry_router.get(
    "/sources/{id}",
    response_model=ResponseEnvelope[DataSourceDetailRead],
    summary="Get data source details and telemetry",
    description="Retrieve detailed operational telemetry, freshness evaluation, and recent ingestion runs for a data source.",
)
def get_data_source_detail(
    id: str = Path(..., description="Data source numeric ID or provider key"),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single data source."""
    try:
        source = _telemetry_service.resolve_source(db, id)
    except DataSourceNotFoundError:
        raise NotFoundError(message=f"Data source with identifier '{id}' was not found.")

    summary = _telemetry_service.get_source_telemetry(db, source)

    # Fetch up to 10 most recent ingestion runs
    recent_runs = (
        db.query(DataIngestionRun)
        .filter(DataIngestionRun.data_source_id == source.id)
        .order_by(DataIngestionRun.started_at.desc())
        .limit(10)
        .all()
    )

    detail_data = DataSourceDetailRead(
        source_id=summary.source_id,
        name=summary.name,
        source_type=summary.source_type,
        provider=summary.provider,
        provider_id=summary.provider_id,
        category=summary.category.value if summary.category else None,
        provider_mode=summary.provider_mode.value,
        provider_health=summary.provider_health.value,
        freshness=summary.freshness,
        last_successful_update=summary.last_successful_update,
        last_attempted_update=summary.last_attempted_update,
        latest_run_status=summary.latest_run_status,
        is_synthetic=summary.is_synthetic,
        is_active=summary.is_active,
        endpoint_url=summary.endpoint_url,
        polling_interval_seconds=summary.polling_interval_seconds,
        region_id=summary.region_id,
        records_ingested_total=summary.records_ingested_total,
        records_failed_total=summary.records_failed_total,
        recent_runs=[
            DataIngestionRunRead.model_validate(r) for r in recent_runs
        ],
        metadata_json=summary.metadata_json,
    )

    return ResponseEnvelope(success=True, data=detail_data)


@telemetry_router.get(
    "/sources/{id}/runs",
    response_model=PaginatedResponse[DataIngestionRunRead],
    summary="List ingestion runs for a data source",
    description="Retrieve paginated execution history of automated or manual ingestion runs.",
)
def list_data_source_runs(
    id: str = Path(..., description="Data source numeric ID or provider key"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated ingestion history for a data source."""
    try:
        source = _telemetry_service.resolve_source(db, id)
    except DataSourceNotFoundError:
        raise NotFoundError(message=f"Data source with identifier '{id}' was not found.")

    query = db.query(DataIngestionRun).filter(DataIngestionRun.data_source_id == source.id)

    if status_filter:
        query = query.filter(DataIngestionRun.status == status_filter.lower().strip())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    runs = (
        query.order_by(DataIngestionRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    pagination = PaginationMetadata(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )

    data = [DataIngestionRunRead.model_validate(r) for r in runs]
    return PaginatedResponse(success=True, data=data, pagination=pagination)


@telemetry_router.post(
    "/sources/{id}/probe",
    response_model=ResponseEnvelope[DataSourceTelemetryRead],
    summary="Probe data source health and trigger sync",
    description="Probe provider health and deterministically record an ingestion sync run.",
)
def probe_data_source(
    id: str = Path(..., description="Data source numeric ID or provider key"),
    db: Session = Depends(get_db),
):
    """Probe provider availability and trigger synchronization."""
    try:
        summary = _telemetry_service.probe_and_sync_source(db, id)
    except DataSourceNotFoundError:
        raise NotFoundError(message=f"Data source with identifier '{id}' was not found.")

    read_model = DataSourceTelemetryRead(
        source_id=summary.source_id,
        name=summary.name,
        source_type=summary.source_type,
        provider=summary.provider,
        provider_id=summary.provider_id,
        category=summary.category.value if summary.category else None,
        provider_mode=summary.provider_mode.value,
        provider_health=summary.provider_health.value,
        freshness=summary.freshness,
        last_successful_update=summary.last_successful_update,
        last_attempted_update=summary.last_attempted_update,
        latest_run_status=summary.latest_run_status,
        is_synthetic=summary.is_synthetic,
        is_active=summary.is_active,
        endpoint_url=summary.endpoint_url,
        polling_interval_seconds=summary.polling_interval_seconds,
        region_id=summary.region_id,
        records_ingested_total=summary.records_ingested_total,
        records_failed_total=summary.records_failed_total,
    )

    return ResponseEnvelope(success=True, data=read_model)


@telemetry_router.post(
    "/import",
    response_model=ResponseEnvelope[dict],
    summary="Trigger data import",
    description="Trigger automated data ingestion pipeline for live or static datasets.",
)
def import_data(
    source_id: Optional[str] = Query(None, description="Optional data source identifier to sync"),
    db: Session = Depends(get_db),
):
    """Trigger manual data import execution."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    if source_id:
        try:
            summary = _telemetry_service.probe_and_sync_source(db, source_id)
            return ResponseEnvelope(
                success=True,
                data={
                    "status": "completed",
                    "source_id": summary.source_id,
                    "name": summary.name,
                    "records_ingested": summary.records_ingested_total,
                    "timestamp": now.isoformat(),
                },
            )
        except DataSourceNotFoundError:
            raise NotFoundError(message=f"Data source with identifier '{source_id}' was not found.")

    # Platform-wide sync
    synced = _telemetry_service.sync_registered_providers(db)
    return ResponseEnvelope(
        success=True,
        data={
            "status": "completed",
            "message": f"Successfully checked and synced {len(synced)} authoritative data sources.",
            "sources_synced": [s.name for s in synced],
            "timestamp": now.isoformat(),
        },
    )

