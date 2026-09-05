"""Scenario Simulator Integration Backend (Chunk M4-06).

Provides deterministic what-if scenario simulations orchestrating:
Risk Engine -> Red Zones -> Relocation Priority -> Site Suitability -> Capacity -> Matching -> Evacuation Routing.
"""

from app.core.scenarios.contracts import (
    CapacityStageResult,
    DynamicRedZoneStageResult,
    MatchingAssignmentSummary,
    MatchingStageResult,
    PriorityStageResult,
    RoutingPathSummary,
    RoutingStageResult,
    ScenarioComparison,
    ScenarioParameters,
    ScenarioRunStatus,
    ScenarioSimulationOutput,
    ScenarioType,
    SiteSimulationInput,
    StagePipelineResult,
    VillageRiskStageResult,
    VillageSimulationInput,
)
from app.core.scenarios.definitions import (
    CANONICAL_SCENARIOS,
    ScenarioDefinition,
    get_scenario_definition,
    list_scenario_definitions,
    resolve_scenario_parameters,
)
from app.core.scenarios.engine import ScenarioSimulatorEngine
from app.core.scenarios.errors import (
    InsufficientScenarioDataError,
    InvalidScenarioParameterError,
    ScenarioError,
    ScenarioExecutionError,
    UnknownScenarioTypeError,
)
from app.core.scenarios.inputs import apply_scenario_modifications

__all__ = [
    # Engine
    "ScenarioSimulatorEngine",
    # Enums & Parameters
    "ScenarioType",
    "ScenarioRunStatus",
    "ScenarioParameters",
    # Inputs & Outputs
    "VillageSimulationInput",
    "SiteSimulationInput",
    "VillageRiskStageResult",
    "DynamicRedZoneStageResult",
    "PriorityStageResult",
    "CapacityStageResult",
    "MatchingAssignmentSummary",
    "MatchingStageResult",
    "RoutingPathSummary",
    "RoutingStageResult",
    "StagePipelineResult",
    "ScenarioComparison",
    "ScenarioSimulationOutput",
    # Definitions
    "ScenarioDefinition",
    "CANONICAL_SCENARIOS",
    "get_scenario_definition",
    "list_scenario_definitions",
    "resolve_scenario_parameters",
    # Functions
    "apply_scenario_modifications",
    # Errors
    "ScenarioError",
    "InvalidScenarioParameterError",
    "UnknownScenarioTypeError",
    "ScenarioExecutionError",
    "InsufficientScenarioDataError",
]
