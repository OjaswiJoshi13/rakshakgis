"""In-memory scenario input overlay and modification functions (Chunk M4-06).

Ensures complete isolation: baseline inputs are strictly copied and never mutated.
"""

import copy
from typing import Any, Dict, List, Tuple

from app.core.scenarios.contracts import (
    ScenarioParameters,
    SiteSimulationInput,
    VillageSimulationInput,
)


def apply_scenario_modifications(
    villages: List[VillageSimulationInput],
    sites: List[SiteSimulationInput],
    parameters: ScenarioParameters,
) -> Tuple[List[VillageSimulationInput], List[SiteSimulationInput], Dict[str, Any]]:
    """Create isolated scenario copies of village and site inputs with applied scenario deltas.

    Strict Isolation Invariant:
      - The original village and site input lists and objects are never mutated.
      - Calculations use deterministic mathematical formulas.
    """
    # 1. Deep copy inputs for strict in-memory isolation
    scenario_villages: List[VillageSimulationInput] = []
    for v in villages:
        v_dict = v.model_dump()

        # Apply rainfall multiplier
        if parameters.rainfall_multiplier != 1.0:
            v_dict["rainfall_intensity"] = min(100.0, max(0.0, v.rainfall_intensity * parameters.rainfall_multiplier))
            if v.rainfall_24h_mm is not None:
                v_dict["rainfall_24h_mm"] = max(0.0, v.rainfall_24h_mm * parameters.rainfall_multiplier)

        # Apply flood hazard increase
        if parameters.flood_hazard_increase > 0.0:
            v_dict["flood_exposure"] = min(100.0, max(0.0, v.flood_exposure + parameters.flood_hazard_increase))

        # Seismic override if provided
        if parameters.seismic_intensity_mmi is not None:
            # Map MMI scale [1.0, 10.0] to risk factor [0.0, 100.0]
            v_dict["hazard_factors"] = dict(v_dict.get("hazard_factors", {}))
            v_dict["hazard_factors"]["seismic"] = min(100.0, max(0.0, parameters.seismic_intensity_mmi * 10.0))

        scenario_villages.append(VillageSimulationInput(**v_dict))

    # 2. Modify site capacities
    scenario_sites: List[SiteSimulationInput] = []
    capacity_factor = max(0.0, 1.0 - (parameters.capacity_reduction_percentage / 100.0))

    for s in sites:
        s_dict = s.model_dump()

        if parameters.capacity_reduction_percentage > 0.0:
            s_dict["housing_capacity"] = max(0, int(s.housing_capacity * capacity_factor))
            s_dict["water_capacity"] = max(0, int(s.water_capacity * capacity_factor))
            s_dict["sanitation_capacity"] = max(0, int(s.sanitation_capacity * capacity_factor))
            s_dict["healthcare_capacity"] = max(0, int(s.healthcare_capacity * capacity_factor))
            s_dict["shelter_capacity"] = max(0, int(s.shelter_capacity * capacity_factor))

        scenario_sites.append(SiteSimulationInput(**s_dict))

    # 3. Build scenario routing hazard context
    routing_hazard_context: Dict[str, Any] = {
        "blocked_segment_ids": list(parameters.blocked_segment_ids),
        "hazard_events": [],
    }

    # If flood severity or extreme rainfall specified, inject simulated events for valley routes
    if parameters.flood_severity == "critical" or parameters.flood_hazard_increase >= 30.0:
        routing_hazard_context["hazard_events"].append(
            {
                "id": "SCENARIO-FLOOD-EVT-01",
                "hazard_type": "flood",
                "severity": "critical",
                "location": {"type": "Point", "coordinates": [79.5250, 30.5250]},
                "description": "Simulation: River inundation runout across lower valley highway; road cut off.",
                "blocks_road": True,
            }
        )

    return scenario_villages, scenario_sites, routing_hazard_context
