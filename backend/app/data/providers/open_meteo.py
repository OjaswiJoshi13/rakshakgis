"""Live Weather & Rainfall Provider backed by Open-Meteo API.

Provides real-time precipitation, 24h rolling rainfall, and forecast metrics
for dynamic risk adjustments and flood susceptibility.
Attribution: Open-Meteo (open-meteo.com) - Non-commercial CC-BY 4.0.
CRITICAL: Do NOT label Open-Meteo as IMD.
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.parse
import urllib.request

from app.data.providers.contracts import (
    BaseDataProvider,
    NormalizedRainfallRecord,
    ProviderHealth,
    ProviderMode,
    ProviderPayloadError,
    ProviderProvenance,
    ProviderQuery,
    ProviderResponse,
    ProviderUnavailableError,
    SourceCategory,
    UnsupportedQueryError,
)

logger = logging.getLogger("rakshakgis.providers.open_meteo")


class OpenMeteoWeatherProvider(BaseDataProvider):
    """Authoritative live weather & precipitation provider via Open-Meteo REST API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_TTL_SECONDS = 300  # 5 minute cache to respect public rate limits

    def __init__(self, timeout_sec: float = 5.0):
        self._timeout_sec = timeout_sec
        self._cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}

    @property
    def provider_id(self) -> str:
        return "open_meteo_live_weather"

    @property
    def provider_name(self) -> str:
        return "Open-Meteo Live Weather & Rainfall Service"

    @property
    def supported_categories(self) -> Set[SourceCategory]:
        return {SourceCategory.RAINFALL}

    @property
    def supported_regions(self) -> Set[str]:
        # Asterisk wildcard for global / multi-regional support
        return {"*"}

    @property
    def mode(self) -> ProviderMode:
        return ProviderMode.LIVE

    def check_health(self) -> ProviderHealth:
        """Verify network reachability and HTTP status of Open-Meteo API."""
        try:
            params = urllib.parse.urlencode({
                "latitude": 30.55,
                "longitude": 79.56,
                "current": "precipitation",
            })
            url = f"{self.BASE_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "RakshakGIS-DisasterPlatform/1.0"})
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status == 200:
                    return ProviderHealth.HEALTHY
                return ProviderHealth.DEGRADED
        except Exception as exc:
            logger.warning("Open-Meteo health check failed: %s", exc)
            return ProviderHealth.UNAVAILABLE

    def fetch_data(self, query: ProviderQuery) -> ProviderResponse[NormalizedRainfallRecord]:
        """Fetch live rainfall observations for given coordinates or region."""
        if query.category != SourceCategory.RAINFALL:
            raise UnsupportedQueryError(
                f"Open-Meteo provider does not support category '{query.category.value}'."
            )

        lat, lon = self._resolve_coordinates(query)
        raw_data = self._fetch_open_meteo(lat, lon)
        
        provenance = ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=ProviderMode.LIVE,
            is_synthetic=False,
            region_id=query.region_id or "global",
            disclaimer=(
                "Authoritative live weather and precipitation data provided by Open-Meteo. "
                "Non-commercial open weather models (ECMWF, GFS). Not official statutory IMD bulletin."
            ),
        )

        records = self._transform_to_canonical(lat, lon, raw_data, provenance, query)

        return ProviderResponse(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=SourceCategory.RAINFALL,
            query=query,
            records=records,
            total_count=len(records),
            provenance=provenance,
        )

    def _resolve_coordinates(self, query: ProviderQuery) -> Tuple[float, float]:
        """Extract lat/lon from query parameters or default to regional centroid."""
        fc = getattr(query, "filter_criteria", None) or {}
        if "latitude" in fc and "longitude" in fc:
            return float(fc["latitude"]), float(fc["longitude"])

        if query.region_id == "himalayan_pilot" or query.district_code == "chamoli":
            return 30.556, 79.563

        return 28.6139, 77.2090

    def _fetch_open_meteo(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch raw JSON from Open-Meteo with in-memory TTL caching."""
        rounded_key = (round(lat, 3), round(lon, 3))
        now = time.time()

        if rounded_key in self._cache:
            cached_time, cached_payload = self._cache[rounded_key]
            if now - cached_time < self.CACHE_TTL_SECONDS:
                return cached_payload

        params = urllib.parse.urlencode({
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m",
            "daily": "precipitation_sum,precipitation_hours",
            "timezone": "UTC",
        })
        url = f"{self.BASE_URL}?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RakshakGIS-DisasterPlatform/1.0"})
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                if resp.status != 200:
                    raise ProviderUnavailableError(
                        f"Open-Meteo returned HTTP status {resp.status}", provider_id=self.provider_id
                    )
                data = json.loads(resp.read().decode("utf-8"))
                self._cache[rounded_key] = (now, data)
                return data
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(
                f"Failed to connect to Open-Meteo live API: {exc}", provider_id=self.provider_id
            ) from exc

    def _transform_to_canonical(
        self,
        lat: float,
        lon: float,
        data: Dict[str, Any],
        provenance: ProviderProvenance,
        query: ProviderQuery,
    ) -> List[NormalizedRainfallRecord]:
        """Convert Open-Meteo response into typed NormalizedRainfallRecord."""
        current = data.get("current", {})
        daily = data.get("daily", {})

        current_rain_mm = float(current.get("rain", current.get("precipitation", 0.0)))
        daily_sums = daily.get("precipitation_sum", [])
        rolling_24h_mm = float(daily_sums[0]) if daily_sums else current_rain_mm

        is_heavy = rolling_24h_mm >= 64.5
        is_very_heavy = rolling_24h_mm >= 115.5

        if rolling_24h_mm >= 204.4:
            severity = "critical"
        elif is_very_heavy:
            severity = "very_high"
        elif is_heavy:
            severity = "high"
        elif rolling_24h_mm >= 15.5:
            severity = "moderate"
        else:
            severity = "low"

        obs_time = current.get("time") or datetime.now(timezone.utc).isoformat()
        if "T" not in obs_time:
            obs_time = f"{obs_time}T00:00:00Z"
        elif not obs_time.endswith("Z") and "+" not in obs_time:
            obs_time = f"{obs_time}Z"

        record_id = f"OM_{round(lat, 3)}_{round(lon, 3)}_{obs_time[:13].replace(':', '')}"

        record = NormalizedRainfallRecord(
            record_id=record_id,
            observed_at=obs_time,
            location_coordinates=(lon, lat),
            provenance=provenance,
            village_id=query.village_id,
            rainfall_24h_mm=round(rolling_24h_mm, 2),
            severity=severity,
            is_heavy_rain=is_heavy,
            is_very_heavy_rain=is_very_heavy,
            description=f"Live Open-Meteo precipitation observation (current: {current_rain_mm:.1f} mm, 24h: {rolling_24h_mm:.1f} mm)",
        )

        return [record]
