"""National Centre for Seismology (NCS) Earthquake Catalog Provider.

Consumes verified earthquake observations from NCS MoES bulletin spreadsheet.
File path: data/raw/ncs/Official Website of National Center of Seismology.xlsx
"""

from datetime import datetime, timezone
import logging
import os
from typing import List, Optional, Set, Tuple
import pandas as pd

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

logger = logging.getLogger("rakshakgis.providers.ncs_earthquake")


class NCSEarthquakeProvider(BaseDataProvider):
    """Authoritative static earthquake catalog provider from National Centre for Seismology."""

    DEFAULT_FILE_PATH = os.path.join(
        "data", "raw", "ncs", "Official Website of National Center of Seismology.xlsx"
    )

    def __init__(self, file_path: Optional[str] = None):
        self._file_path = file_path or self.DEFAULT_FILE_PATH
        self._cached_records: Optional[List[NormalizedHazardObservationRecord]] = None

    @property
    def provider_id(self) -> str:
        return "ncs_official_seismology"

    @property
    def provider_name(self) -> str:
        return "National Centre for Seismology (NCS) Official Earthquake Catalog"

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
        """Verify local spreadsheet file exists and is readable."""
        if os.path.exists(self._file_path):
            return ProviderHealth.HEALTHY
        return ProviderHealth.UNAVAILABLE

    def fetch_data(
        self, query: ProviderQuery
    ) -> ProviderResponse[NormalizedHazardObservationRecord]:
        """Fetch normalized seismic records from NCS catalog."""
        if query.category != SourceCategory.HAZARD_OBSERVATION:
            raise UnsupportedQueryError(
                f"NCS Seismology provider does not support category '{query.category.value}'."
            )

        if not os.path.exists(self._file_path):
            raise ProviderUnavailableError(
                f"NCS earthquake file not found at expected path: {self._file_path}",
                provider_id=self.provider_id,
            )

        provenance = ProviderProvenance(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            mode=ProviderMode.LIVE,
            is_synthetic=False,
            region_id=query.region_id or "national",
            disclaimer=(
                "Official earthquake bulletin published by National Centre for Seismology (NCS), "
                "Ministry of Earth Sciences, Government of India."
            ),
        )

        all_records = self._load_records(provenance)

        # Filter by region or bounding radius if requested
        filtered = self._filter_records(all_records, query)

        return ProviderResponse(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            category=SourceCategory.HAZARD_OBSERVATION,
            query=query,
            records=filtered,
            total_count=len(filtered),
            provenance=provenance,
        )

    def _load_records(
        self, provenance: ProviderProvenance
    ) -> List[NormalizedHazardObservationRecord]:
        if self._cached_records is not None:
            return self._cached_records

        try:
            df = pd.read_excel(self._file_path, header=1)
        except Exception as exc:
            raise ProviderUnavailableError(
                f"Failed to read NCS spreadsheet: {exc}", provider_id=self.provider_id
            ) from exc

        records: List[NormalizedHazardObservationRecord] = []

        for idx, row in df.iterrows():
            try:
                mag = float(row.get("Magnitude", 0.0))
                lat = float(row.get("Lat", 0.0))
                lon = float(row.get("Long", 0.0))
                depth = float(row.get("Depth", 10.0))
                location = str(row.get("Location", "") or row.get("Region", "India"))
                origin_time_raw = str(row.get("Origin Time", ""))

                if lat == 0.0 and lon == 0.0:
                    continue

                if " " in origin_time_raw:
                    obs_iso = origin_time_raw.replace(" ", "T") + "Z"
                else:
                    obs_iso = f"{origin_time_raw}T00:00:00Z"

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

                rec_id = f"NCS_EQ_{idx}_{obs_iso[:10].replace('-', '')}"
                rec = NormalizedHazardObservationRecord(
                    record_id=rec_id,
                    observed_at=obs_iso,
                    location_coordinates=(lon, lat),
                    provenance=provenance,
                    hazard_type="seismic",
                    village_name=location,
                    severity=severity,
                    intensity_value=round(mag, 2),
                    intensity_unit="richter_magnitude",
                    description=f"NCS Seismic Event M{mag:.1f} at {location} (Depth: {depth:.0f} km)",
                )
                records.append(rec)
            except Exception as e:
                logger.debug("Skipping row %d in NCS catalog: %s", idx, e)
                continue

        self._cached_records = records
        return records

    def _filter_records(
        self, records: List[NormalizedHazardObservationRecord], query: ProviderQuery
    ) -> List[NormalizedHazardObservationRecord]:
        target_region = (query.region_id or "").lower()
        if not target_region or target_region == "national" or target_region == "india":
            return records[:50]

        # If himalayan_pilot / chamoli, prioritize Himalayan records
        if "himalayan" in target_region or "chamoli" in target_region or "uttarakhand" in target_region:
            matched = [
                r for r in records
                if any(k in (r.description or "").lower() for k in ["uttarakhand", "chamoli", "himalay", "tibetan", "nepal", "delhi", "himachal"])
            ]
            return matched if matched else records[:30]

        return records[:50]
