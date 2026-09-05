"""Pydantic request and response schemas for scenario simulation API (Chunk M4-06)."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from app.core.scenarios.contracts import (
    ScenarioComparison,
    ScenarioParameters,
    ScenarioRunStatus,
    ScenarioSimulationOutput,
    ScenarioType,
    SiteSimulationInput,
    StagePipelineResult,
    VillageSimulationInput,
)


class ScenarioDefinitionRead(BaseModel):
    """Catalog entry for a scenario definition."""

    scenario_type: str
    name: str
    description: str
    default_parameters: ScenarioParameters
    is_canonical: bool = True
    tags: List[str] = Field(default_factory=list)


class ScenarioCreate(BaseModel):
    """Payload to define and persist a new custom scenario."""

    name: str = Field(min_length=3, max_length=150)
    description: Optional[str] = None
    rainfall_multiplier: float = Field(default=1.0, ge=0.0)
    seismic_intensity_mmi: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    road_blockage_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    parameters_json: Optional[Dict[str, Any]] = None


class ScenarioRead(BaseModel):
    """Database-persisted scenario definition schema."""

    id: int
    name: str
    description: Optional[str] = None
    created_by_user_id: Optional[int] = None
    rainfall_multiplier: float
    seismic_intensity_mmi: Optional[float] = None
    road_blockage_percentage: float
    parameters_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioRunRequest(BaseModel):
    """Payload to trigger a scenario simulation run."""

    scenario_type: str = Field(
        default="EXTREME_RAINFALL",
        description="Scenario type (NORMAL, EXTREME_RAINFALL, FLASH_FLOOD, CAPACITY_CRISIS, CUSTOM).",
    )
    region_profile_id: Optional[str] = Field(
        default="himalayan_pilot",
        description="Region profile ID to use for regional thresholds.",
    )
    parameters: Optional[ScenarioParameters] = Field(
        default=None,
        description="Optional parameter overrides for the scenario.",
    )
    villages: Optional[List[VillageSimulationInput]] = Field(
        default=None,
        description="Optional custom village input set. If omitted, uses pilot dataset villages.",
    )
    sites: Optional[List[SiteSimulationInput]] = Field(
        default=None,
        description="Optional custom site input set. If omitted, uses pilot dataset candidate sites.",
    )
    persist: bool = Field(
        default=False,
        description="If True, saves execution metrics and results summary to scenario_runs table.",
    )


class ScenarioRunRecordRead(BaseModel):
    """Database-persisted scenario execution run record."""

    id: int
    scenario_id: int
    executed_by_user_id: Optional[int] = None
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    simulated_affected_villages: Optional[int] = None
    simulated_displaced_population: Optional[int] = None
    results_summary_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
