"""Live Riverine Flood & Water Level Provider backed by Central Water Commission (CWC).

Parses official live flood table from CWC Advanced Flood Forecasting (AFF) system.
Returns verified river gauge observations, warning/danger levels, and flood stages.
Official URL: https://aff.india-water.gov.in/textdata/Floodday_table_view_header.txt
"""

import csv
from datetime import datetime, timezone
import io
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.request

from app.data.providers.contracts import (
    BaseDataProvider,
    NormalizedFloodRecord,
    ProviderHealth,
    ProviderMode,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
)

logger = logging.getLogger("rakshakgis.providers.cwc_flood")


class CWCFloodProvider(BaseDataProvider):
    """Authoritative live flood monitoring provider consuming official CWC daily observation tables."""

    TABLE_URL = "https://aff.india-water.gov.in/textdata/Floodday_table_view_header.txt"
    CACHE_TTL_SECONDS = 900  # 15 minute cache

    def __init__(self, timeout_sec: float = 8.0):
        self._timeout_sec = timeout_sec
        self._cached_records: Optional[List[Dict[str, str]]] = None
        self._cache_timestamp: float = 0.0

    @property
    def provider_id(self) -> str:
        return "cwc_live_flood_aff"

    @property
    def provider_name(self) -> str:
        return "Central Water Commission (CWC) Flood Forecasting Service"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.FLOOD}

    @property
    def supported_regions(self) -> Set[str]:
        return {"*"}

    @property
    def mode(self) -> ProviderMode:
        return ProviderMode.LIVE

    def check_health(self) -> ProviderHealth:
        """Verify network reachability and HTTP status of CWC live table."""
        try:
            req = urllib.request.Request(self.TABLE_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status == 200:
                    return ProviderHealth.HEALTHY
                return ProviderHealth.DEGRADED
        except Exception as exc:
            logger.warning("CWC Flood provider health check failed: %s", exc)
            return ProviderHealth.UNAVAILABLE

    def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedFloodRecord]:
        """Fetch and filter live flood monitoring station readings."""
        if query.category != SourceCategory.FLOOD:
            raise UnsupportedQueryError(
                f"CWC Flood provider does not support category '{query.category.value}'."
            )

        raw_rows = self._get_cached_or_fetch_table()

        provenance = ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=ProviderMode.LIVE,
            is_synthetic=False,
            region_id=query.region_id or "national",
            disclaimer=(
                "Official river gauge and hydrological flood observations published by "
                "Central Water Commission (CWC), Ministry of Jal Shakti, Government of India."
            ),
        )

        records = self._transform_rows(raw_rows, query, provenance)

        return ProviderResponse(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=SourceCategory.FLOOD,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )

    def _get_cached_or_fetch_table(self) -> List[Dict[str, str]]:
        """Fetch and parse CSV table with TTL caching."""
        now = time.time()
        if self._cached_records and (now - self._cache_timestamp < self.CACHE_TTL_SECONDS):
            return self._cached_records

        try:
            req = urllib.request.Request(
                self.TABLE_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status != 200:
                    raise ProviderUnavailableError(
                        f"CWC server returned HTTP status {resp.status}", provider_id=self.provider_id
                    )
                raw_bytes = resp.read()
                raw_text = raw_bytes.decode("utf-8", errors="ignore")

            reader = csv.DictReader(io.StringIO(raw_text))
            rows = [r for r in reader if r.get("Station")]
            self._cached_records = rows
            self._cache_timestamp = now
            return rows
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(
                f"Failed to fetch CWC flood observation table: {exc}", provider_id=self.provider_id
            ) from exc

    def _transform_rows(
        self,
        rows: List[Dict[str, str]],
        query: ProviderQuery,
        provenance: ProviderProvenance,
    ) -> List[NormalizedFloodRecord]:
        """Filter and convert station rows to NormalizedFloodRecord instances."""
        normalized: List[NormalizedFloodRecord] = []
        target_district = (query.district_code or "").strip().lower()
        target_region = (query.region_id or "").strip().lower()

        for idx, r in enumerate(rows):
            station = r.get("Station", "").strip()
            district = r.get("District", "").strip()
            state = r.get("State", "").strip()

            # Apply district/state filters if specified
            if target_district and target_district not in district.lower():
                continue
            if target_region and target_region != "himalayan_pilot" and target_region not in state.lower():
                continue

            try:
                lat = float(r.get("Latitude", 0.0))
                lon = float(r.get("Longitude", 0.0))
            except (ValueError, TypeError):
                continue

            if lat == 0.0 and lon == 0.0:
                continue

            # Parse water level, warning level, danger level
            try:
                water_level = float(r.get("WIMS_Value") or r.get("forecast_value_ffs") or 0.0)
            except ValueError:
                water_level = 0.0

            try:
                danger_level = float(r.get("DangerLevel") or 0.0)
            except ValueError:
                danger_level = 0.0

            try:
                warning_level = float(r.get("WarningLevel") or 0.0)
            except ValueError:
                warning_level = 0.0

            above_danger = max(0.0, water_level - danger_level) if (danger_level > 0 and water_level > 0) else 0.0
            condition = (r.get("current_condition") or r.get("ffs_condition") or "Normal").strip()

            if above_danger > 1.0 or "Severe" in condition:
                severity = "critical"
            elif above_danger > 0.0 or "Danger" in condition:
                severity = "very_high"
            elif (warning_level > 0 and water_level >= warning_level) or "Warning" in condition:
                severity = "high"
            elif water_level > 0:
                severity = "moderate"
            else:
                severity = "low"

            obs_date = r.get("Date_WIMS") or r.get("timeofforecast") or datetime.now(timezone.utc).isoformat()
            river = r.get("River", "").strip()
            clean_station_id = f"CWC_{station.replace(' ', '_').replace('/', '_')}_{idx}"

            rec = NormalizedFloodRecord(
                record_id=clean_station_id,
                observed_at=obs_date if "T" in obs_date else f"{obs_date}T00:00:00Z",
                location_coordinates=(lon, lat),
                provenance=provenance,
                village_id=query.village_id,
                village_name=station,
                flood_type="riverine_flood",
                water_level_m_above_danger=round(above_danger, 2),
                severity=severity,
                description=f"CWC Gauge Station '{station}' on River '{river}' (Stage: {water_level:.2f}m, Danger: {danger_level:.2f}m, Status: {condition})",
            )
            normalized.append(rec)

            if len(normalized) >= 50:  # Cap at top 50 relevant stations per query
                break

        return normalized
