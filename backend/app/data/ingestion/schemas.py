"""Typed schemas for data validation issues, rejected records, canonical records, and ingestion results."""

from enum import Enum
from typing import Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field

from app.data.providers.contracts import (
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderMode,
    ProviderProvenance,
    SourceCategory,
)


class ValidationIssueCode(str, Enum):
    """Categorical classification of validation failures."""

    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_IDENTITY = "INVALID_IDENTITY"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    COORDINATES_OUT_OF_BOUNDS = "COORDINATES_OUT_OF_BOUNDS"
    INVALID_NUMERIC_VALUE = "INVALID_NUMERIC_VALUE"
    NUMERIC_OUT_OF_DOMAIN = "NUMERIC_OUT_OF_DOMAIN"
    INVALID_SEVERITY = "INVALID_SEVERITY"
    INVALID_HAZARD_TYPE = "INVALID_HAZARD_TYPE"
    INVALID_CATEGORY = "INVALID_CATEGORY"
    INVALID_PROVENANCE = "INVALID_PROVENANCE"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    MALFORMED_RECORD = "MALFORMED_RECORD"


class ValidationSeverity(str, Enum):
    """Severity classification for validation diagnostic issues."""

    ERROR = "error"
    WARNING = "warning"


class ValidationIssue(BaseModel):
    """Detailed record-level or field-level validation diagnostic issue."""

    model_config = ConfigDict(frozen=True)

    record_id: Optional[str] = None
    field: Optional[str] = None
    code: ValidationIssueCode
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


class RejectedRecord(BaseModel):
    """Encapsulation of a rejected record with index, identifier, and causal validation issues."""

    model_config = ConfigDict(frozen=True)

    record_id: Optional[str] = None
    index: int
    raw_summary: Optional[str] = None
    issues: List[ValidationIssue]


class IngestionBatchMetadata(BaseModel):
    """Deterministic metadata describing the execution context of an ingestion batch."""

    model_config = ConfigDict(frozen=True)

    batch_id: str
    processed_at: str  # ISO-8601 string
    pipeline_version: str = "1.0.0"
    is_synthetic: bool = True


# =====================================================================
# Canonical Ingested Records (Extending M3-03 Normalized Records)
# =====================================================================


class CanonicalRainfallRecord(NormalizedRainfallRecord):
    """Canonicalized precipitation observation record with ingestion provenance."""

    ingested_at: str
    batch_id: str
    canonical_hash: str


class CanonicalFloodRecord(NormalizedFloodRecord):
    """Canonicalized flood / hydrological observation record with ingestion provenance."""

    ingested_at: str
    batch_id: str
    canonical_hash: str


class CanonicalLandslideRecord(NormalizedLandslideRecord):
    """Canonicalized landslide observation record with ingestion provenance."""

    ingested_at: str
    batch_id: str
    canonical_hash: str


class CanonicalHazardObservationRecord(NormalizedHazardObservationRecord):
    """Canonicalized multi-hazard sensor observation record with ingestion provenance."""

    ingested_at: str
    batch_id: str
    canonical_hash: str


class CanonicalPopulationRecord(NormalizedPopulationRecord):
    """Canonicalized demographic exposure record with ingestion provenance."""

    ingested_at: str
    batch_id: str
    canonical_hash: str


CanonicalRecord = Union[
    CanonicalRainfallRecord,
    CanonicalFloodRecord,
    CanonicalLandslideRecord,
    CanonicalHazardObservationRecord,
    CanonicalPopulationRecord,
]


# =====================================================================
# Ingestion Result Envelope
# =====================================================================

T = TypeVar("T")


class IngestionResult(BaseModel, Generic[T]):
    """Standardized result envelope returned by the ingestion pipeline."""

    model_config = ConfigDict(frozen=True)

    provider_id: str
    provider_name: str
    category: SourceCategory
    total_input_count: int
    accepted_count: int
    rejected_count: int
    accepted_records: List[T]
    rejected_records: List[RejectedRecord]
    validation_issues: List[ValidationIssue]
    provenance: ProviderProvenance
    metadata: IngestionBatchMetadata
