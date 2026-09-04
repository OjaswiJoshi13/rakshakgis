"""RakshakGIS Data Validation & Ingestion Pipelines Package (Chunk M3-04)."""

from app.data.ingestion.errors import (
    BatchValidationError,
    IngestionError,
    RecordValidationError,
    UnsupportedCategoryError,
)
from app.data.ingestion.pipeline import (
    IngestionPipeline,
    ingest_batch,
    ingest_provider_response,
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
    ValidationSeverity,
)
from app.data.ingestion.validators import (
    validate_coordinates,
    validate_identity,
    validate_numeric,
    validate_provenance,
    validate_record,
    validate_timestamp,
)

__all__ = [
    # Pipeline
    "IngestionPipeline",
    "ingest_provider_response",
    "ingest_batch",
    # Result & Diagnostic Schemas
    "IngestionResult",
    "IngestionBatchMetadata",
    "RejectedRecord",
    "ValidationIssue",
    "ValidationIssueCode",
    "ValidationSeverity",
    # Canonical Record Models
    "CanonicalRecord",
    "CanonicalRainfallRecord",
    "CanonicalFloodRecord",
    "CanonicalLandslideRecord",
    "CanonicalHazardObservationRecord",
    "CanonicalPopulationRecord",
    # Exceptions
    "IngestionError",
    "BatchValidationError",
    "UnsupportedCategoryError",
    "RecordValidationError",
    # Validators
    "validate_record",
    "validate_identity",
    "validate_timestamp",
    "validate_coordinates",
    "validate_numeric",
    "validate_provenance",
]
