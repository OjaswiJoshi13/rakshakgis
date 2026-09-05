"""Domain contracts and data models for the Scenario Simulator Engine (Chunk M4-06)."""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator


class ScenarioType(str, Enum):
    """Canonical simulation scenario types."""
    NORMAL = "NORMAL"
    EXTREME_RAINFALL = "EXTREME_RAINFALL"
    FLASH_FLOOD = "FLASH_FLOOD"
    CAPACITY_CRISIS = "CAPACITY_CRISIS"
    CUSTOM = "CUSTOM"


class ScenarioRunStatus(str, Enum):
    """Execution status of a scenario simulation run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScenarioParameters(BaseModel):
    """Explicit parameters governing how inputs are modified for a scenario."""

    scenario_type: ScenarioType = ScenarioType.NORMAL
    rainfall_multiplier: float = Field(
        default=1.0,
        description="Multiplier applied to rainfall observations and risk factors (e.g. 1.40 for +40%).",
    )
    capacity_reduction_percentage: float = Field(
        default=0.0,
        description="Percentage (0.0 to 100.0) by which candidate site capacities are reduced.",
    )
    flood_severity: Optional[str] = Field(
        default=None,
        description="Flood severity override (e.g. 'critical', 'high').",
    )
    flood_hazard_increase: float = Field(
        default=0.0,
        description="Absolute points added to flood risk factors for flood-prone corridors.",
    )
    road_blockage_percentage: float = Field(
        default=0.0,
        description="Percentage of network roads blocked in simulation.",
    )
    blocked_segment_ids: List[str] = Field(
        default_factory=list,
        description="Specific road segment IDs explicitly cut off in the scenario.",
    )
    seismic_intensity_mmi: Optional[float] = Field(
        default=None,
        description="Optional seismic intensity trigger (MMI).",
    )
    custom_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional scenario-specific parameter overrides.",
    )

    @field_validator("rainfall_multiplier")
    @classmethod
    def validate_rainfall_multiplier(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("rainfall_multiplier cannot be NaN or infinite.")
        if v < 0.0:
            raise ValueError("rainfall_multiplier must be non-negative.")
        return v

    @field_validator("capacity_reduction_percentage")
    @classmethod
    def validate_capacity_reduction(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("capacity_reduction_percentage cannot be NaN or infinite.")
        if not (0.0 <= v <= 100.0):
            raise ValueError("capacity_reduction_percentage must be between 0.0 and 100.0.")
        return v

    @field_validator("flood_hazard_increase")
    @classmethod
    def validate_flood_hazard_increase(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("flood_hazard_increase cannot be NaN or infinite.")
        if v < 0.0:
            raise ValueError("flood_hazard_increase must be non-negative.")
        return v

    @field_validator("road_blockage_percentage")
    @classmethod
    def validate_road_blockage(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("road_blockage_percentage cannot be NaN or infinite.")
        if not (0.0 <= v <= 100.0):
            raise ValueError("road_blockage_percentage must be between 0.0 and 100.0.")
        return v


class VillageSimulationInput(BaseModel):
    """Input representation of a settlement evaluated in the simulation pipeline."""

    village_id: str
    village_name: str
    location: Tuple[float, float] = Field(description="(longitude, latitude)")
    households: int = Field(ge=0)
    population: int = Field(ge=0)
    elderly_count: int = Field(default=0, ge=0)
    children_count: int = Field(default=0, ge=0)
    disabled_count: int = Field(default=0, ge=0)
    livestock_count: int = Field(default=0, ge=0)

    # 6 Risk factor values in [0.0, 100.0]
    hazard_severity: float = Field(default=50.0, ge=0.0, le=100.0)
    flood_exposure: float = Field(default=30.0, ge=0.0, le=100.0)
    rainfall_intensity: float = Field(default=40.0, ge=0.0, le=100.0)
    slope_landslide_susceptibility: float = Field(default=50.0, ge=0.0, le=100.0)
    infrastructure_vulnerability: float = Field(default=40.0, ge=0.0, le=100.0)
    social_vulnerability: float = Field(default=40.0, ge=0.0, le=100.0)

    # Optional dynamic sensor telemetry readings
    rainfall_24h_mm: Optional[float] = None
    slope_deg: Optional[float] = None
    historical_impact: Optional[float] = None
    accessibility: Optional[float] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        lon, lat = v
        if math.isnan(lon) or math.isnan(lat) or math.isinf(lon) or math.isinf(lat):
            raise ValueError("Location coordinates cannot be NaN or infinite.")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} out of bounds [-180, 180].")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} out of bounds [-90, 90].")
        return (lon, lat)


class SiteSimulationInput(BaseModel):
    """Input representation of a candidate relocation site evaluated in the simulation pipeline."""

    site_id: Union[int, str]
    site_name: str
    location: Optional[Tuple[float, float]] = None
    terrain_slope_deg: float = Field(default=5.0, ge=0.0)
    hazard_buffer_distance_m: float = Field(default=1000.0, ge=0.0)
    housing_capacity: int = Field(default=100, ge=0)
    water_capacity: int = Field(default=100, ge=0)
    sanitation_capacity: int = Field(default=100, ge=0)
    healthcare_capacity: int = Field(default=100, ge=0)
    shelter_capacity: int = Field(default=100, ge=0)
    status: str = Field(default="approved")

    metadata: Dict[str, Any] = Field(default_factory=dict)


# Stage Result Contracts

class VillageRiskStageResult(BaseModel):
    village_id: str
    village_name: str
    risk_score: float
    risk_band: str
    factor_breakdown: Dict[str, float]


class DynamicRedZoneStageResult(BaseModel):
    total_evaluated: int
    triggered_count: int
    triggered_village_ids: List[str]
    candidate_ids: List[str]


class PriorityStageResult(BaseModel):
    village_id: str
    village_name: str
    priority_score: float
    priority_band: str


class CapacityStageResult(BaseModel):
    site_id: str
    site_name: str
    effective_capacity: int
    available_capacity: int
    limiting_factor: str
    is_feasible: bool


class MatchingAssignmentSummary(BaseModel):
    village_id: str
    village_name: str
    assigned_site_id: Optional[str] = None
    assigned_site_name: Optional[str] = None
    is_assigned: bool
    demanded_households: int
    allocated_households: int
    unassigned_code: Optional[str] = None
    rank_score: Optional[float] = None
    distance_km: Optional[float] = None


class MatchingStageResult(BaseModel):
    total_villages: int
    total_households_demanded: int
    total_households_allocated: int
    total_households_unassigned: int
    assigned_count: int
    unassigned_count: int
    assignments: List[MatchingAssignmentSummary]


class RoutingPathSummary(BaseModel):
    village_id: str
    site_id: str
    is_feasible: bool
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[float] = None
    blocked_avoided_count: int = 0
    route_status: str


class RoutingStageResult(BaseModel):
    routes_evaluated: int
    feasible_routes_count: int
    unroutable_count: int
    average_distance_km: Optional[float] = None
    routes: List[RoutingPathSummary]


class StagePipelineResult(BaseModel):
    """Complete output of executing all 7 domain pipeline stages."""

    risk_results: List[VillageRiskStageResult]
    red_zone_result: DynamicRedZoneStageResult
    priority_results: List[PriorityStageResult]
    capacity_results: List[CapacityStageResult]
    matching_result: MatchingStageResult
    routing_result: RoutingStageResult

    summary_metrics: Dict[str, Any] = Field(default_factory=dict)


class ScenarioComparison(BaseModel):
    """Mathematical and categorical comparison between baseline and scenario runs."""

    # Risk comparison
    risk_score_deltas: Dict[str, float] = Field(description="village_id -> (scenario_score - baseline_score)")
    average_risk_delta: float
    risk_band_shifts: List[Dict[str, Any]]
    villages_escalated_to_critical: List[str]

    # Red Zone comparison
    baseline_red_zones_count: int
    scenario_red_zones_count: int
    new_red_zone_villages: List[str]

    # Priority comparison
    priority_score_deltas: Dict[str, float] = Field(description="village_id -> (scenario_priority - baseline_priority)")
    priority_band_shifts: List[Dict[str, Any]]
    villages_escalated_to_immediate: List[str]

    # Capacity comparison
    site_capacity_deltas: Dict[str, int] = Field(description="site_id -> (scenario_effective - baseline_effective)")
    newly_infeasible_sites: List[str]

    # Matching comparison
    baseline_unassigned_count: int
    scenario_unassigned_count: int
    newly_unassigned_villages: List[str]
    site_reallocations: List[Dict[str, Any]]

    # Routing comparison
    route_distance_deltas: Dict[str, float] = Field(description="village_id -> distance delta")
    corridors_diverted: List[str]
    newly_severed_routes: List[str]

    comparison_narrative: str


class ScenarioSimulationOutput(BaseModel):
    """Root simulation envelope returned by the Scenario Simulator Engine."""

    scenario_name: str
    scenario_type: ScenarioType
    region_profile_id: str
    run_id: str
    status: ScenarioRunStatus
    parameters: ScenarioParameters
    started_at: str
    completed_at: str

    baseline_metrics: Dict[str, Any]
    scenario_metrics: Dict[str, Any]
    comparison: ScenarioComparison

    # Full stage pipeline details
    baseline_pipeline: StagePipelineResult
    scenario_pipeline: StagePipelineResult

    provenance: Dict[str, Any]
    explainability: Dict[str, Any]
