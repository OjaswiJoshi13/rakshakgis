"""Deterministic evaluation engine for data source freshness and temporal health."""

from datetime import datetime, timezone
from typing import Optional, Union
from dateutil import parser as date_parser

from app.core.telemetry.contracts import (
    DEFAULT_THRESHOLDS,
    FreshnessEvaluation,
    FreshnessStatus,
    FreshnessThresholds,
)
from app.data.providers.contracts import (
    ProviderHealth,
    SourceCategory,
)


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime object is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_timestamp_safe(ts: Optional[Union[datetime, str]]) -> Optional[datetime]:
    """Safely parse a datetime or ISO 8601 string into a timezone-aware UTC datetime.

    Returns None if the timestamp is missing, empty, or unparseable.
    """
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return _ensure_utc(ts)
    if isinstance(ts, str):
        cleaned = ts.strip()
        if not cleaned:
            return None
        try:
            parsed = date_parser.isoparse(cleaned)
            return _ensure_utc(parsed)
        except (ValueError, TypeError):
            try:
                parsed = date_parser.parse(cleaned)
                return _ensure_utc(parsed)
            except (ValueError, TypeError, OverflowError):
                return None
    return None


class FreshnessEvaluator:
    """Deterministic, stateless evaluator for data source freshness."""

    def __init__(self, thresholds: Optional[FreshnessThresholds] = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def evaluate(
        self,
        last_successful_update: Optional[Union[datetime, str]],
        provider_health: ProviderHealth = ProviderHealth.HEALTHY,
        category: Optional[SourceCategory] = None,
        custom_threshold_seconds: Optional[float] = None,
        as_of_time: Optional[datetime] = None,
        latest_run_status: Optional[str] = None,
    ) -> FreshnessEvaluation:
        """Deterministically evaluate the freshness and operational usability of a data source.

        Safety invariants enforced:
        - Missing timestamp -> UNKNOWN (never FRESH, not usable)
        - Provider UNAVAILABLE -> UNAVAILABLE (never FRESH, not usable)
        - Invalid timestamp -> UNKNOWN (not usable)
        - Future timestamp beyond tolerance -> CLOCK_SKEW (never FRESH, not usable)
        - Old timestamp exceeding threshold -> STALE (not usable)
        - Recent timestamp within threshold and provider healthy/degraded -> FRESH
        """
        eval_time = _ensure_utc(as_of_time or datetime.now(timezone.utc))

        # 1. Resolve effective threshold
        if custom_threshold_seconds is not None and custom_threshold_seconds > 0:
            effective_threshold = float(custom_threshold_seconds)
        else:
            effective_threshold = self.thresholds.get_threshold_for_category(category)

        # 2. Check Provider Availability First
        if provider_health == ProviderHealth.UNAVAILABLE:
            return FreshnessEvaluation(
                status=FreshnessStatus.UNAVAILABLE,
                age_seconds=None,
                threshold_seconds=effective_threshold,
                is_usable=False,
                reason="Underlying data provider is offline or unreachable.",
                evaluated_at=eval_time,
            )

        # 3. Check for Missing or Invalid Timestamp
        if last_successful_update is None:
            reason = "No successful data update timestamp recorded for this data source."
            if latest_run_status == "failed":
                reason += " Latest ingestion attempt failed."
            return FreshnessEvaluation(
                status=FreshnessStatus.UNKNOWN,
                age_seconds=None,
                threshold_seconds=effective_threshold,
                is_usable=False,
                reason=reason,
                evaluated_at=eval_time,
            )

        parsed_ts = parse_timestamp_safe(last_successful_update)
        if parsed_ts is None:
            return FreshnessEvaluation(
                status=FreshnessStatus.UNKNOWN,
                age_seconds=None,
                threshold_seconds=effective_threshold,
                is_usable=False,
                reason=f"Invalid, corrupted, or unparseable timestamp: '{last_successful_update}'.",
                evaluated_at=eval_time,
            )

        # 4. Calculate Age & Detect Clock Skew
        age_seconds = (eval_time - parsed_ts).total_seconds()

        # Future timestamp beyond clock-skew tolerance
        if age_seconds < -self.thresholds.clock_skew_tolerance_seconds:
            return FreshnessEvaluation(
                status=FreshnessStatus.CLOCK_SKEW,
                age_seconds=age_seconds,
                threshold_seconds=effective_threshold,
                is_usable=False,
                reason=(
                    f"Timestamp '{parsed_ts.isoformat()}' is in the future by "
                    f"{-age_seconds:.1f}s (exceeds clock skew tolerance of {self.thresholds.clock_skew_tolerance_seconds}s)."
                ),
                evaluated_at=eval_time,
            )

        # Minor negative age within tolerance clamped to 0.0s
        if age_seconds < 0:
            age_seconds = 0.0

        # 5. Evaluate Fresh vs Stale
        if age_seconds <= effective_threshold:
            # Data is fresh
            if provider_health == ProviderHealth.DEGRADED:
                reason = (
                    f"Data is within freshness threshold ({age_seconds:.1f}s <= {effective_threshold:.1f}s), "
                    f"but provider reports DEGRADED health."
                )
                if latest_run_status == "failed":
                    reason += " Note: latest scheduled sync attempt failed."
            else:
                reason = (
                    f"Data is fresh ({age_seconds:.1f}s <= {effective_threshold:.1f}s)."
                )
                if latest_run_status == "failed":
                    reason += " Note: latest sync attempt failed, but previous data remains within freshness window."

            return FreshnessEvaluation(
                status=FreshnessStatus.FRESH,
                age_seconds=age_seconds,
                threshold_seconds=effective_threshold,
                is_usable=True,
                reason=reason,
                evaluated_at=eval_time,
            )
        else:
            # Data is stale
            reason = (
                f"Data is stale: elapsed age of {age_seconds:.1f}s exceeds "
                f"the freshness threshold of {effective_threshold:.1f}s."
            )
            if latest_run_status == "failed":
                reason += " Latest ingestion attempt also failed."

            return FreshnessEvaluation(
                status=FreshnessStatus.STALE,
                age_seconds=age_seconds,
                threshold_seconds=effective_threshold,
                is_usable=False,
                reason=reason,
                evaluated_at=eval_time,
            )
