"""Live Seismic Hazard Provider backed by USGS Earthquake Hazards Program API.

Queries real-time seismic events via public FDSN web service for regional risk adjustments.
URL: https://earthquake.usgs.gov/fdsnws/event/1/query
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.parse
import urllib.request

from app.data.providers.contracts import (
    BaseDataProvider,
    NormalizedHazardObservationRecord,
    ProviderHealth,
    ProviderMode,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
)

logger = logging.getLogger("rakshakgis.providers.usgs_earthquake")


class USGSEarthquakeProvider(BaseDataProvider):
    """Authoritative live earthquake feed consuming USGS real-time GeoJSON API."""

    API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    CACHE_TTL_SECONDS = 600  # 10 minute cache

    def __init__(self, timeout_sec: float = 6.0):
        self._timeout_sec = timeout_sec
        self._cache: Dict[str, Tuple[float, List[NormalizedHazardObservationRecord]]] = {}

    @property
    def provider_id(self) -> str:
        return "usgs_live_earthquake"

    @property
    def provider_name(self) -> str:
        return "USGS Real-Time Earthquake Hazards Service"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.HAZARD_OBSERVATION}

    @property
    def supported_regions(self) -> Set[str]:
        return {"*"}

    @property
    def mode(self) -> ProviderMode:
        return ProviderMode.LIVE

    def check_health(self) -> ProviderHealth:
        """Probe USGS API availability with minimal query."""
        try:
            params = urllib.parse.urlencode({
                "format": "geojson",
                "limit": 1,
                "minmagnitude": 5.0,
            })
            url = f"{self.API_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "RakshakGIS/1.0"})
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status == 200:
                    return ProviderHealth.HEALTHY
                return ProviderHealth.DEGRADED
        except Exception as exc:
            logger.warning("USGS Earthquake health check failed: %s", exc)
            return ProviderHealth.UNAVAILABLE

    def fetch_data(
        self, query: ProviderQuery
    ) -> ProviderResponse[NormalizedHazardObservationRecord]:
        """Fetch real-time seismic events within regional bounding radius."""
        if query.category != SourceCategory.HAZARD_OBSERVATION:
            raise UnsupportedQueryError(
                f"USGS Earthquake provider does not support category '{query.category.value}'."
            )

        lat, lon = self._resolve_center_point(query)
        cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
        now = time.time()

        if cache_key in self._cache:
            cached_time, cached_records = self._cache[cache_key]
            if now - cached_time < self.CACHE_TTL_SECONDS:
                records = cached_records
            else:
                records = self._fetch_and_parse(lat, lon, query)
                self._cache[cache_key] = (now, records)
        else:
            records = self._fetch_and_parse(lat, lon, query)
            self._cache[cache_key] = (now, records)

        provenance = ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=ProviderMode.LIVE,
            is_synthetic=False,
            region_id=query.region_id or "global",
            disclaimer=(
                "Authoritative real-time seismic data from USGS Earthquake Hazards Program. "
                "FDSN web services; public domain."
            ),
        )

        return ProviderResponse(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=SourceCategory.HAZARD_OBSERVATION,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )

    def _resolve_center_point(self, query: ProviderQuery) -> Tuple[float, float]:
        fc = query.filter_criteria or {}
        if "latitude" in fc and "longitude" in fc:
            return float(fc["latitude"]), float(fc["longitude"])
        if query.region_id == "himalayan_pilot" or query.district_code == "chamoli":
            return 30.556, 79.563
        return 28.6139, 77.2090

    def _fetch_and_parse(
        self, lat: float, lon: float, query: ProviderQuery
    ) -> List[NormalizedHazardObservationRecord]:
        """Call USGS API and convert GeoJSON features to NormalizedHazardObservationRecord."""
        start_time = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        params = urllib.parse.urlencode({
            "format": "geojson",
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "maxradiuskm": 500,  # 500 km radius
            "minmagnitude": 2.5,
            "starttime": start_time,
            "limit": 30,
        })
        url = f"{self.API_URL}?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RakshakGIS/1.0"})
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status != 200:
                    raise ProviderUnavailableError(
                        f"USGS returned status {resp.status}", provider_id=self.provider_id
                    )
                raw_json = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(
                f"Failed to query USGS Earthquake API: {exc}", provider_id=self.provider_id
            ) from exc

        provenance = ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=ProviderMode.LIVE,
            is_synthetic=False,
            region_id=query.region_id or "global",
        )

        records: List[NormalizedHazardObservationRecord] = []
        features = raw_json.get("features", [])

        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0.0, 0.0, 0.0])
            f_lon, f_lat = float(coords[0]), float(coords[1])
            depth_km = float(coords[2]) if len(coords) > 2 else 10.0

            mag = float(props.get("mag") or 0.0)
            place = props.get("place") or "Unknown"
            epoch_ms = props.get("time") or 0
            obs_dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc).isoformat()

            if mag >= 6.0:
                severity = "critical"
            elif mag >= 5.0:
                severity = "very_high"
            elif mag >= 4.0:
                severity = "high"
            elif mag >= 3.0:
                severity = "moderate"
            else:
                severity = "low"

            rec_id = f"USGS_{feat.get('id', str(epoch_ms))}"
            rec = NormalizedHazardObservationRecord(
                record_id=rec_id,
                observed_at=obs_dt,
                location_coordinates=(f_lon, f_lat),
                provenance=provenance,
                hazard_type="seismic",
                village_id=query.village_id,
                village_name=place,
                severity=severity,
                intensity_value=round(mag, 2),
                intensity_unit="richter_magnitude",
                description=f"Earthquake M{mag:.1f} - {place} (Depth: {depth_km:.1f} km)",
            )
            records.append(rec)

        return records
