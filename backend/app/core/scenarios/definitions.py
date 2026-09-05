"""Canonical scenario definitions and default parameter configurations (Chunk M4-06)."""

from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from app.core.profiles.models import RegionProfile
from app.core.scenarios.contracts import ScenarioParameters, ScenarioType
from app.core.scenarios.errors import InvalidScenarioParameterError, UnknownScenarioTypeError


class ScenarioDefinition(BaseModel):
    """Metadata and default parameters defining a scenario type."""

    scenario_type: ScenarioType
    name: str
    description: str
    default_parameters: ScenarioParameters
    is_canonical: bool = True
    tags: List[str] = Field(default_factory=list)


CANONICAL_SCENARIOS: Dict[ScenarioType, ScenarioDefinition] = {
    ScenarioType.NORMAL: ScenarioDefinition(
        scenario_type=ScenarioType.NORMAL,
        name="Normal / Baseline State",
        description="Represents current baseline operating conditions without artificial hazard or capacity alterations.",
        default_parameters=ScenarioParameters(
            scenario_type=ScenarioType.NORMAL,
            rainfall_multiplier=1.0,
            capacity_reduction_percentage=0.0,
            flood_hazard_increase=0.0,
            road_blockage_percentage=0.0,
        ),
        tags=["baseline", "operational"],
    ),
    ScenarioType.EXTREME_RAINFALL: ScenarioDefinition(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        name="Extreme Rainfall Simulation (+40%)",
        description="Simulates a 40% increase in precipitation intensity (cloudburst / monsoon surge) based on IMD heavy rainfall triggers.",
        default_parameters=ScenarioParameters(
            scenario_type=ScenarioType.EXTREME_RAINFALL,
            rainfall_multiplier=1.40,
            capacity_reduction_percentage=0.0,
            flood_hazard_increase=10.0,
            road_blockage_percentage=0.0,
        ),
        tags=["climate_shock", "hazard_escalation", "monsoon"],
    ),
    ScenarioType.FLASH_FLOOD: ScenarioDefinition(
        scenario_type=ScenarioType.FLASH_FLOOD,
        name="Flash Flood / GLOF Valley Inundation",
        description="Simulates severe riverine flash flooding and GLOF surge along river valleys, cutting off low-lying transit highways.",
        default_parameters=ScenarioParameters(
            scenario_type=ScenarioType.FLASH_FLOOD,
            rainfall_multiplier=1.20,
            flood_severity="critical",
            flood_hazard_increase=35.0,
            road_blockage_percentage=15.0,
            blocked_segment_ids=[],
        ),
        tags=["glof", "flash_flood", "road_severance"],
    ),
    ScenarioType.CAPACITY_CRISIS: ScenarioDefinition(
        scenario_type=ScenarioType.CAPACITY_CRISIS,
        name="Relocation Capacity Crisis (-50%)",
        description="Simulates a 50% loss or shortage of usable carrying capacity across candidate relocation sites.",
        default_parameters=ScenarioParameters(
            scenario_type=ScenarioType.CAPACITY_CRISIS,
            rainfall_multiplier=1.0,
            capacity_reduction_percentage=50.0,
            flood_hazard_increase=0.0,
            road_blockage_percentage=0.0,
        ),
        tags=["bottleneck", "capacity_deficit", "resource_strain"],
    ),
}


def get_scenario_definition(scenario_type: Union[str, ScenarioType]) -> ScenarioDefinition:
    """Retrieve canonical scenario definition or raise UnknownScenarioTypeError."""
    if isinstance(scenario_type, str):
        normalized = scenario_type.strip().upper()
        try:
            st = ScenarioType(normalized)
        except ValueError:
            raise UnknownScenarioTypeError(
                f"Unknown scenario type '{scenario_type}'. Supported types: {[t.value for t in ScenarioType]}"
            )
    else:
        st = scenario_type

    if st not in CANONICAL_SCENARIOS:
        raise UnknownScenarioTypeError(f"No canonical definition registered for scenario '{st.value}'.")
    return CANONICAL_SCENARIOS[st]


def list_scenario_definitions() -> List[ScenarioDefinition]:
    """Return all registered canonical scenario definitions deterministically ordered by scenario type value."""
    return sorted(CANONICAL_SCENARIOS.values(), key=lambda s: s.scenario_type.value)


def resolve_scenario_parameters(
    scenario_type: Union[str, ScenarioType],
    parameters: Optional[ScenarioParameters] = None,
    profile: Optional[RegionProfile] = None,
) -> Tuple[ScenarioDefinition, ScenarioParameters]:
    """Resolve and validate scenario parameters against definition defaults and regional profile bounds.

    Architecture flow:
        ScenarioDefinition (canonical defaults: +40% rainfall, +35 flood exposure, -50% capacity)
            ↓
        Explicit caller overrides (e.g. custom flood_hazard_increase, capacity_reduction)
            ↓
        RegionProfile bounds validation (ScenarioBounds min/max constraints)
            ↓
        Final validated ScenarioParameters
    """
    definition = get_scenario_definition(scenario_type)
    resolved_dict = definition.default_parameters.model_dump()

    # 1. Apply regional profile defaults for scenario-specific corridor blockages
    if profile is not None and hasattr(profile, "scenario_bounds") and profile.scenario_bounds is not None:
        sb = profile.scenario_bounds
        if definition.scenario_type == ScenarioType.FLASH_FLOOD:
            if hasattr(sb, "flood_prone_corridor_segments") and sb.flood_prone_corridor_segments:
                resolved_dict["blocked_segment_ids"] = list(sb.flood_prone_corridor_segments)

    # 2. Merge explicitly set caller overrides on top of defaults
    if parameters is not None:
        user_overrides = parameters.model_dump(exclude_unset=True)
        resolved_dict.update(user_overrides)

    resolved_params = ScenarioParameters(**resolved_dict)

    # 3. Validate against regional profile scenario bounds if a profile is present
    if profile is not None and hasattr(profile, "scenario_bounds") and profile.scenario_bounds is not None:
        bounds = profile.scenario_bounds
        if not (bounds.min_rainfall_multiplier <= resolved_params.rainfall_multiplier <= bounds.max_rainfall_multiplier):
            raise InvalidScenarioParameterError(
                f"Rainfall multiplier {resolved_params.rainfall_multiplier} is outside regional bounds "
                f"[{bounds.min_rainfall_multiplier}, {bounds.max_rainfall_multiplier}]."
            )
        if resolved_params.road_blockage_percentage > bounds.max_road_blockage_percentage:
            raise InvalidScenarioParameterError(
                f"Road blockage percentage {resolved_params.road_blockage_percentage}% exceeds regional max "
                f"{bounds.max_road_blockage_percentage}%."
            )
        if resolved_params.seismic_intensity_mmi is not None:
            if not (bounds.min_seismic_intensity_mmi <= resolved_params.seismic_intensity_mmi <= bounds.max_seismic_intensity_mmi):
                raise InvalidScenarioParameterError(
                    f"Seismic intensity {resolved_params.seismic_intensity_mmi} MMI is outside regional bounds "
                    f"[{bounds.min_seismic_intensity_mmi}, {bounds.max_seismic_intensity_mmi}]."
                )

    return definition, resolved_params
