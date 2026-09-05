"""Permanent and Dynamic Red Zone Demarcation package (Chunks M3-10 & M3-11)."""

from app.core.risk.red_zone.contracts import (
    DangerLevel,
    GeophysicalObservationInput,
    PermanentRedZoneCandidate,
    PermanentRedZoneExplainability,
    RedZoneStatus,
    RedZoneType,
    TriggerAudit,
)
from app.core.risk.red_zone.dynamic_contracts import (
    ComparisonOperator,
    DynamicHazardIndicator,
    DynamicHazardObservation,
    DynamicRedZoneCandidate,
    DynamicRedZoneExplainability,
    DynamicThresholdConfig,
    DynamicTriggerStatus,
    SingleTriggerEvaluation,
)
from app.core.risk.red_zone.dynamic_engine import DynamicRedZoneEngine
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
    # Engines
    "PermanentRedZoneEngine",
    "DynamicRedZoneEngine",
    # Enums
    "RedZoneStatus",
    "RedZoneType",
    "DangerLevel",
    "DynamicTriggerStatus",
    "DynamicHazardIndicator",
    "ComparisonOperator",
    # M3-10 Permanent Contracts
    "GeophysicalObservationInput",
    "TriggerAudit",
    "PermanentRedZoneExplainability",
    "PermanentRedZoneCandidate",
    # M3-11 Dynamic Contracts
    "DynamicThresholdConfig",
    "DynamicHazardObservation",
    "SingleTriggerEvaluation",
    "DynamicRedZoneExplainability",
    "DynamicRedZoneCandidate",
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

