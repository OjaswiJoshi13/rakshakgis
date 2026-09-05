"""Pydantic request and response schemas for Evacuation & Access Routing API (Chunk M4-05)."""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.geometry import LineString as ShapelyLineString

from app.core.relocation.routing.contracts import (
    EvacuationRoutingResult,
    HazardExposureDetail,
    RouteExplainability,
    RouteResult,
    RouteSegment,
    RouteStatus,
    RouteType,
)


class GeoJSONLineString(BaseModel):
    """GeoJSON LineString geometry schema."""

    type: str = Field(default="LineString", pattern="^LineString$")
    coordinates: List[Tuple[float, float]] = Field(
        ...,
        min_length=2,
        description="Array of [longitude, latitude] coordinate pairs",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if len(v) < 2:
            raise ValueError("A LineString must have at least 2 coordinate points.")
        for lon, lat in v:
            if math.isnan(lon) or math.isnan(lat) or math.isinf(lon) or math.isinf(lat):
                raise ValueError(f"Coordinates must be finite numbers, got ({lon}, {lat})")
            if not (-180.0 <= lon <= 180.0):
                raise ValueError(f"Longitude must be between -180.0 and 180.0, got {lon}")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude must be between -90.0 and 90.0, got {lat}")
        return [(float(x), float(y)) for x, y in v]


def parse_geometry_to_geojson_linestring(geom_obj) -> Optional[GeoJSONLineString]:
    """Helper to convert database WKBElement/Shapely geometry to GeoJSONLineString."""
    if geom_obj is None:
        return None
    if isinstance(geom_obj, GeoJSONLineString):
        return geom_obj
    if isinstance(geom_obj, dict):
        return GeoJSONLineString(**geom_obj)

    try:
        sh_geom = to_shape(geom_obj) if hasattr(geom_obj, "data") else geom_obj
        if isinstance(sh_geom, ShapelyLineString):
            coords = [(float(x), float(y)) for x, y in sh_geom.coords]
            return GeoJSONLineString(type="LineString", coordinates=coords)
    except Exception:
        pass
    return None


class RouteGenerateRequest(BaseModel):
    """Request payload for evaluating evacuation routing."""

    origin: Optional[Tuple[float, float]] = Field(
        None, description="Origin coordinates (longitude, latitude)"
    )
    destination: Optional[Tuple[float, float]] = Field(
        None, description="Destination coordinates (longitude, latitude)"
    )
    assignment_id: Optional[int] = Field(
        None, ge=1, description="Database ID of a relocation assignment to derive origin and destination"
    )
    origin_village_id: Optional[int] = Field(
        None, ge=1, description="Database ID of origin village"
    )
    destination_site_id: Optional[int] = Field(
        None, ge=1, description="Database ID of destination candidate site"
    )
    region_profile_id: str = Field(
        default="himalayan_pilot", description="Regional profile configuration ID"
    )
    routing_mode: str = Field(
        default="evacuation", description="Routing mode: evacuation, relief, or safe_access"
    )
    require_alternative: bool = Field(
        default=True, description="Whether to evaluate secondary alternative evacuation route"
    )
    hazard_context: Optional[Dict[str, Any]] = Field(
        None, description="Custom hazard events or active conditions override"
    )

    @field_validator("origin", "destination")
    @classmethod
    def validate_point_coordinates(cls, v: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
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


class RouteCreate(BaseModel):
    """Schema for persisting an evacuation route in the database."""

    name: str = Field(..., min_length=1, max_length=150, description="Descriptive route name")
    origin_village_id: int = Field(..., ge=1, description="Database ID of origin village")
    destination_site_id: int = Field(..., ge=1, description="Database ID of destination candidate site")
    path: GeoJSONLineString = Field(..., description="Route road LineString geometry")
    distance_km: float = Field(..., ge=0.0, description="Route distance in km")
    estimated_travel_time_min: Optional[float] = Field(None, ge=0.0, description="Travel time in minutes")
    route_type: str = Field(default="evacuation", description="Route type: evacuation, relief, alternate")
    safety_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Route safety score")
    is_blocked: bool = Field(default=False, description="Whether route is currently blocked")
    blockage_reason: Optional[str] = Field(None, max_length=255, description="Blockage explanation")


class RouteRead(BaseModel):
    """Response schema for a persisted route record."""

    id: Optional[int] = None
    name: str
    origin_village_id: int
    origin_village_name: Optional[str] = None
    destination_site_id: int
    destination_site_name: Optional[str] = None
    path: GeoJSONLineString
    distance_km: float
    estimated_travel_time_min: Optional[float] = None
    route_type: str
    safety_score: Optional[float] = None
    is_blocked: bool
    blockage_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
