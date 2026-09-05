"""Deterministic infrastructure sizing and deficit calculations for critical dimensions."""

import math
from typing import Dict, Tuple

from app.core.relocation.capacity.contracts import (
    CapacityPlanningConfig,
    DimensionSizingResult,
    InfrastructureDimension,
    SiteCapacityInput,
)


class InfrastructureSizer:
    """Evaluates demand, existing capacity, and deficits across all 5 critical dimensions."""

    def __init__(self, config: CapacityPlanningConfig) -> None:
        self.config = config

    def size_all(
        self, site: SiteCapacityInput
    ) -> Tuple[Dict[str, DimensionSizingResult], Dict[str, int]]:
        """Compute infrastructure demand, supply margins, and deficits for all critical dimensions.

        Returns:
            Tuple of:
              - results: Dict[str, DimensionSizingResult] keyed by dimension value
              - deficits: Dict[str, int] keyed by dimension value containing negative household margins
        """
        results: Dict[str, DimensionSizingResult] = {}
        deficits: Dict[str, int] = {}

        incoming_hh = site.incoming_households
        hh_size = site.household_size or self.config.persons_per_household

        # 1. Housing Sizing
        housing_res = self._size_housing(site, incoming_hh)
        results[InfrastructureDimension.HOUSING.value] = housing_res
        if housing_res.margin_households is not None and housing_res.margin_households < 0:
            deficits[InfrastructureDimension.HOUSING.value] = abs(housing_res.margin_households)

        # 2. Water Sizing
        water_res = self._size_water(site, incoming_hh, hh_size)
        results[InfrastructureDimension.WATER.value] = water_res
        if water_res.margin_households is not None and water_res.margin_households < 0:
            deficits[InfrastructureDimension.WATER.value] = abs(water_res.margin_households)

        # 3. Sanitation Sizing
        sanitation_res = self._size_sanitation(site, incoming_hh)
        results[InfrastructureDimension.SANITATION.value] = sanitation_res
        if sanitation_res.margin_households is not None and sanitation_res.margin_households < 0:
            deficits[InfrastructureDimension.SANITATION.value] = abs(sanitation_res.margin_households)

        # 4. Healthcare Sizing
        health_res = self._size_healthcare(site, incoming_hh)
        results[InfrastructureDimension.HEALTHCARE.value] = health_res
        if health_res.margin_households is not None and health_res.margin_households < 0:
            deficits[InfrastructureDimension.HEALTHCARE.value] = abs(health_res.margin_households)

        # 5. Shelter Sizing
        shelter_res = self._size_shelter(site, incoming_hh)
        results[InfrastructureDimension.SHELTER.value] = shelter_res
        if shelter_res.margin_households is not None and shelter_res.margin_households < 0:
            deficits[InfrastructureDimension.SHELTER.value] = abs(shelter_res.margin_households)

        return results, deficits

    def _size_housing(self, site: SiteCapacityInput, incoming_hh: int) -> DimensionSizingResult:
        """Size housing dimension in households and land area (sq.m)."""
        existing_cap = site.housing_capacity

        if existing_cap is None and site.area_sq_m is not None and site.area_sq_m > 0:
            existing_cap = int(site.area_sq_m / self.config.land_area_sq_m_per_household)

        if existing_cap is None:
            return DimensionSizingResult(
                dimension=InfrastructureDimension.HOUSING,
                name="Housing / Habitation",
                existing_capacity_households=None,
                demand_households=incoming_hh,
                margin_households=None,
                is_feasible=False,
                physical_unit="sq_m",
                notes="Housing capacity is unknown/unspecified; cannot verify safe residential capacity.",
            )

        margin = existing_cap - incoming_hh
        demand_area = incoming_hh * self.config.land_area_sq_m_per_household
        existing_area = (
            site.area_sq_m
            if site.area_sq_m is not None
            else existing_cap * self.config.land_area_sq_m_per_household
        )
        diff_area = existing_area - demand_area

        return DimensionSizingResult(
            dimension=InfrastructureDimension.HOUSING,
            name="Housing / Habitation",
            existing_capacity_households=existing_cap,
            demand_households=incoming_hh,
            margin_households=margin,
            is_feasible=margin >= 0,
            physical_unit="sq_m",
            existing_physical_quantity=round(existing_area, 1),
            demand_physical_quantity=round(demand_area, 1),
            deficit_or_surplus_physical=round(diff_area, 1),
            notes=f"Housing margin: {margin:+d} households ({diff_area:+.1f} sq.m usable land).",
        )

    def _size_water(
        self, site: SiteCapacityInput, incoming_hh: int, hh_size: float
    ) -> DimensionSizingResult:
        """Size water supply in households and Liters Per Day (LPD)."""
        existing_cap = site.water_capacity

        if existing_cap is None and site.water_supply_lpd is not None:
            lpd_per_hh = self.config.water_supply_lpd_per_capita * hh_size
            if lpd_per_hh > 0:
                existing_cap = int(site.water_supply_lpd / lpd_per_hh)

        if existing_cap is None:
            return DimensionSizingResult(
                dimension=InfrastructureDimension.WATER,
                name="Water Availability",
                existing_capacity_households=None,
                demand_households=incoming_hh,
                margin_households=None,
                is_feasible=False,
                physical_unit="liters_per_day",
                notes="Water capacity is unknown/unspecified; cannot verify safe water supply.",
            )

        margin = existing_cap - incoming_hh
        lpd_per_hh = self.config.water_supply_lpd_per_capita * hh_size
        demand_lpd = incoming_hh * lpd_per_hh
        existing_lpd = (
            site.water_supply_lpd
            if site.water_supply_lpd is not None
            else existing_cap * lpd_per_hh
        )
        diff_lpd = existing_lpd - demand_lpd

        return DimensionSizingResult(
            dimension=InfrastructureDimension.WATER,
            name="Water Availability",
            existing_capacity_households=existing_cap,
            demand_households=incoming_hh,
            margin_households=margin,
            is_feasible=margin >= 0,
            physical_unit="liters_per_day",
            existing_physical_quantity=round(existing_lpd, 1),
            demand_physical_quantity=round(demand_lpd, 1),
            deficit_or_surplus_physical=round(diff_lpd, 1),
            notes=f"Water margin: {margin:+d} households ({diff_lpd:+.1f} LPD based on {self.config.water_supply_lpd_per_capita:.0f} LPD/capita).",
        )

    def _size_sanitation(self, site: SiteCapacityInput, incoming_hh: int) -> DimensionSizingResult:
        """Size sanitation in households and toilet units."""
        existing_cap = site.sanitation_capacity

        if existing_cap is None and site.sanitation_units is not None:
            existing_cap = int(site.sanitation_units * self.config.households_per_sanitation_unit)

        if existing_cap is None:
            return DimensionSizingResult(
                dimension=InfrastructureDimension.SANITATION,
                name="Sanitation Facilities",
                existing_capacity_households=None,
                demand_households=incoming_hh,
                margin_households=None,
                is_feasible=False,
                physical_unit="sanitation_units",
                notes="Sanitation capacity is unknown/unspecified; cannot verify sanitation infrastructure.",
            )

        margin = existing_cap - incoming_hh
        demand_units = (
            math.ceil(incoming_hh / self.config.households_per_sanitation_unit)
            if incoming_hh > 0
            else 0
        )
        existing_units = (
            site.sanitation_units
            if site.sanitation_units is not None
            else math.ceil(existing_cap / self.config.households_per_sanitation_unit)
        )
        diff_units = existing_units - demand_units

        return DimensionSizingResult(
            dimension=InfrastructureDimension.SANITATION,
            name="Sanitation Facilities",
            existing_capacity_households=existing_cap,
            demand_households=incoming_hh,
            margin_households=margin,
            is_feasible=margin >= 0,
            physical_unit="sanitation_units",
            existing_physical_quantity=float(existing_units),
            demand_physical_quantity=float(demand_units),
            deficit_or_surplus_physical=float(diff_units),
            notes=f"Sanitation margin: {margin:+d} households ({diff_units:+d} sanitation units @ {self.config.households_per_sanitation_unit:.0f} hh/unit).",
        )

    def _size_healthcare(self, site: SiteCapacityInput, incoming_hh: int) -> DimensionSizingResult:
        """Size healthcare capacity in households."""
        existing_cap = site.healthcare_capacity

        if existing_cap is None:
            return DimensionSizingResult(
                dimension=InfrastructureDimension.HEALTHCARE,
                name="Healthcare Access",
                existing_capacity_households=None,
                demand_households=incoming_hh,
                margin_households=None,
                is_feasible=False,
                physical_unit="households",
                notes="Healthcare capacity is unknown/unspecified; field health survey or explicit capacity required.",
            )

        margin = existing_cap - incoming_hh
        return DimensionSizingResult(
            dimension=InfrastructureDimension.HEALTHCARE,
            name="Healthcare Access",
            existing_capacity_households=existing_cap,
            demand_households=incoming_hh,
            margin_households=margin,
            is_feasible=margin >= 0,
            physical_unit="households",
            existing_physical_quantity=float(existing_cap),
            demand_physical_quantity=float(incoming_hh),
            deficit_or_surplus_physical=float(margin),
            notes=f"Healthcare capacity margin: {margin:+d} households.",
        )

    def _size_shelter(self, site: SiteCapacityInput, incoming_hh: int) -> DimensionSizingResult:
        """Size emergency shelter capacity in households."""
        existing_cap = site.shelter_capacity

        if existing_cap is None:
            return DimensionSizingResult(
                dimension=InfrastructureDimension.SHELTER,
                name="Emergency Shelter",
                existing_capacity_households=None,
                demand_households=incoming_hh,
                margin_households=None,
                is_feasible=False,
                physical_unit="households",
                notes="Emergency shelter capacity is unknown/unspecified; field shelter survey or explicit capacity required.",
            )

        margin = existing_cap - incoming_hh
        return DimensionSizingResult(
            dimension=InfrastructureDimension.SHELTER,
            name="Emergency Shelter",
            existing_capacity_households=existing_cap,
            demand_households=incoming_hh,
            margin_households=margin,
            is_feasible=margin >= 0,
            physical_unit="households",
            existing_physical_quantity=float(existing_cap),
            demand_physical_quantity=float(incoming_hh),
            deficit_or_surplus_physical=float(margin),
            notes=f"Shelter capacity margin: {margin:+d} households.",
        )
