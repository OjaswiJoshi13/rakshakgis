"""Typed contracts, data transfer models, and schemas for Carrying Capacity & Infrastructure Sizing."""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.profiles.models import RegionProfile
from app.core.relocation.capacity.errors import InvalidCapacityDataError


class InfrastructureDimension(str, Enum):
    """Authoritative critical infrastructure dimensions evaluated for carrying capacity."""

    HOUSING = "housing"
    WATER = "water"
    SANITATION = "sanitation"
    HEALTHCARE = "healthcare"
    SHELTER = "shelter"


class CapacityFeasibilityStatus(str, Enum):
    """Evaluation status for carrying capacity and infrastructure sizing."""

    FEASIBLE = "feasible"
    INSUFFICIENT = "insufficient"
    INDETERMINATE = "indeterminate"


class CapacityPlanningConfig(BaseModel):
    """Regional planning parameters and resource standards governing capacity conversions."""

    model_config = ConfigDict(frozen=True)

    water_supply_lpd_per_capita: float = Field(default=70.0, gt=0.0)
    land_area_sq_m_per_household: float = Field(default=120.0, gt=0.0)
    persons_per_household: float = Field(default=4.17, gt=0.0)
    households_per_sanitation_unit: float = Field(default=4.0, gt=0.0)

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "CapacityPlanningConfig":
        """Construct configuration from strongly-typed RegionProfile."""
        assumptions = profile.site_capacity_assumptions
        return cls(
            water_supply_lpd_per_capita=assumptions.water_supply_lpd_per_capita,
            land_area_sq_m_per_household=assumptions.land_area_sq_m_per_household,
            persons_per_household=4.17,
            households_per_sanitation_unit=4.0,
        )


class DimensionSizingResult(BaseModel):
    """Infrastructure sizing and deficit evaluation for a single critical dimension."""

    model_config = ConfigDict(frozen=True)

    dimension: InfrastructureDimension
    name: str
    existing_capacity_households: Optional[int] = None
    demand_households: int
    margin_households: Optional[int] = None  # existing - demand (strictly preserves negative values)
    is_feasible: bool
    physical_unit: Optional[str] = None
    existing_physical_quantity: Optional[float] = None
    demand_physical_quantity: Optional[float] = None
    deficit_or_surplus_physical: Optional[float] = None
    notes: Optional[str] = None


class SiteCapacityInput(BaseModel):
    """Input parameters for evaluating a candidate site's carrying capacity."""

    site_id: Optional[Union[int, str]] = None
    site_name: str
    incoming_households: int = Field(default=0, ge=0)
    current_occupancy_households: int = Field(default=0, ge=0)
    household_size: Optional[float] = Field(None, gt=0.0)

    # 5 Critical Household Capacities (direct inputs)
    housing_capacity: Optional[int] = Field(None, ge=0)
    water_capacity: Optional[int] = Field(None, ge=0)
    sanitation_capacity: Optional[int] = Field(None, ge=0)
    healthcare_capacity: Optional[int] = Field(None, ge=0)
    shelter_capacity: Optional[int] = Field(None, ge=0)

    # Physical Infrastructure Metrics (used for sizing / fallback derivations)
    area_sq_m: Optional[float] = Field(None, ge=0.0)
    water_supply_lpd: Optional[float] = Field(None, ge=0.0)
    water_supply_lpd_per_capita: Optional[float] = Field(None, ge=0.0)
    sanitation_units: Optional[int] = Field(None, ge=0)
    has_health_center: Optional[bool] = None
    has_emergency_shelter: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def validate_numbers(cls, data: Any) -> Any:
        """Reject NaN, Infinity, or negative numbers across all input fields."""
        if not isinstance(data, dict):
            return data

        for k, v in data.items():
            if isinstance(v, (int, float)):
                if math.isnan(v):
                    raise InvalidCapacityDataError(f"Field '{k}' cannot be NaN.")
                if math.isinf(v):
                    raise InvalidCapacityDataError(f"Field '{k}' cannot be Infinity.")
                if v < 0:
                    raise InvalidCapacityDataError(f"Field '{k}' cannot be negative ({v}).")
        return data

    @classmethod
    def from_candidate_site_model(
        cls,
        site: Any,
        incoming_households: int = 0,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "SiteCapacityInput":
        """Construct SiteCapacityInput from SQLAlchemy CandidateSite model instance."""
        max_hh = 0
        allocated_hh = 0
        total_water_lpd = None
        sanitation_units = None
        water_per_capita = None
        max_pop = 0

        if hasattr(site, "capacities") and site.capacities:
            for cap in site.capacities:
                max_hh += cap.max_households or 0
                allocated_hh += cap.allocated_households or 0
                max_pop += cap.max_population or 0
                if cap.water_supply_lpd is not None:
                    total_water_lpd = (total_water_lpd or 0.0) + cap.water_supply_lpd
                if cap.sanitation_units is not None:
                    sanitation_units = (sanitation_units or 0) + cap.sanitation_units

        if total_water_lpd is not None and max_pop > 0:
            water_per_capita = total_water_lpd / max_pop

        # Check infrastructure assets for healthcare and shelter
        has_health = False
        has_shelter = False
        if hasattr(site, "infrastructures") and site.infrastructures:
            for infra in site.infrastructures:
                infra_t = (infra.infra_type or "").lower()
                status = (infra.status or "").lower()
                if status in ("operational", "active"):
                    if "medical" in infra_t or "health" in infra_t or "clinic" in infra_t:
                        has_health = True
                    if "shelter" in infra_t:
                        has_shelter = True

        # Derive baseline capacities where available
        effective_hh_size = (max_pop / max_hh) if (max_hh > 0 and max_pop > 0) else None

        water_cap = None
        if total_water_lpd is not None and effective_hh_size:
            # 70.0 LPD per person standard
            water_cap = int(total_water_lpd / (70.0 * effective_hh_size))

        sanitation_cap = None
        if sanitation_units is not None:
            sanitation_cap = int(sanitation_units * 4)  # 4 households per unit

        data = {
            "site_id": site.id,
            "site_name": site.name,
            "incoming_households": incoming_households,
            "current_occupancy_households": allocated_hh,
            "household_size": effective_hh_size,
            "housing_capacity": max_hh if max_hh > 0 else None,
            "water_capacity": water_cap,
            "sanitation_capacity": sanitation_cap,
            "healthcare_capacity": None,  # Explicitly unknown without survey/override
            "shelter_capacity": None,     # Explicitly unknown without survey/override
            "area_sq_m": site.area_sq_m,
            "water_supply_lpd": total_water_lpd,
            "water_supply_lpd_per_capita": water_per_capita,
            "sanitation_units": sanitation_units,
            "has_health_center": has_health,
            "has_emergency_shelter": has_shelter,
        }

        if overrides:
            data.update(overrides)

        return cls(**data)

    @classmethod
    def from_synthetic_feature(
        cls,
        feature_or_props: Any,
        incoming_households: int = 0,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "SiteCapacityInput":
        """Construct SiteCapacityInput from synthetic candidate site GeoJSON feature or dict."""
        props = feature_or_props
        if hasattr(feature_or_props, "properties"):
            props = feature_or_props.properties
        elif isinstance(feature_or_props, dict) and "properties" in feature_or_props:
            props = feature_or_props["properties"]

        suitability = {}
        capacity = {}
        if hasattr(props, "suitability"):
            suitability = getattr(props, "suitability", {})
            capacity = getattr(props, "capacity", {})
        elif isinstance(props, dict):
            suitability = props.get("suitability", {})
            capacity = props.get("capacity", {})

        def get_val(key: str, *sources: Any) -> Any:
            for s in sources:
                if isinstance(s, dict) and key in s:
                    return s[key]
                if hasattr(s, key):
                    return getattr(s, key)
            return None

        max_hh = get_val("max_households", capacity, props) or 0
        max_pop = get_val("max_population", capacity, props) or 0
        allocated_hh = get_val("allocated_households", capacity, props) or 0
        sanitation_units = get_val("sanitation_units", capacity, props)
        water_lpd_capita = get_val("water_supply_lpd_per_capita", suitability, props)
        area_sq_m = get_val("area_sq_m", suitability, props)

        hh_size = (max_pop / max_hh) if (max_hh > 0 and max_pop > 0) else 4.17
        total_water = (water_lpd_capita * max_pop) if (water_lpd_capita and max_pop) else None

        water_cap = None
        if total_water is not None and hh_size:
            water_cap = int(total_water / (70.0 * hh_size))

        sanitation_cap = None
        if sanitation_units is not None:
            sanitation_cap = int(sanitation_units * 4)

        data = {
            "site_id": get_val("id", props),
            "site_name": get_val("name", props) or "Synthetic Relocation Site",
            "incoming_households": incoming_households,
            "current_occupancy_households": allocated_hh,
            "household_size": hh_size,
            "housing_capacity": max_hh if max_hh > 0 else None,
            "water_capacity": water_cap,
            "sanitation_capacity": sanitation_cap,
            "healthcare_capacity": None,
            "shelter_capacity": None,
            "area_sq_m": area_sq_m,
            "water_supply_lpd": total_water,
            "water_supply_lpd_per_capita": water_lpd_capita,
            "sanitation_units": sanitation_units,
        }

        if overrides:
            data.update(overrides)

        return cls(**data)


class SiteCapacityResult(BaseModel):
    """Standardized result envelope for carrying capacity and infrastructure sizing."""

    model_config = ConfigDict(frozen=True)

    site_id: Optional[Union[int, str]] = None
    site_name: str
    effective_capacity_households: Optional[int] = None
    current_occupancy_households: int = 0
    available_capacity_households: Optional[int] = None
    incoming_households: int = 0
    capacity_margin_households: Optional[int] = None  # available - incoming (preserves negative margins)
    remaining_capacity_households: Optional[int] = None  # identical to margin
    feasible: bool
    limiting_factors: List[str] = Field(default_factory=list)
    unknown_dimensions: List[str] = Field(default_factory=list)
    infrastructure_results: Dict[str, DimensionSizingResult] = Field(default_factory=dict)
    deficits: Dict[str, int] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
