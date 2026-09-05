"""Carrying Capacity & Infrastructure Sizing coordinator engine."""

from typing import Any, Dict, List, Optional

from app.core.profiles.models import RegionProfile
from app.core.relocation.capacity.contracts import (
    CapacityPlanningConfig,
    InfrastructureDimension,
    SiteCapacityInput,
    SiteCapacityResult,
)
from app.core.relocation.capacity.sizing import InfrastructureSizer


class CarryingCapacityEngine:
    """Evaluates effective carrying capacity, limiting infrastructure factors, and demand margins."""

    def __init__(self, config: Optional[CapacityPlanningConfig] = None) -> None:
        self.config = config or CapacityPlanningConfig()
        self.sizer = InfrastructureSizer(self.config)

    @classmethod
    def from_region_profile(cls, profile: RegionProfile) -> "CarryingCapacityEngine":
        """Factory creating engine configured with regional assumptions."""
        config = CapacityPlanningConfig.from_profile(profile)
        return cls(config=config)

    def evaluate(self, site: SiteCapacityInput) -> SiteCapacityResult:
        """Evaluate effective carrying capacity, infrastructure sizing, and relocation feasibility."""
        # 1. Evaluate infrastructure dimensions and physical deficits
        infra_results, deficits = self.sizer.size_all(site)

        # 2. Extract 5 critical household capacities
        caps = {
            InfrastructureDimension.HOUSING.value: infra_results[
                InfrastructureDimension.HOUSING.value
            ].existing_capacity_households,
            InfrastructureDimension.WATER.value: infra_results[
                InfrastructureDimension.WATER.value
            ].existing_capacity_households,
            InfrastructureDimension.SANITATION.value: infra_results[
                InfrastructureDimension.SANITATION.value
            ].existing_capacity_households,
            InfrastructureDimension.HEALTHCARE.value: infra_results[
                InfrastructureDimension.HEALTHCARE.value
            ].existing_capacity_households,
            InfrastructureDimension.SHELTER.value: infra_results[
                InfrastructureDimension.SHELTER.value
            ].existing_capacity_households,
        }

        # 3. Check for unknown critical dimensions
        unknown_dims = sorted([dim for dim, val in caps.items() if val is None])
        reasons: List[str] = []

        if unknown_dims:
            # Unknown capacity must NEVER be treated as unlimited.
            reasons.append(
                f"Critical infrastructure capacity dimension(s) {unknown_dims} are unknown or missing; "
                "cannot treat unknown capacity as unlimited. Comprehensive safe capacity determination requires complete data."
            )
            return SiteCapacityResult(
                site_id=site.site_id,
                site_name=site.site_name,
                effective_capacity_households=None,
                current_occupancy_households=site.current_occupancy_households,
                available_capacity_households=None,
                incoming_households=site.incoming_households,
                capacity_margin_households=None,
                remaining_capacity_households=None,
                feasible=False,
                limiting_factors=[],
                unknown_dimensions=unknown_dims,
                infrastructure_results=infra_results,
                deficits=deficits,
                assumptions=self._build_assumptions(site),
                reasons=reasons,
            )

        # 4. Authoritative Core Capacity Rule: MIN(housing, water, sanitation, healthcare, shelter)
        known_caps = {dim: val for dim, val in caps.items() if val is not None}
        min_capacity = min(known_caps.values())
        effective_capacity = min_capacity

        # 5. Deterministic Limiting Factor Identification (all tied dimensions sorted alphabetically)
        limiting_factors = sorted(
            [dim for dim, val in known_caps.items() if val == min_capacity]
        )

        # 6. Incoming and Available Capacity
        available_capacity = effective_capacity - site.current_occupancy_households
        capacity_margin = available_capacity - site.incoming_households
        remaining_capacity = capacity_margin  # strictly preserve negative values

        # 7. Feasibility Determination
        is_feasible = True

        if effective_capacity <= 0:
            is_feasible = False
            reasons.append(
                f"Effective site capacity is {effective_capacity} households; site cannot safely host relocation."
            )

        if available_capacity <= 0:
            is_feasible = False
            reasons.append(
                f"Available capacity is exhausted or zero ({available_capacity} households available after current occupancy of {site.current_occupancy_households})."
            )

        if capacity_margin < 0:
            is_feasible = False
            reasons.append(
                f"Capacity insufficient: Incoming demand of {site.incoming_households} households exceeds available capacity of {available_capacity} households "
                f"(deficit of {abs(capacity_margin)} households; limiting factor(s): {limiting_factors})."
            )
        elif is_feasible:
            reasons.append(
                f"Capacity feasible: Site can safely accommodate {site.incoming_households} incoming households with a remaining margin of {capacity_margin} households "
                f"(effective capacity: {effective_capacity}, limiting factor(s): {limiting_factors})."
            )

        # Report any specific infrastructure dimension deficits
        if deficits:
            reasons.append(
                f"Infrastructure deficits detected across {len(deficits)} dimension(s): {deficits}."
            )

        return SiteCapacityResult(
            site_id=site.site_id,
            site_name=site.site_name,
            effective_capacity_households=effective_capacity,
            current_occupancy_households=site.current_occupancy_households,
            available_capacity_households=available_capacity,
            incoming_households=site.incoming_households,
            capacity_margin_households=capacity_margin,
            remaining_capacity_households=remaining_capacity,
            feasible=is_feasible,
            limiting_factors=limiting_factors,
            unknown_dimensions=[],
            infrastructure_results=infra_results,
            deficits=deficits,
            assumptions=self._build_assumptions(site),
            reasons=reasons,
        )

    def _build_assumptions(self, site: SiteCapacityInput) -> Dict[str, Any]:
        """Construct explainability assumptions and planning provenance metadata."""
        hh_size = site.household_size or self.config.persons_per_household
        return {
            "effective_capacity_formula": "MIN(housing, water, sanitation, healthcare, shelter)",
            "water_supply_lpd_per_capita": self.config.water_supply_lpd_per_capita,
            "land_area_sq_m_per_household": self.config.land_area_sq_m_per_household,
            "persons_per_household": round(hh_size, 2),
            "households_per_sanitation_unit": self.config.households_per_sanitation_unit,
            "planning_standard_notice": (
                "Demographic and infrastructure sizing parameters are region-profile and MVP planning assumptions, "
                "not statutory government methodology."
            ),
        }
