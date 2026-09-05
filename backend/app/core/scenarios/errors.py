"""Exception hierarchy for the scenario simulation engine (Chunk M4-06)."""

from typing import Any, Dict, Optional


class ScenarioError(Exception):
    """Base exception for all scenario simulation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidScenarioParameterError(ScenarioError):
    """Raised when scenario parameters fail domain validation (e.g. NaN, Inf, negative values)."""
    pass


class UnknownScenarioTypeError(ScenarioError):
    """Raised when an unconfigured or invalid scenario type is requested."""
    pass


class ScenarioExecutionError(ScenarioError):
    """Raised when a specific pipeline stage fails during simulation."""

    def __init__(self, message: str, stage: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, details)
        self.stage = stage


class InsufficientScenarioDataError(ScenarioError):
    """Raised when baseline data is insufficient to compute a valid simulation."""
    pass
