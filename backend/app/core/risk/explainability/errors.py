"""Exception hierarchy for Risk Explainability & Factor Contribution (Chunk M3-08)."""


class RiskExplainabilityError(Exception):
    """Base exception for all risk explainability errors."""


class UncomputableExplanationError(RiskExplainabilityError):
    """Raised when an operation strictly requiring a computable risk score encounters incomplete or invalid input."""


class IncompatibleClassificationError(RiskExplainabilityError):
    """Raised when an explicitly provided classification result does not match the composite risk result."""
