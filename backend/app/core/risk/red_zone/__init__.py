"""Permanent Red Zone Demarcation package (Chunk M3-10)."""

from app.core.risk.red_zone.contracts import (
    DangerLevel,
    GeophysicalObservationInput,
    PermanentRedZoneCandidate,
    PermanentRedZoneExplainability,
    RedZoneStatus,
    RedZoneType,
    TriggerAudit,
)
from app.core.risk.red_zone.engine import PermanentRedZoneEngine
from app.core.risk.red_zone.errors import (
    InsufficientGeophysicalDataError,
    InvalidGeophysicalDataError,
    RedZoneConfigError,
    RedZoneError,
    SpatialGeometryError,
)
from app.core.risk.red_zone.geometry import (
    calculate_geodesic_area_sq_km,
    create_geodesic_buffer,
    dissolve_overlapping_candidates,
    normalize_to_multipolygon,
)

__all__ = [
    # Engine
    "PermanentRedZoneEngine",
    # Enums
    "RedZoneStatus",
    "RedZoneType",
    "DangerLevel",
    # Contracts
    "GeophysicalObservationInput",
    "TriggerAudit",
    "PermanentRedZoneExplainability",
    "PermanentRedZoneCandidate",
    # Geometry Utilities
    "create_geodesic_buffer",
    "normalize_to_multipolygon",
    "calculate_geodesic_area_sq_km",
    "dissolve_overlapping_candidates",
    # Exceptions
    "RedZoneError",
    "InvalidGeophysicalDataError",
    "InsufficientGeophysicalDataError",
    "SpatialGeometryError",
    "RedZoneConfigError",
]
