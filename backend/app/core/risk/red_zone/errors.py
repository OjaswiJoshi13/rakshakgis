"""Exception hierarchy for Permanent Red Zone Demarcation (Chunk M3-10)."""

from typing import Optional


class RedZoneError(Exception):
    """Base exception for all Red Zone demarcation and evaluation errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidGeophysicalDataError(RedZoneError):
    """Raised when geophysical input values violate physical domains (e.g. NaN, Inf, slope > 90 deg)."""


class InsufficientGeophysicalDataError(RedZoneError):
    """Raised when required geophysical indicators are missing under strict data policies."""

    def __init__(
        self,
        message: str,
        missing_fields: Optional[list] = None,
        details: Optional[dict] = None,
    ) -> None:
        details_dict = details or {}
        if missing_fields:
            details_dict["missing_fields"] = missing_fields
        super().__init__(message, details=details_dict)
        self.missing_fields = missing_fields or []


class SpatialGeometryError(RedZoneError):
    """Raised when geometry inputs are invalid, unprojectable, or fail topological normalization."""


class RedZoneConfigError(RedZoneError):
    """Raised when regional configuration or red zone thresholds are invalid."""
