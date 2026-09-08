"""Comprehensive test suite for Data Source Freshness & Telemetry Backend (Chunk M3-13).

Covers:
1. Healthy provider + recent successful update -> FRESH
2. Old successful update -> STALE
3. Unavailable provider -> UNAVAILABLE
4. Missing update timestamp -> not FRESH (UNKNOWN)
5. Failed ingestion -> not FRESH
6. Invalid timestamp -> explicit invalid/unknown handling
7. Future timestamp -> safe clock-skew handling
8. Deterministic freshness evaluation
9. Provider health integration with M3-03
10. Provider registry integration
11. Synthetic/demo provenance preserved
12. No secrets exposed in telemetry responses
13. Ingestion run status/counts represented correctly
14. API returns structured telemetry/source data
15. API errors use existing common error contract
16. Existing backend tests remain unchanged and passing
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.telemetry.contracts import (
    DEFAULT_THRESHOLDS,
    FreshnessEvaluation,
    FreshnessStatus,
    FreshnessThresholds,
    SourceTelemetrySummary,
)
from app.core.telemetry.errors import DataSourceNotFoundError
from app.core.telemetry.evaluator import (
    FreshnessEvaluator,
    parse_timestamp_safe,
)
from app.core.telemetry.service import (
    TelemetryService,
    sanitize_log_content,
)
from app.data.providers.contracts import (
    BaseDataProvider,
    ProviderHealth,
    ProviderMode,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    SourceCategory,
)
from app.data.providers.mock import MockRainfallProvider
from app.data.providers.registry import ProviderRegistry
from app.main import app
from app.core.database import SessionLocal
from app.models.telemetry import (
    DataIngestionRun,
    DataSource,
)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def evaluator():
    """Default freshness evaluator."""
    return FreshnessEvaluator()


# =====================================================================
# 1. Healthy provider + recent successful update -> FRESH
# =====================================================================


def test_01_healthy_recent_update_is_fresh(evaluator):
    """Test 1: Healthy provider with recent successful update evaluates to FRESH and usable."""
    now = datetime.now(timezone.utc)
    recent_update = now - timedelta(minutes=15)  # 15 min old

    # Rainfall threshold is 3600s (60 min)
    result = evaluator.evaluate(
        last_successful_update=recent_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.FRESH
    assert result.is_usable is True
    assert result.age_seconds is not None
    assert 890 <= result.age_seconds <= 910
    assert result.threshold_seconds == 3600.0
    assert "fresh" in result.reason.lower()


# =====================================================================
# 2. Old successful update -> STALE
# =====================================================================


def test_02_old_successful_update_is_stale(evaluator):
    """Test 2: Update older than category threshold evaluates to STALE and unusable."""
    now = datetime.now(timezone.utc)
    old_update = now - timedelta(hours=2)  # 2 hours old for 1 hour threshold

    result = evaluator.evaluate(
        last_successful_update=old_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.STALE
    assert result.is_usable is False
    assert result.age_seconds is not None
    assert result.age_seconds > 3600.0
    assert "stale" in result.reason.lower()


# =====================================================================
# 3. Unavailable provider -> UNAVAILABLE
# =====================================================================


def test_03_unavailable_provider_is_unavailable(evaluator):
    """Test 3: Provider marked UNAVAILABLE evaluates to UNAVAILABLE even if data is 1 second old."""
    now = datetime.now(timezone.utc)
    recent_update = now - timedelta(seconds=1)

    result = evaluator.evaluate(
        last_successful_update=recent_update,
        provider_health=ProviderHealth.UNAVAILABLE,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.UNAVAILABLE
    assert result.is_usable is False
    assert "offline or unreachable" in result.reason.lower()


# =====================================================================
# 4. Missing update timestamp -> not FRESH (UNKNOWN)
# =====================================================================


def test_04_missing_update_timestamp_is_unknown(evaluator):
    """Test 4: Missing last update timestamp evaluates to UNKNOWN, never FRESH."""
    now = datetime.now(timezone.utc)

    result = evaluator.evaluate(
        last_successful_update=None,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.UNKNOWN
    assert result.is_usable is False
    assert result.age_seconds is None
    assert "no successful data update timestamp" in result.reason.lower()


# =====================================================================
# 5. Failed ingestion -> not FRESH
# =====================================================================


def test_05_failed_ingestion_not_fresh(evaluator):
    """Test 5: Failed ingestion without valid past data evaluates to UNKNOWN with failure noted."""
    now = datetime.now(timezone.utc)

    result = evaluator.evaluate(
        last_successful_update=None,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.FLOOD,
        as_of_time=now,
        latest_run_status="failed",
    )

    assert result.status == FreshnessStatus.UNKNOWN
    assert result.is_usable is False
    assert "failed" in result.reason.lower()


def test_05b_failed_ingestion_with_stale_data_is_stale(evaluator):
    """Test 5b: Failed ingestion with old past data evaluates to STALE."""
    now = datetime.now(timezone.utc)
    old_update = now - timedelta(days=2)

    result = evaluator.evaluate(
        last_successful_update=old_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.FLOOD,
        as_of_time=now,
        latest_run_status="failed",
    )

    assert result.status == FreshnessStatus.STALE
    assert result.is_usable is False
    assert "failed" in result.reason.lower()


# =====================================================================
# 6. Invalid timestamp -> explicit invalid/unknown handling
# =====================================================================


def test_06_invalid_timestamp_is_unknown(evaluator):
    """Test 6: Malformed or unparseable timestamp evaluates to UNKNOWN, not FRESH."""
    now = datetime.now(timezone.utc)

    for bad_ts in ["not-a-timestamp", "2026-99-99T99:99:99", "   ", "invalid-date"]:
        result = evaluator.evaluate(
            last_successful_update=bad_ts,
            provider_health=ProviderHealth.HEALTHY,
            category=SourceCategory.RAINFALL,
            as_of_time=now,
        )
        assert result.status == FreshnessStatus.UNKNOWN
        assert result.is_usable is False
        assert "invalid" in result.reason.lower() or "unparseable" in result.reason.lower()


# =====================================================================
# 7. Future timestamp -> safe clock-skew handling
# =====================================================================


def test_07_future_timestamp_is_clock_skew(evaluator):
    """Test 7: Future timestamp beyond 60s tolerance is flagged as CLOCK_SKEW, not FRESH."""
    now = datetime.now(timezone.utc)
    future_update = now + timedelta(minutes=10)

    result = evaluator.evaluate(
        last_successful_update=future_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.CLOCK_SKEW
    assert result.is_usable is False
    assert "clock skew" in result.reason.lower()
    assert "future" in result.reason.lower()


def test_07b_minor_clock_skew_within_tolerance(evaluator):
    """Test 7b: Minor negative age within 60s tolerance is clamped to 0.0s and accepted as FRESH."""
    now = datetime.now(timezone.utc)
    slight_future = now + timedelta(seconds=15)  # Within 60s tolerance

    result = evaluator.evaluate(
        last_successful_update=slight_future,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.FRESH
    assert result.is_usable is True
    assert result.age_seconds == 0.0


# =====================================================================
# 8. Deterministic freshness evaluation
# =====================================================================


def test_08_deterministic_evaluation(evaluator):
    """Test 8: Freshness evaluation produces identical results on identical inputs."""
    fixed_now = datetime(2026, 9, 6, 12, 0, 0, tzinfo=timezone.utc)
    last_update = datetime(2026, 9, 6, 11, 30, 0, tzinfo=timezone.utc)

    eval1 = evaluator.evaluate(
        last_successful_update=last_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=fixed_now,
    )

    eval2 = evaluator.evaluate(
        last_successful_update=last_update,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.RAINFALL,
        as_of_time=fixed_now,
    )

    assert eval1.status == eval2.status
    assert eval1.age_seconds == eval2.age_seconds
    assert eval1.threshold_seconds == eval2.threshold_seconds
    assert eval1.is_usable == eval2.is_usable
    assert eval1.reason == eval2.reason


# =====================================================================
# 9. Provider health integration with M3-03
# =====================================================================


def test_09_provider_health_degraded(evaluator):
    """Test 9: DEGRADED provider with fresh data is marked FRESH but notes degradation in reason."""
    now = datetime.now(timezone.utc)
    recent_update = now - timedelta(minutes=10)

    result = evaluator.evaluate(
        last_successful_update=recent_update,
        provider_health=ProviderHealth.DEGRADED,
        category=SourceCategory.LANDSLIDE,
        as_of_time=now,
    )

    assert result.status == FreshnessStatus.FRESH
    assert result.is_usable is True
    assert "degraded" in result.reason.lower()


# =====================================================================
# 10. Provider registry integration
# =====================================================================


def test_10_provider_registry_synchronization(db_session: Session):
    """Test 10: TelemetryService discovers registered providers and syncs to DataSource DB table."""
    service = TelemetryService()
    synced = service.sync_registered_providers(db_session)

    assert len(synced) >= 5
    provider_ids = [s.provider for s in synced]
    assert "mock_imd_rainfall" in provider_ids
    assert "mock_cwc_flood" in provider_ids
    assert "mock_gsi_landslide" in provider_ids
    assert "mock_multi_hazard_telemetry" in provider_ids
    assert "mock_census_demographics" in provider_ids


# =====================================================================
# 11. Synthetic/demo provenance preserved
# =====================================================================


def test_11_synthetic_demo_provenance_preserved(db_session: Session):
    """Test 11: Telemetry responses preserve synthetic flags and disclaimer metadata."""
    service = TelemetryService()
    summaries = service.list_sources_telemetry(db_session)

    assert len(summaries) > 0
    synthetic_sources = [s for s in summaries if s.provider and s.provider.startswith("mock_")]
    assert len(synthetic_sources) >= 4
    for s in synthetic_sources:
        assert s.is_synthetic is True
        assert s.metadata_json is not None
        assert "disclaimer" in s.metadata_json
        assert "DEMO / SYNTHETIC" in s.metadata_json["disclaimer"]

    real_sources = [s for s in summaries if s.provider in ("ncs_official_seismology", "usgs_live_earthquake", "open_meteo_live_weather")]
    for s in real_sources:
        assert s.is_synthetic is False


# =====================================================================
# 12. No secrets exposed in telemetry responses
# =====================================================================


def test_12_secret_sanitization():
    """Test 12: Secret sanitization scrubs Bearer tokens, API keys, and connection strings."""
    dirty_log = (
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secretpayload123 "
        "Failed with api_key='sk-prod-9876543210' and password = 'SuperSecret123!' "
        "Connecting to postgresql://admin:MySecretPass@db:5432/rakshakgis"
    )

    clean_log = sanitize_log_content(dirty_log)

    assert "Bearer [REDACTED]" in clean_log
    assert "eyJhbGciOiJIUzI1Ni" not in clean_log
    assert "[REDACTED]" in clean_log
    assert "sk-prod-9876543210" not in clean_log
    assert "SuperSecret123!" not in clean_log
    assert "MySecretPass" not in clean_log


def test_12b_record_ingestion_sanitizes_secrets(db_session: Session):
    """Test 12b: Recording an ingestion run sanitizes secrets before saving to DB."""
    service = TelemetryService()
    sources = service.sync_registered_providers(db_session)
    source = sources[0]

    run = service.record_ingestion_run(
        db=db_session,
        source_id=source.id,
        status="failed",
        records_ingested=0,
        records_failed=5,
        log_details="Sync failed with token='secret_token_abc123' for user password='my_pwd'",
    )

    assert "secret_token_abc123" not in run.log_details
    assert "my_pwd" not in run.log_details
    assert "[REDACTED]" in run.log_details


# =====================================================================
# 13. Ingestion run status/counts represented correctly
# =====================================================================


def test_13_ingestion_run_stats_aggregation(db_session: Session):
    """Test 13: Ingestion runs aggregate total ingested and failed record counts correctly."""
    service = TelemetryService()
    sources = service.sync_registered_providers(db_session)
    source = sources[1]

    now = datetime.now(timezone.utc)

    # Record two runs
    service.record_ingestion_run(
        db=db_session,
        source_id=source.id,
        status="success",
        records_ingested=25,
        records_failed=2,
        started_at=now - timedelta(hours=1),
        completed_at=now - timedelta(minutes=58),
        log_details="Batch 1 completed.",
    )

    service.record_ingestion_run(
        db=db_session,
        source_id=source.id,
        status="success",
        records_ingested=50,
        records_failed=3,
        started_at=now - timedelta(minutes=10),
        completed_at=now - timedelta(minutes=9),
        log_details="Batch 2 completed.",
    )

    telemetry = service.get_source_telemetry(db_session, source, as_of_time=now)

    assert telemetry.records_ingested_total >= 75
    assert telemetry.records_failed_total >= 5
    assert telemetry.latest_run_status == "success"
    assert telemetry.freshness.status == FreshnessStatus.FRESH


# =====================================================================
# 14. API returns structured telemetry/source data
# =====================================================================


def test_14_api_telemetry_sources_endpoints(client: TestClient):
    """Test 14: API endpoints return properly enveloped structured telemetry responses."""
    # 1. Overview
    res_overview = client.get("/api/v1/telemetry/overview")
    assert res_overview.status_code == 200
    overview_body = res_overview.json()
    assert overview_body["success"] is True
    assert "data" in overview_body
    assert "total_sources" in overview_body["data"]
    assert overview_body["data"]["total_sources"] >= 5

    # 2. List sources
    res_list = client.get("/api/v1/telemetry/sources?page=1&page_size=10")
    assert res_list.status_code == 200
    list_body = res_list.json()
    assert list_body["success"] is True
    assert "data" in list_body
    assert "pagination" in list_body
    assert len(list_body["data"]) >= 5

    # 3. Source detail by ID or provider key
    source_item = list_body["data"][0]
    source_id = source_item["source_id"]

    res_detail = client.get(f"/api/v1/telemetry/sources/{source_id}")
    assert res_detail.status_code == 200
    detail_body = res_detail.json()
    assert detail_body["success"] is True
    assert detail_body["data"]["source_id"] == source_id
    assert "freshness" in detail_body["data"]
    assert "recent_runs" in detail_body["data"]

    # 4. Source runs
    res_runs = client.get(f"/api/v1/telemetry/sources/{source_id}/runs")
    assert res_runs.status_code == 200
    runs_body = res_runs.json()
    assert runs_body["success"] is True
    assert "pagination" in runs_body

    # 5. Probe
    res_probe = client.post(f"/api/v1/telemetry/sources/{source_id}/probe")
    assert res_probe.status_code == 200
    probe_body = res_probe.json()
    assert probe_body["success"] is True
    assert probe_body["data"]["freshness"]["status"] == FreshnessStatus.FRESH.value


# =====================================================================
# 15. API errors use existing common error contract
# =====================================================================


def test_15_api_errors_common_contract(client: TestClient):
    """Test 15: Non-existent data source returns 404 adhering to ErrorResponse schema."""
    response = client.get("/api/v1/telemetry/sources/999999")
    assert response.status_code == 404

    body = response.json()
    assert body["success"] is False
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert "999999" in body["error"]["message"]
    assert body["error"]["status_code"] == 404


# =====================================================================
# 16. Configurable category thresholds & custom polling override
# =====================================================================


def test_16_category_and_custom_thresholds(evaluator):
    """Test 16: Category-specific default thresholds and custom threshold overrides."""
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)

    # Landslide default threshold is 24h (86400s) -> 2 days is STALE
    eval_landslide = evaluator.evaluate(
        last_successful_update=two_days_ago,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.LANDSLIDE,
        as_of_time=now,
    )
    assert eval_landslide.status == FreshnessStatus.STALE

    # Population exposure default threshold is 7 days (604800s) -> 2 days is FRESH
    eval_population = evaluator.evaluate(
        last_successful_update=two_days_ago,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.POPULATION_EXPOSURE,
        as_of_time=now,
    )
    assert eval_population.status == FreshnessStatus.FRESH

    # Custom threshold override: 3 days (259200s) makes Landslide evaluate to FRESH
    eval_custom = evaluator.evaluate(
        last_successful_update=two_days_ago,
        provider_health=ProviderHealth.HEALTHY,
        category=SourceCategory.LANDSLIDE,
        custom_threshold_seconds=259200.0,
        as_of_time=now,
    )
    assert eval_custom.status == FreshnessStatus.FRESH
