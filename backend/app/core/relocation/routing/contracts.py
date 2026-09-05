"""Strongly typed domain models, enums, and schemas for Evacuation & Access Routing Engine."""

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RouteStatus(str, Enum):
    """Evaluation outcome for an evacuation or access route."""

    FEASIBLE = "feasible"
    NO_ROUTE = "no_route"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID_INPUT = "invalid_input"


class SegmentHazardStatus(str, Enum):
    """Hazard exposure status of a single road segment."""

    NORMAL = "normal"
    PENALIZED = "penalized"
    BLOCKED = "blocked"


class RouteType(str, Enum):
    """Classification of generated route."""

    PRIMARY = "primary"
    ALTERNATIVE = "alternative"
    RELIEF = "relief"


class HazardType(str, Enum):
    """Recognized natural hazard categories for road routing."""

    LANDSLIDE = "landslide"
    FLOOD = "flood"
    RAINFALL = "rainfall"
    SUBSIDENCE = "subsidence"
    UNKNOWN = "unknown"


class HazardExposureDetail(BaseModel):
    """Detail of a hazard observation or event affecting a road segment."""

    hazard_type: str = Field(..., description="Hazard type (landslide, flood, rainfall, etc.)")
    severity: str = Field(..., description="Severity rating (low, moderate, high, critical)")
    event_id: Optional[str] = Field(None, description="Identifier of the hazard event or observation")
    distance_to_segment_m: Optional[float] = Field(None, ge=0.0, description="Minimum distance from hazard to segment in meters")
    buffer_m: Optional[float] = Field(None, ge=0.0, description="Applicable hazard exclusion or caution buffer in meters")
    applied_penalty_multiplier: float = Field(default=0.0, ge=0.0, description="Cost multiplier applied to segment")
    blockage_reason: Optional[str] = Field(None, description="Explanation if this hazard blocks the segment")
    description: Optional[str] = Field(None, description="Descriptive narrative of hazard impact")


class RouteSegment(BaseModel):
    """A directed edge in the road network traversed by a route."""

    segment_id: str = Field(..., description="Unique segment identifier")
    from_node: str = Field(..., description="Origin node identifier")
    to_node: str = Field(..., description="Destination node identifier")
    geometry: List[Tuple[float, float]] = Field(..., description="List of (longitude, latitude) coordinates along the road")
    distance_km: float = Field(..., ge=0.0, description="Physical road distance of the segment in kilometers")
    base_speed_kmh: Optional[float] = Field(default=30.0, ge=0.0, description="Design or operational vehicle speed in km/h")
    estimated_time_minutes: Optional[float] = Field(None, ge=0.0, description="Estimated transit time in minutes")
    road_type: str = Field(default="primary", description="Road functional classification")
    road_width_m: Optional[float] = Field(None, ge=0.0, description="Width of carriageway in meters")
    hazard_status: SegmentHazardStatus = Field(default=SegmentHazardStatus.NORMAL, description="Hazard condition")
    hazard_penalty: float = Field(default=0.0, ge=0.0, description="Effective cost penalty in kilometers")
    hazard_exposures: List[HazardExposureDetail] = Field(default_factory=list, description="Hazards affecting this segment")
    blockage_reason: Optional[str] = Field(None, description="Reason if blocked")

    @field_validator("distance_km")
    @classmethod
    def validate_distance_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v) or v < 0.0:
            raise ValueError(f"distance_km must be a non-negative finite number, got {v}")
        return v


class RouteExplainability(BaseModel):
    """Transparent narrative and structured factors explaining route selection."""

    selection_rationale: str = Field(..., description="Why this route was selected")
    hazard_summary: str = Field(..., description="Summary of hazard exposure on the route")
    penalties_applied: List[str] = Field(default_factory=list, description="List of applied hazard penalties")
    blocked_segments_avoided: List[str] = Field(default_factory=list, description="List of blocked road corridors avoided")
    alternative_status: str = Field(..., description="Explanation of alternative route availability")
    data_provenance: Dict[str, Any] = Field(default_factory=dict, description="Source data pedigree and synthetic disclaimers")
    uncertainty_notes: List[str] = Field(default_factory=list, description="Missing data gaps or unverified assumptions")


class RouteResult(BaseModel):
    """Complete evaluation and geometry of an evacuation or access route."""

    route_id: str = Field(..., description="Unique generated route identifier")
    route_name: str = Field(..., description="Descriptive route name")
    status: RouteStatus = Field(..., description="Feasibility status")
    route_type: RouteType = Field(..., description="Primary or alternative")
    origin: Tuple[float, float] = Field(..., description="(longitude, latitude) origin")
    destination: Tuple[float, float] = Field(..., description="(longitude, latitude) destination")
    geometry: List[Tuple[float, float]] = Field(..., description="Complete road LineString coordinates")
    distance_km: float = Field(..., ge=0.0, description="Total physical road distance in km")
    estimated_time_minutes: Optional[float] = Field(None, ge=0.0, description="Total estimated travel time in minutes (None if unavailable)")
    base_distance_km: float = Field(..., ge=0.0, description="Base physical road distance without penalties")
    total_hazard_penalty: float = Field(default=0.0, ge=0.0, description="Total penalty added to effective routing cost")
    effective_cost: float = Field(..., ge=0.0, description="Routing cost used for graph optimization")
    segments: List[RouteSegment] = Field(default_factory=list, description="Ordered road segments composing the route")
    hazard_exposure_summary: List[HazardExposureDetail] = Field(default_factory=list, description="Aggregated hazard exposures")
    is_feasible: bool = Field(..., description="Whether route is safe and passable")
    explainability: RouteExplainability = Field(..., description="Explainability narrative and audit trail")

    @field_validator("distance_km", "effective_cost", "base_distance_km")
    @classmethod
    def validate_numeric_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v) or v < 0.0:
            raise ValueError(f"Metric must be non-negative and finite, got {v}")
        return v


class RouteQuery(BaseModel):
    """Input query specification for evacuation routing."""

    origin: Optional[Tuple[float, float]] = Field(None, description="(longitude, latitude) origin coordinates")
    destination: Optional[Tuple[float, float]] = Field(None, description="(longitude, latitude) destination coordinates")
    assignment_id: Optional[int] = Field(None, ge=1, description="Database ID of a relocation assignment")
    origin_village_id: Optional[int] = Field(None, ge=1, description="Database ID of origin village")
    destination_site_id: Optional[int] = Field(None, ge=1, description="Database ID of destination candidate site")
    region_profile_id: str = Field(default="himalayan_pilot", description="Regional profile configuration ID")
    routing_mode: str = Field(default="evacuation", description="Mode: evacuation, relief, or safe_access")
    require_alternative: bool = Field(default=True, description="Whether to compute an alternative evacuation route")
    hazard_context: Optional[Dict[str, Any]] = Field(None, description="Optional active hazard parameters or overrides")

    @field_validator("origin", "destination")
    @classmethod
    def validate_coordinates(cls, v: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        if v is None:
            return None
        if len(v) != 2:
            raise ValueError("Coordinates must be a tuple of (longitude, latitude)")
        lon, lat = v
        if math.isnan(lon) or math.isnan(lat) or math.isinf(lon) or math.isinf(lat):
            raise ValueError(f"Coordinates must be finite numbers, got ({lon}, {lat})")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude must be between -180.0 and 180.0, got {lon}")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude must be between -90.0 and 90.0, got {lat}")
        return (float(lon), float(lat))


class EvacuationRoutingResult(BaseModel):
    """Aggregate response envelope containing primary and alternative evacuation routes."""

    status: RouteStatus = Field(..., description="Overall routing feasibility status")
    primary_route: Optional[RouteResult] = Field(None, description="Optimal safe evacuation route")
    alternative_route: Optional[RouteResult] = Field(None, description="Feasible secondary/alternative evacuation route")
    assignment_id: Optional[int] = Field(None, description="Linked relocation assignment ID if applicable")
    origin_village_name: Optional[str] = Field(None, description="Name of origin village")
    destination_site_name: Optional[str] = Field(None, description="Name of destination candidate site")
    unassigned_reason: Optional[str] = Field(None, description="Reason if no feasible route could be resolved")
    governance_notice: str = Field(
        default=(
            "DEMO / DECISION SUPPORT ONLY for SIH Problem Statement 26191. "
            "Routes represent deterministic decision-support proposals for district disaster management review. "
            "Does NOT constitute automated emergency dispatch or statutory evacuation orders."
        ),
        description="Mandatory governance disclaimer",
    )
