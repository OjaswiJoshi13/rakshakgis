"""Exceptions and error definitions for the Risk Normalization Engine."""


class NormalizationError(Exception):
    """Base exception for all normalization engine errors."""

    pass


class NormalizationConfigError(NormalizationError):
    """Raised when normalization parameters or configuration ranges are mathematically invalid."""

    pass


class InvalidInputError(NormalizationError):
    """Raised when raw observation data is malformed, NaN, infinite, or domain-invalid."""

    pass


class UnsupportedFactorError(NormalizationError):
    """Raised when a normalization request is made for an unsupported hazard or factor category."""

    pass
