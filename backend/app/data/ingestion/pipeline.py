"""Main IngestionPipeline coordinating batch validation, canonicalization, and result envelope generation."""

from datetime import datetime
import hashlib
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from app.data.ingestion.errors import (
    BatchValidationError,
    UnsupportedCategoryError,
)
from app.data.ingestion.schemas import (
    CanonicalFloodRecord,
    CanonicalHazardObservationRecord,
    CanonicalLandslideRecord,
    CanonicalPopulationRecord,
    CanonicalRainfallRecord,
    CanonicalRecord,
    IngestionBatchMetadata,
    IngestionResult,
    RejectedRecord,
    ValidationIssue,
    ValidationIssueCode,
)
from app.data.ingestion.validators import (
    get_field,
    validate_record,
)
from app.data.providers.contracts import (
    ProviderMode,
    ProviderProvenance,
    ProviderResponse,
    SourceCategory,
)

T = TypeVar("T")


class IngestionPipeline:
    """Deterministic validation, normalization, and ingestion pipeline for environmental data."""

    def __init__(self, pipeline_version: str = "1.0.0"):
        self.pipeline_version = pipeline_version

    def ingest_provider_response(
        self,
        response: ProviderResponse[Any],
        batch_id: Optional[str] = None,
        processed_at: Optional[str] = None,
    ) -> IngestionResult[CanonicalRecord]:
        """Ingest and validate records directly from an M3-03 ProviderResponse envelope."""
        if not isinstance(response, ProviderResponse):
            raise BatchValidationError(
                f"Expected ProviderResponse instance, got {type(response).__name__}."
            )

        return self.ingest_batch(
            category=response.category,
            records=response.records,
            provenance=response.provenance,
            provider_id=response.provider_id,
            provider_name=response.provider_name,
            batch_id=batch_id,
            processed_at=processed_at,
        )

    def ingest_batch(
        self,
        category: SourceCategory,
        records: List[Any],
        provenance: ProviderProvenance,
        provider_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        batch_id: Optional[str] = None,
        processed_at: Optional[str] = None,
    ) -> IngestionResult[CanonicalRecord]:
        """Validate, deduplicate, and canonicalize a batch of input records."""
        # 1. Envelope & Category Validation
        if not isinstance(category, SourceCategory):
            try:
                category = SourceCategory(str(category))
            except (ValueError, TypeError):
                raise UnsupportedCategoryError(
                    f"Unsupported or invalid SourceCategory: '{category}'."
                )

        if not provenance:
            raise BatchValidationError("Missing required batch provenance.")

        resolved_provider_id = provider_id or provenance.provider_id
        resolved_provider_name = provider_name or provenance.provider_name

        total_input_count = len(records)
        accepted_records: List[CanonicalRecord] = []
        rejected_records: List[RejectedRecord] = []
        all_validation_issues: List[ValidationIssue] = []

        seen_record_ids: set = set()

        # 2. Stage-by-stage Record Validation
        for idx, rec in enumerate(records):
            rec_id, issues = validate_record(rec, category)

            if issues:
                all_validation_issues.extend(issues)
                safe_summary = (
                    f"Type: {type(rec).__name__}, ID: {rec_id or 'unknown'}, "
                    f"Errors: {[i.code.value for i in issues]}"
                )
                rejected_records.append(
                    RejectedRecord(
                        record_id=rec_id,
                        index=idx,
                        raw_summary=safe_summary,
                        issues=issues,
                    )
                )
                continue

            # 3. Intra-batch Duplicate Detection
            if rec_id in seen_record_ids:
                dup_issue = ValidationIssue(
                    record_id=rec_id,
                    field="village_id" if category == SourceCategory.POPULATION_EXPOSURE else "record_id",
                    code=ValidationIssueCode.DUPLICATE_RECORD,
                    message=f"Duplicate record identifier '{rec_id}' detected in batch.",
                )
                all_validation_issues.append(dup_issue)
                rejected_records.append(
                    RejectedRecord(
                        record_id=rec_id,
                        index=idx,
                        raw_summary=f"Duplicate of already processed record '{rec_id}'",
                        issues=[dup_issue],
                    )
                )
                continue

            seen_record_ids.add(rec_id)

            # 4. Canonicalization
            canonical_rec = self._canonicalize_record(
                rec=rec,
                category=category,
                record_id=rec_id,
                batch_id=batch_id or "PENDING",
                provenance=provenance,
            )
            accepted_records.append(canonical_rec)

        # 5. Deterministic Batch Metadata Generation
        final_batch_id, final_processed_at = self._compute_deterministic_metadata(
            provider_id=resolved_provider_id,
            category=category,
            records=records,
            accepted_records=accepted_records,
            explicit_batch_id=batch_id,
            explicit_processed_at=processed_at,
        )

        # Update batch_id in accepted records if it was dynamically computed
        if batch_id is None:
            updated_accepted = []
            for r in accepted_records:
                # Re-create with exact batch_id
                r_dict = r.model_dump()
                r_dict["batch_id"] = final_batch_id
                updated_accepted.append(r.__class__(**r_dict))
            accepted_records = updated_accepted

        # 6. Deterministic Output Sorting
        if category == SourceCategory.POPULATION_EXPOSURE:
            accepted_records.sort(key=lambda r: r.village_id)
        else:
            accepted_records.sort(key=lambda r: (r.observed_at, r.record_id))

        rejected_records.sort(key=lambda r: r.index)

        metadata = IngestionBatchMetadata(
            batch_id=final_batch_id,
            processed_at=final_processed_at,
            pipeline_version=self.pipeline_version,
            is_synthetic=provenance.is_synthetic,
        )

        return IngestionResult[CanonicalRecord](
            provider_id=resolved_provider_id,
            provider_name=resolved_provider_name,
            category=category,
            total_input_count=total_input_count,
            accepted_count=len(accepted_records),
            rejected_count=len(rejected_records),
            accepted_records=accepted_records,
            rejected_records=rejected_records,
            validation_issues=all_validation_issues,
            provenance=provenance,
            metadata=metadata,
        )

    def _canonicalize_record(
        self,
        rec: Any,
        category: SourceCategory,
        record_id: str,
        batch_id: str,
        provenance: ProviderProvenance,
    ) -> CanonicalRecord:
        """Canonicalize coordinates, timestamps, and compute deterministic hash."""
        coords = get_field(rec, "location_coordinates")
        canonical_coords = (round(float(coords[0]), 6), round(float(coords[1]), 6))

        # Provenance on record
        rec_prov = get_field(rec, "provenance") or provenance

        if category == SourceCategory.POPULATION_EXPOSURE:
            v_id = get_field(rec, "village_id")
            v_name = (get_field(rec, "village_name") or "").strip()
            reg_code = (get_field(rec, "region_code") or "").strip()
            dist_code = (get_field(rec, "district_code") or "").strip()
            blk_code = (get_field(rec, "block_code") or "").strip()
            tot_pop = int(get_field(rec, "total_population"))
            hh = int(get_field(rec, "households"))
            elderly = int(get_field(rec, "elderly_count"))
            children = int(get_field(rec, "children_count"))
            disabled = int(get_field(rec, "disabled_count"))
            livestock = int(get_field(rec, "livestock_count"))

            hash_payload = (
                f"{v_id}|{canonical_coords[0]}|{canonical_coords[1]}|"
                f"{tot_pop}|{hh}|{elderly}|{children}|{disabled}|{livestock}"
            )
            canonical_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

            return CanonicalPopulationRecord(
                village_id=v_id,
                village_name=v_name,
                region_code=reg_code,
                district_code=dist_code,
                block_code=blk_code,
                location_coordinates=canonical_coords,
                total_population=tot_pop,
                households=hh,
                elderly_count=elderly,
                children_count=children,
                disabled_count=disabled,
                livestock_count=livestock,
                provenance=rec_prov,
                ingested_at="2026-09-05T00:00:00Z",
                batch_id=batch_id,
                canonical_hash=canonical_hash,
            )

        # Observation categories
        raw_obs = get_field(rec, "observed_at")
        clean_ts = datetime.fromisoformat(raw_obs.replace("Z", "+00:00")).isoformat()
        village_id = get_field(rec, "village_id")
        village_name = get_field(rec, "village_name")
        if village_name:
            village_name = village_name.strip()
        severity = (get_field(rec, "severity") or "moderate").lower().strip()
        description = get_field(rec, "description")
        if description:
            description = description.strip()

        if category == SourceCategory.RAINFALL:
            rain_mm = float(get_field(rec, "rainfall_24h_mm"))
            is_heavy = bool(get_field(rec, "is_heavy_rain"))
            is_very_heavy = bool(get_field(rec, "is_very_heavy_rain"))
            hash_payload = f"{record_id}|{clean_ts}|{canonical_coords[0]}|{canonical_coords[1]}|{rain_mm}"
            canonical_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

            return CanonicalRainfallRecord(
                record_id=record_id,
                observed_at=clean_ts,
                location_coordinates=canonical_coords,
                provenance=rec_prov,
                village_id=village_id,
                village_name=village_name,
                rainfall_24h_mm=rain_mm,
                severity=severity,
                is_heavy_rain=is_heavy,
                is_very_heavy_rain=is_very_heavy,
                description=description,
                ingested_at=clean_ts,
                batch_id=batch_id,
                canonical_hash=canonical_hash,
            )

        elif category == SourceCategory.FLOOD:
            water_level = float(get_field(rec, "water_level_m_above_danger"))
            flood_type = (get_field(rec, "flood_type") or "flash_flood").strip()
            hash_payload = f"{record_id}|{clean_ts}|{canonical_coords[0]}|{canonical_coords[1]}|{water_level}"
            canonical_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

            return CanonicalFloodRecord(
                record_id=record_id,
                observed_at=clean_ts,
                location_coordinates=canonical_coords,
                provenance=rec_prov,
                village_id=village_id,
                village_name=village_name,
                flood_type=flood_type,
                water_level_m_above_danger=water_level,
                severity=severity,
                description=description,
                ingested_at=clean_ts,
                batch_id=batch_id,
                canonical_hash=canonical_hash,
            )

        elif category == SourceCategory.LANDSLIDE:
            debris_vol = float(get_field(rec, "debris_volume_cu_m"))
            road_blocked = bool(get_field(rec, "road_blocked"))
            hash_payload = f"{record_id}|{clean_ts}|{canonical_coords[0]}|{canonical_coords[1]}|{debris_vol}"
            canonical_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

            return CanonicalLandslideRecord(
                record_id=record_id,
                observed_at=clean_ts,
                location_coordinates=canonical_coords,
                provenance=rec_prov,
                village_id=village_id,
                village_name=village_name,
                debris_volume_cu_m=debris_vol,
                severity=severity,
                road_blocked=road_blocked,
                description=description,
                ingested_at=clean_ts,
                batch_id=batch_id,
                canonical_hash=canonical_hash,
            )

        elif category == SourceCategory.HAZARD_OBSERVATION:
            haz_type = (get_field(rec, "hazard_type") or "unknown").strip().lower()
            intensity_val = float(get_field(rec, "intensity_value"))
            intensity_unit = (get_field(rec, "intensity_unit") or "").strip()
            hash_payload = (
                f"{record_id}|{clean_ts}|{canonical_coords[0]}|{canonical_coords[1]}|"
                f"{haz_type}|{intensity_val}|{intensity_unit}"
            )
            canonical_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

            return CanonicalHazardObservationRecord(
                record_id=record_id,
                observed_at=clean_ts,
                location_coordinates=canonical_coords,
                provenance=rec_prov,
                hazard_type=haz_type,
                village_id=village_id,
                village_name=village_name,
                severity=severity,
                intensity_value=intensity_val,
                intensity_unit=intensity_unit,
                description=description,
                ingested_at=clean_ts,
                batch_id=batch_id,
                canonical_hash=canonical_hash,
            )

        raise UnsupportedCategoryError(f"Cannot canonicalize category: '{category}'")

    def _compute_deterministic_metadata(
        self,
        provider_id: str,
        category: SourceCategory,
        records: List[Any],
        accepted_records: List[CanonicalRecord],
        explicit_batch_id: Optional[str] = None,
        explicit_processed_at: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Derive strictly deterministic batch_id and processed_at timestamp."""
        # 1. Batch ID
        if explicit_batch_id:
            batch_id = explicit_batch_id
        else:
            seed_parts = [provider_id, category.value]
            for r in records:
                r_id = get_field(r, "record_id") or get_field(r, "village_id") or "null"
                seed_parts.append(str(r_id))
            digest = hashlib.sha256(":".join(seed_parts).encode()).hexdigest()[:12]
            batch_id = f"BATCH-{digest}"

        # 2. Processed At
        if explicit_processed_at:
            processed_at = explicit_processed_at
        else:
            # Deterministically use latest timestamp from accepted records, or deterministic default
            timestamps = []
            for r in accepted_records:
                if hasattr(r, "observed_at") and r.observed_at:
                    timestamps.append(r.observed_at)
            if timestamps:
                processed_at = max(timestamps)
            else:
                processed_at = "2026-09-05T00:00:00Z"

        return batch_id, processed_at


# Default pipeline instance
_DEFAULT_PIPELINE = IngestionPipeline()


def ingest_provider_response(
    response: ProviderResponse[Any],
    batch_id: Optional[str] = None,
    processed_at: Optional[str] = None,
) -> IngestionResult[CanonicalRecord]:
    """Convenience function to ingest data via default IngestionPipeline."""
    return _DEFAULT_PIPELINE.ingest_provider_response(
        response=response, batch_id=batch_id, processed_at=processed_at
    )


def ingest_batch(
    category: SourceCategory,
    records: List[Any],
    provenance: ProviderProvenance,
    provider_id: Optional[str] = None,
    provider_name: Optional[str] = None,
    batch_id: Optional[str] = None,
    processed_at: Optional[str] = None,
) -> IngestionResult[CanonicalRecord]:
    """Convenience function to ingest a batch via default IngestionPipeline."""
    return _DEFAULT_PIPELINE.ingest_batch(
        category=category,
        records=records,
        provenance=provenance,
        provider_id=provider_id,
        provider_name=provider_name,
        batch_id=batch_id,
        processed_at=processed_at,
    )
