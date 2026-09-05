"""Exception hierarchy for the Relocation Matching & Assignment Engine (Chunk M4-04)."""

from typing import Optional


class RelocationMatchingError(Exception):
    """Base exception for all relocation matching and assignment errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidMatchingInputError(RelocationMatchingError):
    """Raised when village demand, site data, or matching parameters violate domain constraints."""

    pass


class MatchingConfigurationError(RelocationMatchingError):
    """Raised when regional profile or matching engine configuration is invalid."""

    pass


class SiteCapacityExhaustedError(RelocationMatchingError):
    """Raised when attempting to allocate to a site whose remaining capacity is completely exhausted."""

    pass
