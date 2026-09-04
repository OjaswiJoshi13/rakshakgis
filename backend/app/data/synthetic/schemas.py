"""Pydantic schemas for validating and typing synthetic demo datasets."""

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry schema with [longitude, latitude] coordinates."""

    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float] = Field(
        ...,
        description="Coordinates tuple [longitude, latitude] in WGS84 (EPSG:4326).",
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
    """GeoJSON Polygon geometry schema with closed-ring validation."""

    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[Tuple[float, float]]] = Field(
        ...,
        description="Polygon rings coordinates array [[[lon, lat], ...]] in WGS84 (EPSG:4326).",
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
            if ring[0][0] != ring[-1][0] or ring[0][1] != ring[-1][1]:
                raise ValueError(
                    f"Polygon ring {ring_idx} is not closed: first vertex {ring[0]} != last vertex {ring[-1]}"
                )
        return v


class VillageDemographics(BaseModel):
    """Demographic and vulnerable population counts."""

    elderly_count: int = Field(..., ge=0)
    children_count: int = Field(..., ge=0)
    disabled_count: int = Field(..., ge=0)
    livestock_count: int = Field(..., ge=0)


class VillageVulnerabilityIndicators(BaseModel):
    """Normalized vulnerability indices (0.0 to 1.0) and structural attributes."""

    social_vulnerability_index: float = Field(..., ge=0.0, le=1.0)
    economic_vulnerability_index: float = Field(..., ge=0.0, le=1.0)
    structural_vulnerability_index: float = Field(..., ge=0.0, le=1.0)
    road_connectivity_index: float = Field(..., ge=0.0, le=1.0)
    poverty_ratio: float = Field(..., ge=0.0, le=1.0)
    kuccha_housing_ratio: float = Field(..., ge=0.0, le=1.0)


class VillageInfrastructure(BaseModel):
    """Essential village infrastructure presence."""

    has_primary_school: bool
    has_health_subcenter: bool
    has_piped_water: bool
    has_electricity: bool
    has_telecom_coverage: bool


class VillageAccessibility(BaseModel):
    """Road connectivity and evacuation accessibility metrics."""

    distance_to_motorable_road_km: float = Field(..., ge=0.0)
    road_type: Literal["paved", "unpaved", "footpath"]
    evacuation_route_condition: Literal["good", "fair", "poor", "critical_chokepoints"]
    is_winter_cutoff_prone: bool


class VillageHazards(BaseModel):
    """Site-specific geophysical hazard indicators."""

    elevation_m: float = Field(..., ge=0.0)
    slope_deg: float = Field(..., ge=0.0, le=90.0)
    historical_landslide_count: int = Field(..., ge=0)
    active_subsidence: bool
    distance_to_river_m: float = Field(..., ge=0.0)
    soil_type: str
    geological_formation: str


class SyntheticProvenance(BaseModel):
    """Explicit labelling indicating synthetic demonstration origin."""

    is_synthetic: bool = True
    data_source: str = "DEMO_SYNTHETIC_GENERATOR"
    pilot_region: str = "himalayan_pilot"
    generator_seed: int = 26191
    disclaimer: str


class SyntheticVillageProperties(BaseModel):
    """Structured properties for a synthetic village entity."""

    id: str
    name: str
    region_code: str
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    census_code: str
    population: int = Field(..., ge=0)
    households: int = Field(..., ge=0)
    demographics: VillageDemographics
    vulnerability: VillageVulnerabilityIndicators
    infrastructure: VillageInfrastructure
    accessibility: VillageAccessibility
    hazards: VillageHazards
    provenance: SyntheticProvenance


class SyntheticVillageFeature(BaseModel):
    """GeoJSON Feature representation of a synthetic village."""

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: GeoJSONPoint
    properties: SyntheticVillageProperties


class SyntheticVillagesFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection containing all pilot villages."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    name: str = "synthetic_himalayan_villages"
    features: List[SyntheticVillageFeature]


class CandidateSiteCapacity(BaseModel):
    """Carrying capacity inputs for candidate relocation sites."""

    max_households: int = Field(..., ge=0)
    max_population: int = Field(..., ge=0)
    allocated_households: int = Field(default=0, ge=0)
    allocated_population: int = Field(default=0, ge=0)
    available_households: int = Field(..., ge=0)
    available_population: int = Field(..., ge=0)
    sanitation_units: int = Field(..., ge=0)


class CandidateSiteSuitabilityInputs(BaseModel):
    """Geophysical and resource inputs consumed by later M4 suitability engine."""

    area_sq_m: float = Field(..., ge=0.0)
    terrain_slope_deg: float = Field(..., ge=0.0, le=90.0)
    elevation_m: float = Field(..., ge=0.0)
    soil_stability: str
    hazard_buffer_distance_m: float = Field(..., ge=0.0)
    road_width_m: float = Field(..., ge=0.0)
    distance_to_highway_km: float = Field(..., ge=0.0)
    all_weather_access: bool
    water_supply_lpd_per_capita: float = Field(..., ge=0.0)
    water_source_distance_m: float = Field(..., ge=0.0)
    perennial_water_source: bool
    distance_to_health_center_km: float = Field(..., ge=0.0)
    distance_to_school_km: float = Field(..., ge=0.0)
    distance_to_emergency_km: float = Field(..., ge=0.0)
    distance_to_market_km: float = Field(..., ge=0.0)
    distance_to_farmland_km: float = Field(..., ge=0.0)
    livelihood_potential: Literal["high", "moderate", "low"]
    expansion_potential: Literal["high", "moderate", "low", "none"]
    suitability_category: Literal["suitable", "constrained", "rejected"]
    rejection_reason: Optional[str] = None


class SyntheticCandidateSiteProperties(BaseModel):
    """Properties for a candidate relocation site."""

    id: str
    name: str
    district_code: str
    district_name: str
    block_code: str
    site_type: str
    status: Literal["proposed", "approved", "rejected", "active"]
    suitability: CandidateSiteSuitabilityInputs
    capacity: CandidateSiteCapacity
    provenance: SyntheticProvenance


class SyntheticCandidateSiteFeature(BaseModel):
    """GeoJSON Feature representation of a candidate relocation site."""

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: GeoJSONPolygon
    properties: SyntheticCandidateSiteProperties


class SyntheticCandidateSitesFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection containing candidate relocation sites."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    name: str = "synthetic_himalayan_candidate_sites"
    features: List[SyntheticCandidateSiteFeature]


class SyntheticHazardEvent(BaseModel):
    """Point-in-time synthetic hazard incident or sensor observation."""

    id: str
    village_id: str
    village_name: str
    hazard_type: Literal["landslide", "rainfall", "seismic", "flash_flood"]
    observed_at: str  # ISO 8601 string
    severity: Literal["low", "moderate", "high", "very_high", "critical"]
    intensity_value: float
    intensity_unit: str
    location: GeoJSONPoint
    description: str
    provenance: SyntheticProvenance


class DatasetMetadata(BaseModel):
    """Metadata describing the deterministic synthetic dataset package."""

    dataset_id: str = "rakshakgis_himalayan_pilot_v1"
    version: str = "1.0.0"
    source_type: Literal["synthetic", "demo"] = "synthetic"
    generation_method: str = "deterministic_prng"
    generator_seed: int = 26191
    pilot_region_profile: str = "himalayan_pilot"
    village_count: int = 40
    candidate_site_count: int = 12
    hazard_event_count: int = 30
    geographic_bounding_box: Dict[str, float] = {
        "min_lon": 79.10,
        "max_lon": 79.85,
        "min_lat": 30.20,
        "max_lat": 30.70,
    }
    disclaimer: str


class HimalayanPilotDataset(BaseModel):
    """Complete container model for the synthetic Himalayan pilot dataset."""

    model_config = ConfigDict(frozen=True)

    metadata: DatasetMetadata
    villages: SyntheticVillagesFeatureCollection
    candidate_sites: SyntheticCandidateSitesFeatureCollection
    hazard_events: List[SyntheticHazardEvent]
