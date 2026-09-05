"""Exception hierarchy for Carrying Capacity & Infrastructure Sizing engine."""

from typing import Optional


class CarryingCapacityError(Exception):
    """Base exception for all carrying capacity and infrastructure sizing errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidCapacityDataError(CarryingCapacityError):
    """Raised when numerical capacity input data contains NaN, Inf, or negative values."""

    pass


class MissingCapacityDataError(CarryingCapacityError):
    """Raised when critical safety capacity data is missing or indeterminate."""

    pass


class CapacityConfigError(CarryingCapacityError):
    """Raised when regional capacity planning configuration is invalid or missing required fields."""

    pass
