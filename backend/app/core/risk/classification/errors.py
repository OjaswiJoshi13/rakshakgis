"""Exceptions and error definitions for the Risk Classification & Grading Engine."""


class RiskClassificationError(Exception):
    """Base exception for all risk classification engine errors."""

    pass


class InvalidRiskScoreError(RiskClassificationError):
    """Raised when an input risk score is invalid, non-numeric, NaN, infinite, or out of domain [0.0, 100.0]."""

    pass


class ClassificationBandConfigError(RiskClassificationError):
    """Raised when risk score band cutoffs are mathematically invalid or non-monotonic."""

    pass
