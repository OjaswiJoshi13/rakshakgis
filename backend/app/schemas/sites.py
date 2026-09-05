"""Pydantic validation and serialization schemas for candidate relocation sites."""

from datetime import datetime
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator
from geoalchemy2.shape import to_shape
from shapely.geometry import shape, Point as ShapelyPoint, Polygon as ShapelyPolygon


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry schema with SRID 4326 coordinate bounds validation."""

    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float] = Field(
        ...,
        description="Coordinates tuple [longitude, latitude] in WGS84 (SRID 4326).",
        examples=[[78.0, 30.0]],
    )

    @field_validator("coordinates", mode="after")
    @classmethod
    def validate_coordinates(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        lon, lat = v
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} out of valid range [-180.0, 180.0]")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} out of valid range [-90.0, 90.0]")
        return v


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry schema with ring topology and coordinate bounds validation."""

    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[Tuple[float, float]]] = Field(
        ...,
        description="Polygon rings coordinates array [[[lon, lat], ...]] in WGS84 (SRID 4326).",
    )

    @field_validator("coordinates", mode="after")
    @classmethod
    def validate_polygon_rings(
        cls, v: List[List[Tuple[float, float]]]
    ) -> List[List[Tuple[float, float]]]:
        if not v or len(v) == 0:
            raise ValueError("Polygon coordinates must contain at least one exterior ring")

        for ring_idx, ring in enumerate(v):
            if len(ring) < 4:
                raise ValueError(
                    f"Polygon ring {ring_idx} must contain at least 4 vertices to form a closed ring"
                )

            # Check closed ring condition (first vertex == last vertex)
            first_pt = ring[0]
            last_pt = ring[-1]
            if first_pt[0] != last_pt[0] or first_pt[1] != last_pt[1]:
                raise ValueError(
                    f"Polygon ring {ring_idx} is not closed: first vertex {first_pt} does not match last vertex {last_pt}"
                )

            # Validate each vertex coordinate bounds
            for pt in ring:
                lon, lat = pt
                if not (-180.0 <= lon <= 180.0):
                    raise ValueError(f"Longitude {lon} out of valid range [-180.0, 180.0]")
                if not (-90.0 <= lat <= 90.0):
                    raise ValueError(f"Latitude {lat} out of valid range [-90.0, 90.0]")

        return v


def parse_geometry_to_geojson_point(geom_obj) -> Optional[GeoJSONPoint]:
    """Helper to convert database WKBElement/Shapely geometry to GeoJSONPoint."""
    if geom_obj is None:
        return None
    if isinstance(geom_obj, GeoJSONPoint):
        return geom_obj
    if isinstance(geom_obj, dict):
        return GeoJSONPoint(**geom_obj)

    try:
        sh_geom = to_shape(geom_obj) if hasattr(geom_obj, "data") else geom_obj
        if isinstance(sh_geom, ShapelyPoint):
            return GeoJSONPoint(type="Point", coordinates=(sh_geom.x, sh_geom.y))
    except Exception:
        pass
    return None


def parse_geometry_to_geojson_polygon(geom_obj) -> Optional[GeoJSONPolygon]:
    """Helper to convert database WKBElement/Shapely geometry to GeoJSONPolygon."""
    if geom_obj is None:
        return None
    if isinstance(geom_obj, GeoJSONPolygon):
        return geom_obj
    if isinstance(geom_obj, dict):
        return GeoJSONPolygon(**geom_obj)

    try:
        sh_geom = to_shape(geom_obj) if hasattr(geom_obj, "data") else geom_obj
        if isinstance(sh_geom, ShapelyPolygon):
            exterior_coords = list(sh_geom.exterior.coords)
            interiors_coords = [list(ring.coords) for ring in sh_geom.interiors]
            all_rings = [exterior_coords] + interiors_coords
            formatted_rings = [
                [(float(x), float(y)) for x, y in ring] for ring in all_rings
            ]
            return GeoJSONPolygon(type="Polygon", coordinates=formatted_rings)
    except Exception:
        pass
    return None


class SiteCapacityRead(BaseModel):
    """Schema for candidate site capacity metrics."""

    id: int
    site_id: int
    max_households: int
    max_population: int
    allocated_households: int
    allocated_population: int
    available_households: int
    available_population: int
    water_supply_lpd: Optional[float] = None
    sanitation_units: Optional[int] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InfrastructureRead(BaseModel):
    """Schema for candidate site infrastructure assets."""

    id: int
    site_id: Optional[int] = None
    name: str
    infra_type: str
    status: str
    location: GeoJSONPoint
    capacity_description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def convert_location(cls, v):
        res = parse_geometry_to_geojson_point(v)
        if res:
            return res
        return v


class CandidateSiteRead(BaseModel):
    """Base schema for candidate relocation site summary."""

    id: int
    name: str
    district_id: int
    location: GeoJSONPoint
    boundary: Optional[GeoJSONPolygon] = None
    area_sq_m: Optional[float] = None
    terrain_slope_deg: Optional[float] = None
    elevation_m: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def convert_location(cls, v):
        res = parse_geometry_to_geojson_point(v)
        if res:
            return res
        return v

    @field_validator("boundary", mode="before")
    @classmethod
    def convert_boundary(cls, v):
        if v is None:
            return None
        res = parse_geometry_to_geojson_polygon(v)
        if res:
            return res
        return v


class CandidateSiteDetailRead(CandidateSiteRead):
    """Detailed candidate site response including capacities and infrastructures."""

    capacities: List[SiteCapacityRead] = []
    infrastructures: List[InfrastructureRead] = []


ALLOWED_STATUSES = {"proposed", "approved", "rejected", "active"}


class CandidateSiteCreate(BaseModel):
    """Request payload schema for creating a candidate site."""

    name: str = Field(..., min_length=1, max_length=150, description="Site name")
    district_id: int = Field(..., description="ID of the district where site is located")
    location: GeoJSONPoint = Field(..., description="GeoJSON Point location (SRID 4326)")
    boundary: Optional[GeoJSONPolygon] = Field(
        None, description="Optional GeoJSON Polygon boundary (SRID 4326)"
    )
    area_sq_m: Optional[float] = Field(None, ge=0.0, description="Total site area in sq meters")
    terrain_slope_deg: Optional[float] = Field(
        None, ge=0.0, le=90.0, description="Average terrain slope in degrees"
    )
    elevation_m: Optional[float] = Field(None, description="Mean elevation in meters")
    status: Optional[str] = Field("proposed", description="Site status: proposed, approved, rejected, active")

    @field_validator("status", mode="after")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return "proposed"
        val = v.lower().strip()
        if val not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid site status '{v}'. Allowed statuses are: {', '.join(sorted(ALLOWED_STATUSES))}"
            )
        return val


class CandidateSiteUpdate(BaseModel):
    """Request payload schema for partially updating a candidate site."""

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    district_id: Optional[int] = None
    location: Optional[GeoJSONPoint] = None
    boundary: Optional[GeoJSONPolygon] = None
    area_sq_m: Optional[float] = Field(None, ge=0.0)
    terrain_slope_deg: Optional[float] = Field(None, ge=0.0, le=90.0)
    elevation_m: Optional[float] = None
    status: Optional[str] = None

    @field_validator("status", mode="after")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.lower().strip()
        if val not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid site status '{v}'. Allowed statuses are: {', '.join(sorted(ALLOWED_STATUSES))}"
            )
        return val


class SiteEvaluationRequest(BaseModel):
    """Optional configuration request payload for site evaluation."""

    persist_score: bool = Field(
        default=False,
        description="If True, updates candidate_sites.suitability_score in the database with the result.",
    )
    region_profile_id: Optional[str] = Field(
        default="himalayan_pilot",
        description="Optional regional profile identifier (e.g. 'himalayan_pilot').",
    )
    overrides: Optional[dict] = Field(
        default=None,
        description="Optional attribute overrides for what-if evaluation.",
    )


class SiteCapacityEvaluationRequest(BaseModel):
    """Request payload for evaluating carrying capacity and infrastructure sizing."""

    incoming_households: int = Field(
        default=0,
        ge=0,
        description="Number of incoming households proposed for relocation.",
    )
    current_occupancy_households: Optional[int] = Field(
        default=None,
        ge=0,
        description="Optional override for current site occupancy in households.",
    )
    household_size: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Average persons per household for per-capita infrastructure conversions.",
    )
    region_profile_id: Optional[str] = Field(
        default="himalayan_pilot",
        description="Optional regional profile identifier (e.g. 'himalayan_pilot').",
    )
    overrides: Optional[dict] = Field(
        default=None,
        description="Optional capacity overrides (e.g. {'healthcare_capacity': 100, 'shelter_capacity': 80}).",
    )
