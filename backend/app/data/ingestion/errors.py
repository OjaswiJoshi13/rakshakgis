"""Exception hierarchy for the RakshakGIS data validation and ingestion pipeline."""

from typing import Optional


class IngestionError(Exception):
    """Base exception for all ingestion pipeline failures."""

    def __init__(self, message: str, provider_id: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider_id = provider_id

    def __str__(self) -> str:
        if self.provider_id:
            return f"[{self.provider_id}] {self.message}"
        return self.message


class BatchValidationError(IngestionError):
    """Raised when an entire batch cannot be processed due to fatal batch-level structural issues."""

    pass


class UnsupportedCategoryError(IngestionError):
    """Raised when an unsupported or invalid data source category is submitted to the pipeline."""

    pass


class RecordValidationError(IngestionError):
    """Raised when strict-mode record validation encounters an invalid record."""

    def __init__(
        self,
        message: str,
        record_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        field: Optional[str] = None,
    ):
        super().__init__(message, provider_id=provider_id)
        self.record_id = record_id
        self.field = field

    def __str__(self) -> str:
        prefix = f"[{self.provider_id}] " if self.provider_id else ""
        rec = f"(record: {self.record_id}) " if self.record_id else ""
        fld = f"(field: {self.field}) " if self.field else ""
        return f"{prefix}{rec}{fld}{self.message}"
