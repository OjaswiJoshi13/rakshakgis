"""Exceptions and error definitions for the Multi-Hazard Risk Computation Engine."""


class RiskComputationError(Exception):
    """Base exception for all risk computation engine errors."""

    pass


class InsufficientFactorsError(RiskComputationError):
    """Raised when one or more required factors are missing, null, or unavailable."""

    pass


class InvalidFactorValueError(RiskComputationError):
    """Raised when a factor value is NaN, infinite, non-numeric, or outside valid domain [0.0, 100.0]."""

    pass


class WeightConfigurationError(RiskComputationError):
    """Raised when multi-hazard risk weights are mathematically invalid or do not sum to 1.0."""

    pass
