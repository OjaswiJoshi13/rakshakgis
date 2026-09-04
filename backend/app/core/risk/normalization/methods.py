"""Mathematical and algorithmic normalization implementations."""

import math
from typing import Optional, Tuple

from app.core.risk.normalization.contracts import (
    CategoricalSeverityPolicy,
    LinearRangeConfig,
    PiecewiseThresholdConfig,
)
from app.core.risk.normalization.errors import InvalidInputError


def linear_normalize(
    value: float,
    config: LinearRangeConfig,
) -> Tuple[float, bool, Optional[str]]:
    """Transform a continuous numerical observation into a 0.0 - 100.0 score using linear scaling.

    Args:
        value: Raw numeric observation.
        config: Linear configuration containing min_value, max_value, and clamping policies.

    Returns:
        Tuple of (normalized_score, was_clamped, clamping_reason).

    Raises:
        InvalidInputError: If value is NaN, infinite, or not a valid number.
    """
    if value is None:
        raise InvalidInputError("Observation value cannot be None for numeric normalization.")

    if not isinstance(value, (int, float)):
        raise InvalidInputError(f"Expected numeric input (int or float), got {type(value).__name__}: {value!r}")

    if math.isnan(value) or math.isinf(value):
        raise InvalidInputError(f"Invalid input: observation value cannot be NaN or infinite, got {value}")

    min_val = config.min_value
    max_val = config.max_value

    if value <= min_val:
        was_clamped = value < min_val and config.clamp_min
        reason = (
            f"Observation ({value}) is below minimum bound ({min_val}); clamped to 0.0."
            if was_clamped
            else None
        )
        return (0.0, was_clamped, reason)

    if value >= max_val:
        was_clamped = value > max_val and config.clamp_max
        reason = (
            f"Observation ({value}) exceeds maximum bound ({max_val}); clamped to 100.0."
            if was_clamped
            else None
        )
        return (100.0, was_clamped, reason)

    # Standard linear scaling within domain [min_val, max_val]
    normalized = ((value - min_val) / (max_val - min_val)) * 100.0
    return (round(float(normalized), 4), False, None)


def piecewise_threshold_normalize(
    value: float,
    config: PiecewiseThresholdConfig,
) -> Tuple[float, bool, Optional[str]]:
    """Transform a continuous numerical observation using piecewise linear interpolation through thresholds.

    Args:
        value: Raw numeric observation.
        config: Piecewise configuration containing ordered benchmark (threshold, score) tuples.

    Returns:
        Tuple of (normalized_score, was_clamped, clamping_reason).

    Raises:
        InvalidInputError: If value is NaN, infinite, or not a valid number.
    """
    if value is None:
        raise InvalidInputError("Observation value cannot be None for numeric normalization.")

    if not isinstance(value, (int, float)):
        raise InvalidInputError(f"Expected numeric input (int or float), got {type(value).__name__}: {value!r}")

    if math.isnan(value) or math.isinf(value):
        raise InvalidInputError(f"Invalid input: observation value cannot be NaN or infinite, got {value}")

    benchmarks = config.benchmarks

    # Below lowest threshold
    lowest_x, lowest_y = benchmarks[0]
    if value <= lowest_x:
        was_clamped = value < lowest_x
        reason = (
            f"Observation ({value}) is below lowest benchmark threshold ({lowest_x}); clamped to {lowest_y}."
            if was_clamped
            else None
        )
        return (lowest_y, was_clamped, reason)

    # Above highest threshold
    highest_x, highest_y = benchmarks[-1]
    if value >= highest_x:
        was_clamped = value > highest_x
        reason = (
            f"Observation ({value}) exceeds highest benchmark threshold ({highest_x}); clamped to {highest_y}."
            if was_clamped
            else None
        )
        return (highest_y, was_clamped, reason)

    # Intermediate segments
    for i in range(len(benchmarks) - 1):
        x0, y0 = benchmarks[i]
        x1, y1 = benchmarks[i + 1]
        if x0 <= value <= x1:
            fraction = (value - x0) / (x1 - x0)
            interpolated = y0 + fraction * (y1 - y0)
            return (round(float(interpolated), 4), False, None)

    # Fallback boundary safety (should not be reached given earlier checks)
    return (highest_y, False, None)


def categorical_severity_normalize(
    severity: str,
    policy: CategoricalSeverityPolicy,
) -> Tuple[float, bool, Optional[str]]:
    """Transform a discrete severity label into a deterministic 0.0 - 100.0 score.

    Args:
        severity: Qualitative severity string (e.g. 'low', 'moderate', 'high', 'very_high', 'critical').
        policy: CategoricalSeverityPolicy mapping labels to numeric factors.

    Returns:
        Tuple of (normalized_score, was_clamped, clamping_reason).

    Raises:
        InvalidInputError: If severity is not recognized or not a valid string.
    """
    if not isinstance(severity, str) or not severity.strip():
        raise InvalidInputError(f"Severity label must be a non-empty string, got {severity!r}")

    normalized_key = severity.strip().lower()
    if normalized_key in policy.mappings:
        return (policy.mappings[normalized_key], False, None)

    supported = sorted(policy.mappings.keys())
    raise InvalidInputError(
        f"Unsupported severity category '{severity}'. Supported categories are: {supported}"
    )
