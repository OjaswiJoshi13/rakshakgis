"""Exceptions and error definitions for the Multi-Criteria Site Suitability Engine."""

from typing import Any, Dict, List, Optional


class SiteSuitabilityError(Exception):
    """Base exception for all site suitability evaluation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidSiteDataError(SiteSuitabilityError):
    """Raised when candidate site input attributes are NaN, infinite, or domain-invalid."""

    pass


class MissingCriticalAttributeError(SiteSuitabilityError):
    """Raised when critical information required for safety/capacity cannot be determined."""

    pass


class SuitabilityConfigError(SiteSuitabilityError):
    """Raised when criterion weights do not sum strictly to 1.0 or thresholds are invalid."""

    pass


class HardConstraintError(SiteSuitabilityError):
    """Raised when an error occurs during hard constraint evaluation."""

    pass
