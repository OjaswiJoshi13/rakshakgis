"""Granular, composable validator functions for identity, timestamps, coordinates, numbers, and provenance."""

from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from app.data.ingestion.schemas import ValidationIssue, ValidationIssueCode, ValidationSeverity
from app.data.providers.contracts import ProviderMode, ProviderProvenance, SourceCategory

VALID_SEVERITIES = {"low", "moderate", "high", "very_high", "critical"}
VALID_HAZARD_TYPES = {"landslide", "rainfall", "seismic", "flash_flood", "cloudburst", "avalanche"}


def get_field(record: Any, field_name: str, default: Any = None) -> Any:
    """Safely retrieve a field value from either a dict or an object."""
    if isinstance(record, dict):
        return record.get(field_name, default)
    return getattr(record, field_name, default)


def validate_identity(
    record_id: Optional[str],
    id_field_name: str = "record_id",
) -> List[ValidationIssue]:
    """Validate that record identifier is present, non-empty, and valid string."""
    issues: List[ValidationIssue] = []
    if record_id is None:
        issues.append(
            ValidationIssue(
                record_id=None,
                field=id_field_name,
                code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                message=f"Required identifier '{id_field_name}' is missing.",
            )
        )
    elif not isinstance(record_id, str) or not record_id.strip():
        issues.append(
            ValidationIssue(
                record_id=str(record_id) if record_id else None,
                field=id_field_name,
                code=ValidationIssueCode.INVALID_IDENTITY,
                message=f"Identifier '{id_field_name}' must be a non-empty string.",
            )
        )
    return issues


def validate_timestamp(
    observed_at: Optional[str],
    record_id: Optional[str] = None,
    field_name: str = "observed_at",
) -> List[ValidationIssue]:
    """Validate that timestamp is a non-empty string parseable as ISO-8601."""
    issues: List[ValidationIssue] = []
    if observed_at is None:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                message=f"Timestamp '{field_name}' is required.",
            )
        )
        return issues

    if not isinstance(observed_at, str) or not observed_at.strip():
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_TIMESTAMP,
                message=f"Timestamp '{field_name}' must be a non-empty string.",
            )
        )
        return issues

    # Parse ISO-8601
    try:
        # Standard Python 3.11 datetime.fromisoformat supports 'Z' suffix directly
        clean_ts = observed_at.replace("Z", "+00:00")
        datetime.fromisoformat(clean_ts)
    except (ValueError, TypeError) as exc:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_TIMESTAMP,
                message=f"Invalid ISO-8601 timestamp '{observed_at}': {str(exc)}",
            )
        )

    return issues


def validate_coordinates(
    coords: Any,
    record_id: Optional[str] = None,
    field_name: str = "location_coordinates",
) -> List[ValidationIssue]:
    """Validate that coordinates are a 2-tuple of numeric [longitude, latitude] within WGS84 bounds."""
    issues: List[ValidationIssue] = []

    if coords is None:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                message=f"Geographic coordinates '{field_name}' are required.",
            )
        )
        return issues

    if not isinstance(coords, (list, tuple)) or len(coords) != 2:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_COORDINATES,
                message=f"Coordinates must contain exactly two numeric elements [lon, lat], got {coords!r}.",
            )
        )
        return issues

    lon, lat = coords[0], coords[1]

    # Check numeric types
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_COORDINATES,
                message=f"Coordinates elements must be numeric, got ({type(lon).__name__}, {type(lat).__name__}).",
            )
        )
        return issues

    # Check NaN and Infinite
    if math.isnan(lon) or math.isinf(lon) or math.isnan(lat) or math.isinf(lat):
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_COORDINATES,
                message=f"Coordinates cannot be NaN or infinite, got [{lon}, {lat}].",
            )
        )
        return issues

    # Check WGS84 geographic bounds: lon in [-180, 180], lat in [-90, 90]
    out_of_bounds = False
    bounds_msg = []
    if not (-180.0 <= lon <= 180.0):
        out_of_bounds = True
        bounds_msg.append(f"Longitude {lon} outside [-180.0, 180.0]")
    if not (-90.0 <= lat <= 90.0):
        out_of_bounds = True
        bounds_msg.append(f"Latitude {lat} outside [-90.0, 90.0]")

    if out_of_bounds:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.COORDINATES_OUT_OF_BOUNDS,
                message="; ".join(bounds_msg) + " (clamping is strictly forbidden).",
            )
        )

    return issues


def validate_numeric(
    val: Any,
    field_name: str,
    record_id: Optional[str] = None,
    min_val: Optional[float] = 0.0,
    max_val: Optional[float] = None,
    require_integer: bool = False,
) -> List[ValidationIssue]:
    """Validate numeric scalar value: presence, finite, domain bounds."""
    issues: List[ValidationIssue] = []

    if val is None:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                message=f"Required numeric field '{field_name}' is missing.",
            )
        )
        return issues

    if not isinstance(val, (int, float)) or isinstance(val, bool):
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_NUMERIC_VALUE,
                message=f"Field '{field_name}' must be numeric, got {type(val).__name__}.",
            )
        )
        return issues

    # Check NaN and Inf
    if math.isnan(val) or math.isinf(val):
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_NUMERIC_VALUE,
                message=f"Field '{field_name}' cannot be NaN or infinite.",
            )
        )
        return issues

    if require_integer and not isinstance(val, int) and not val.is_integer():
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.INVALID_NUMERIC_VALUE,
                message=f"Field '{field_name}' must be an integer, got {val}.",
            )
        )

    # Check minimum bound
    if min_val is not None and val < min_val:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.NUMERIC_OUT_OF_DOMAIN,
                message=f"Field '{field_name}' value {val} is below allowed minimum {min_val}.",
            )
        )

    # Check maximum bound
    if max_val is not None and val > max_val:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field=field_name,
                code=ValidationIssueCode.NUMERIC_OUT_OF_DOMAIN,
                message=f"Field '{field_name}' value {val} exceeds allowed maximum {max_val}.",
            )
        )

    return issues


def validate_provenance(
    prov: Any,
    record_id: Optional[str] = None,
) -> List[ValidationIssue]:
    """Validate provenance metadata integrity and synthetic labelling."""
    issues: List[ValidationIssue] = []

    if prov is None:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field="provenance",
                code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                message="Provenance metadata is required.",
            )
        )
        return issues

    provider_id = get_field(prov, "provider_id")
    mode = get_field(prov, "mode")
    is_synthetic = get_field(prov, "is_synthetic")

    if not provider_id or not isinstance(provider_id, str):
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field="provenance.provider_id",
                code=ValidationIssueCode.INVALID_PROVENANCE,
                message="Provenance 'provider_id' must be a non-empty string.",
            )
        )

    if not mode or mode not in {ProviderMode.MOCK, ProviderMode.LIVE, "mock", "live"}:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field="provenance.mode",
                code=ValidationIssueCode.INVALID_PROVENANCE,
                message=f"Provenance 'mode' must be MOCK or LIVE, got '{mode}'.",
            )
        )

    # Synthetic integrity: If mode is MOCK, is_synthetic must remain True
    mode_val = mode.value if isinstance(mode, ProviderMode) else mode
    if mode_val == "mock" and is_synthetic is not True:
        issues.append(
            ValidationIssue(
                record_id=record_id,
                field="provenance.is_synthetic",
                code=ValidationIssueCode.INVALID_PROVENANCE,
                message="Mock provider data must be explicitly flagged with is_synthetic=True.",
            )
        )

    return issues


def validate_record(
    record: Any,
    category: SourceCategory,
) -> Tuple[Optional[str], List[ValidationIssue]]:
    """Validate an individual record according to its conceptual source category.

    Returns:
        Tuple[record_id, issues_list]
    """
    issues: List[ValidationIssue] = []

    # 1. Identity
    id_field = "village_id" if category == SourceCategory.POPULATION_EXPOSURE else "record_id"
    rec_id = get_field(record, id_field)
    issues.extend(validate_identity(rec_id, id_field_name=id_field))

    # 2. Coordinates
    coords = get_field(record, "location_coordinates")
    issues.extend(validate_coordinates(coords, record_id=rec_id))

    # 3. Provenance
    prov = get_field(record, "provenance")
    issues.extend(validate_provenance(prov, record_id=rec_id))

    # 4. Temporal (all observation categories require observed_at)
    if category != SourceCategory.POPULATION_EXPOSURE:
        observed_at = get_field(record, "observed_at")
        issues.extend(validate_timestamp(observed_at, record_id=rec_id))

    # 5. Severity (if present)
    severity = get_field(record, "severity")
    if severity is not None:
        if not isinstance(severity, str) or severity.lower() not in VALID_SEVERITIES:
            issues.append(
                ValidationIssue(
                    record_id=rec_id,
                    field="severity",
                    code=ValidationIssueCode.INVALID_SEVERITY,
                    message=f"Severity '{severity}' is invalid. Allowed: {sorted(list(VALID_SEVERITIES))}",
                )
            )

    # 6. Category-specific numerical checks
    if category == SourceCategory.RAINFALL:
        rainfall_val = get_field(record, "rainfall_24h_mm")
        issues.extend(validate_numeric(rainfall_val, "rainfall_24h_mm", record_id=rec_id, min_val=0.0))

    elif category == SourceCategory.FLOOD:
        water_val = get_field(record, "water_level_m_above_danger")
        issues.extend(validate_numeric(water_val, "water_level_m_above_danger", record_id=rec_id, min_val=0.0))

    elif category == SourceCategory.LANDSLIDE:
        debris_val = get_field(record, "debris_volume_cu_m")
        issues.extend(validate_numeric(debris_val, "debris_volume_cu_m", record_id=rec_id, min_val=0.0))

    elif category == SourceCategory.HAZARD_OBSERVATION:
        intensity_val = get_field(record, "intensity_value")
        issues.extend(validate_numeric(intensity_val, "intensity_value", record_id=rec_id, min_val=0.0))
        haz_type = get_field(record, "hazard_type")
        if not haz_type or not isinstance(haz_type, str):
            issues.append(
                ValidationIssue(
                    record_id=rec_id,
                    field="hazard_type",
                    code=ValidationIssueCode.MISSING_REQUIRED_FIELD,
                    message="Field 'hazard_type' is required for hazard observations.",
                )
            )

    elif category == SourceCategory.POPULATION_EXPOSURE:
        pop = get_field(record, "total_population")
        hh = get_field(record, "households")
        elderly = get_field(record, "elderly_count")
        children = get_field(record, "children_count")
        disabled = get_field(record, "disabled_count")
        livestock = get_field(record, "livestock_count")

        issues.extend(validate_numeric(pop, "total_population", record_id=rec_id, min_val=0, require_integer=True))
        issues.extend(validate_numeric(hh, "households", record_id=rec_id, min_val=0, require_integer=True))
        issues.extend(validate_numeric(elderly, "elderly_count", record_id=rec_id, min_val=0, require_integer=True))
        issues.extend(validate_numeric(children, "children_count", record_id=rec_id, min_val=0, require_integer=True))
        issues.extend(validate_numeric(disabled, "disabled_count", record_id=rec_id, min_val=0, require_integer=True))
        issues.extend(validate_numeric(livestock, "livestock_count", record_id=rec_id, min_val=0, require_integer=True))

        # Demographic sanity check: elderly + children <= total_population
        if isinstance(pop, (int, float)) and isinstance(elderly, (int, float)) and isinstance(children, (int, float)):
            if (elderly + children) > pop:
                issues.append(
                    ValidationIssue(
                        record_id=rec_id,
                        field="demographics",
                        code=ValidationIssueCode.NUMERIC_OUT_OF_DOMAIN,
                        message=f"Sum of elderly ({elderly}) and children ({children}) exceeds total population ({pop}).",
                    )
                )

    return (rec_id, issues)
