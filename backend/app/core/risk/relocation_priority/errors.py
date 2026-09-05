"""Exception hierarchy for Relocation Priority Scoring (Chunk M3-12)."""

from typing import Any, Dict, List, Optional


class RelocationPriorityError(Exception):
    """Base exception for all relocation priority scoring errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidPriorityDataError(RelocationPriorityError):
    """Raised when priority factor inputs violate numerical boundaries ([0.0, 100.0], NaN, Inf)."""


class InsufficientPriorityDataError(RelocationPriorityError):
    """Raised when required priority factors are missing or unavailable under strict evaluation policies."""

    def __init__(
        self,
        message: str,
        missing_fields: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details_dict = details or {}
        if missing_fields:
            details_dict["missing_fields"] = missing_fields
        super().__init__(message, details=details_dict)
        self.missing_fields = missing_fields or []


class PriorityConfigError(RelocationPriorityError):
    """Raised when regional profile weights, factor definitions, or band cutoffs are invalid."""
