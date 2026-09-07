"""Pydantic validation and serialization schemas for Red Zones (Chunk M3-10 / M5-07)."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.geometry import MultiPolygon as ShapelyMultiPolygon, Polygon as ShapelyPolygon


class GeoJSONMultiPolygon(BaseModel):
    """GeoJSON MultiPolygon geometry schema conforming to RFC 7946."""

    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: List[List[List[Tuple[float, float]]]] = Field(
        ...,
        description="Array of Polygon coordinate rings [[[[lon, lat], ...]]].",
    )


def parse_geometry_to_geojson_multipolygon(
    geom_obj: Any,
) -> Optional[GeoJSONMultiPolygon]:
    """Helper to convert database WKBElement/Shapely geometry to GeoJSONMultiPolygon."""
    if geom_obj is None:
        return None
    if isinstance(geom_obj, GeoJSONMultiPolygon):
        return geom_obj
    if isinstance(geom_obj, dict):
        if geom_obj.get("type") == "Polygon":
            return GeoJSONMultiPolygon(type="MultiPolygon", coordinates=[geom_obj.get("coordinates", [])])
        return GeoJSONMultiPolygon(**geom_obj)

    try:
        sh_geom = to_shape(geom_obj) if hasattr(geom_obj, "data") else geom_obj
        if isinstance(sh_geom, ShapelyMultiPolygon):
            coords = []
            for poly in sh_geom.geoms:
                poly_rings = [list(poly.exterior.coords)] + [
                    list(interior.coords) for interior in poly.interiors
                ]
                formatted_rings = [
                    [(float(x), float(y)) for x, y in ring] for ring in poly_rings
                ]
                coords.append(formatted_rings)
            return GeoJSONMultiPolygon(type="MultiPolygon", coordinates=coords)
        elif isinstance(sh_geom, ShapelyPolygon):
            poly_rings = [list(sh_geom.exterior.coords)] + [
                list(interior.coords) for interior in sh_geom.interiors
            ]
            formatted_rings = [
                [(float(x), float(y)) for x, y in ring] for ring in poly_rings
            ]
            return GeoJSONMultiPolygon(type="MultiPolygon", coordinates=[formatted_rings])
    except Exception:
        pass
    return None


class RedZoneRead(BaseModel):
    """Demarcated Red Zone model conforming to M3-10 contracts and M5-07 GIS layer."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique red zone identifier")
    name: str = Field(..., description="Designated zone name")
    zone_type: str = Field(..., description="Danger classification (e.g. active_subsidence, landslide_danger)")
    danger_level: str = Field(..., description="Severity level (critical, uninhabitable, very_high)")
    geometry: GeoJSONMultiPolygon = Field(..., description="RFC 7946 MultiPolygon boundary")
    area_sq_km: Optional[float] = Field(None, description="Enclosed surface area in sq km")
    is_active: bool = Field(True, description="Enacted statutory status")
    declared_by_officer_id: Optional[int] = Field(None, description="Authorizing officer ID")
    declared_at: Optional[datetime] = Field(None, description="Declaration timestamp")
    contributing_village_ids: Optional[List[str]] = Field(default_factory=list, description="Affected settlement IDs")
    explainability: Optional[Dict[str, Any]] = Field(None, description="Decision justification and trigger audit")

    @field_validator("geometry", mode="before")
    @classmethod
    def serialize_geometry(cls, v: Any) -> Optional[GeoJSONMultiPolygon]:
        return parse_geometry_to_geojson_multipolygon(v)
