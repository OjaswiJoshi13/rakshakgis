"""Pydantic validation and serialization schemas for administrative villages (GIS Habitations)."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.sites import (
    GeoJSONPoint,
    GeoJSONPolygon,
    parse_geometry_to_geojson_point,
    parse_geometry_to_geojson_polygon,
)


class VillageRead(BaseModel):
    """Village habitation model conforming to RFC 7946 GeoJSON and M5-07 GIS frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique village primary key")
    name: str = Field(..., description="Official village settlement name")
    census_code: Optional[str] = Field(None, description="Census India identifier code")
    block_id: Optional[int] = Field(None, description="Parent administrative block ID")
    location: GeoJSONPoint = Field(..., description="Centroid/settlement location Point (WGS84)")
    boundary: Optional[GeoJSONPolygon] = Field(None, description="Settlement cadastral polygon boundary")
    elevation_m: Optional[float] = Field(None, description="Mean elevation above sea level in meters")
    slope_deg: Optional[float] = Field(None, description="Mean terrain slope angle in degrees")
    is_active: bool = Field(True, description="Active status in GIS layers")

    @field_validator("location", mode="before")
    @classmethod
    def serialize_location_geometry(cls, v: Any) -> Optional[GeoJSONPoint]:
        return parse_geometry_to_geojson_point(v)

    @field_validator("boundary", mode="before")
    @classmethod
    def serialize_boundary_geometry(cls, v: Any) -> Optional[GeoJSONPolygon]:
        return parse_geometry_to_geojson_polygon(v)


class VillageDetailRead(VillageRead):
    """Detailed village record including demographic profile and risk telemetry."""

    population: Optional[int] = Field(None, description="Total settlement population")
    households: Optional[int] = Field(None, description="Total settlement households")
    demographics: Optional[Dict[str, Any]] = Field(None, description="Vulnerable demographic breakdown")
    vulnerability: Optional[Dict[str, Any]] = Field(None, description="Social and physical vulnerability metrics")
    hazards: Optional[Dict[str, Any]] = Field(None, description="Physical hazard exposure indicators")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Full ingestion metadata and provenance")
