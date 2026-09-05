"""Typed schemas, enumerations, and contracts for the Multi-Criteria Site Suitability Engine."""

from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.profiles.models import RegionProfile, SiteCapacityAssumptions
from app.core.relocation.suitability.errors import InvalidSiteDataError, SuitabilityConfigError


class CriterionType(str, Enum):
    """The 9 authoritative criteria for candidate site suitability evaluation."""

    HAZARD_SAFETY = "hazard_safety"                 # 30% (0.30)
    CAPACITY = "capacity"                           # 20% (0.20)
    ROAD_ACCESS = "road_access"                     # 10% (0.10)
    WATER_AVAILABILITY = "water_availability"       # 10% (0.10)
    HEALTHCARE_ACCESS = "healthcare_access"         # 10% (0.10)
    SCHOOL_ACCESS = "school_access"                 # 5% (0.05)
    EMERGENCY_SERVICES = "emergency_services"       # 5% (0.05)
    LIVELIHOOD_ACCESS = "livelihood_access"         # 5% (0.05)
    EXPANSION_POTENTIAL = "expansion_potential"     # 5% (0.05)

    @property
    def label(self) -> str:
        """Human-readable criterion label."""
        mapping = {
            CriterionType.HAZARD_SAFETY: "Hazard Safety",
            CriterionType.CAPACITY: "Capacity & Resource Limits",
            CriterionType.ROAD_ACCESS: "Road & Transport Access",
            CriterionType.WATER_AVAILABILITY: "Water Availability",
            CriterionType.HEALTHCARE_ACCESS: "Healthcare Access",
            CriterionType.SCHOOL_ACCESS: "School Access",
            CriterionType.EMERGENCY_SERVICES: "Emergency Services",
            CriterionType.LIVELIHOOD_ACCESS: "Livelihood Access",
            CriterionType.EXPANSION_POTENTIAL: "Expansion Potential",
        }
        return mapping[self]


class SuitabilityDecision(str, Enum):
    """Authoritative suitability classification decision for candidate relocation sites."""

    SUITABLE = "suitable"             # Eligible and recommended for relocation
    CONSTRAINED = "constrained"       # Eligible but has identified capacity/infrastructure bottlenecks
    UNSUITABLE = "unsuitable"         # Overall suitability score below acceptable threshold
    INELIGIBLE = "ineligible"         # Failed one or more hard safety/capacity constraints


class HardConstraintType(str, Enum):
    """Hard constraints that must pass before any weighted score eligibility."""

    HAZARD_SLOPE = "hazard_slope"
    HAZARD_BUFFER = "hazard_buffer"
    USABLE_CAPACITY = "usable_capacity"



class ConstraintEvaluation(BaseModel):
    """Evaluation record of an individual hard constraint."""

    constraint_type: HardConstraintType
    name: str
    passed: bool
    actual_value: Optional[Union[float, int, str]] = None
    threshold_value: Optional[Union[float, int, str]] = None
    reason: Optional[str] = None


class CriterionScoreResult(BaseModel):
    """Score, weight, and weighted contribution for a single criterion."""

    criterion: CriterionType
    criterion_name: str
    raw_score: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Configured weight 0-1")
    weighted_contribution: float = Field(..., ge=0.0, le=100.0, description="raw_score * weight")
    description: str
    audit_notes: Optional[str] = None


class SuitabilityWeightsConfig(BaseModel):
    """Authoritative weights configuration for candidate site suitability evaluation.

    Authoritative weights:
      1. Hazard Safety       - 30% (0.30)
      2. Capacity            - 20% (0.20)
      3. Road Access         - 10% (0.10)
      4. Water Availability  - 10% (0.10)
      5. Healthcare Access   - 10% (0.10)
      6. School Access       -  5% (0.05)
      7. Emergency Services  -  5% (0.05)
      8. Livelihood Access   -  5% (0.05)
      9. Expansion Potential -  5% (0.05)
    Total = 1.00 (100%).
    """

    model_config = ConfigDict(frozen=True)

    hazard_safety: float = Field(default=0.30, ge=0.0, le=1.0)
    capacity: float = Field(default=0.20, ge=0.0, le=1.0)
    road_access: float = Field(default=0.10, ge=0.0, le=1.0)
    water_availability: float = Field(default=0.10, ge=0.0, le=1.0)
    healthcare_access: float = Field(default=0.10, ge=0.0, le=1.0)
    school_access: float = Field(default=0.05, ge=0.0, le=1.0)
    emergency_services: float = Field(default=0.05, ge=0.0, le=1.0)
    livelihood_access: float = Field(default=0.05, ge=0.0, le=1.0)
    expansion_potential: float = Field(default=0.05, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "SuitabilityWeightsConfig":
        total = (
            self.hazard_safety
            + self.capacity
            + self.road_access
            + self.water_availability
            + self.healthcare_access
            + self.school_access
            + self.emergency_services
            + self.livelihood_access
            + self.expansion_potential
        )
        if not math.isclose(total, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise SuitabilityConfigError(
                f"Suitability weights must sum strictly to 1.0 (100%), got {total:.6f}"
            )
        return self

    def get_weight(self, criterion: CriterionType) -> float:
        """Lookup weight for a specific criterion type."""
        mapping = {
            CriterionType.HAZARD_SAFETY: self.hazard_safety,
            CriterionType.CAPACITY: self.capacity,
            CriterionType.ROAD_ACCESS: self.road_access,
            CriterionType.WATER_AVAILABILITY: self.water_availability,
            CriterionType.HEALTHCARE_ACCESS: self.healthcare_access,
            CriterionType.SCHOOL_ACCESS: self.school_access,
            CriterionType.EMERGENCY_SERVICES: self.emergency_services,
            CriterionType.LIVELIHOOD_ACCESS: self.livelihood_access,
            CriterionType.EXPANSION_POTENTIAL: self.expansion_potential,
        }
        return mapping[criterion]


class SuitabilityThresholdsConfig(BaseModel):
    """Regional and domain thresholds for hard constraints and decision grading."""

    model_config = ConfigDict(frozen=True)

    max_safe_slope_deg: float = Field(default=15.0, ge=0.0, le=90.0)
    min_hazard_buffer_m: float = Field(default=500.0, ge=0.0)
    min_water_lpd_per_capita: float = Field(default=70.0, ge=0.0)
    min_viable_households: int = Field(default=20, ge=1)
    suitable_score_threshold: float = Field(default=65.0, ge=0.0, le=100.0)
    constrained_score_threshold: float = Field(default=40.0, ge=0.0, le=100.0)

    @classmethod
    def from_profile(cls, profile: RegionProfile) -> "SuitabilityThresholdsConfig":
        """Factory method to source thresholds from regional profile capacity assumptions."""
        assumptions: SiteCapacityAssumptions = profile.site_capacity_assumptions
        return cls(
            max_safe_slope_deg=assumptions.max_safe_slope_deg,
            min_hazard_buffer_m=assumptions.hazard_buffer_m,
            min_water_lpd_per_capita=assumptions.water_supply_lpd_per_capita,
        )


class SiteSuitabilityInput(BaseModel):
    """Standardized input DTO consumed by the Multi-Criteria Site Suitability Engine."""

    site_id: Optional[Union[int, str]] = None
    name: str
    district_id: Optional[int] = None
    district_name: Optional[str] = None

    # Topography & Hazard Attributes
    terrain_slope_deg: Optional[float] = Field(None, ge=0.0, le=90.0)
    hazard_buffer_distance_m: Optional[float] = Field(None, ge=0.0)
    soil_stability: Optional[str] = None
    elevation_m: Optional[float] = None

    # Capacity Attributes
    max_households: Optional[int] = Field(None, ge=0)
    max_population: Optional[int] = Field(None, ge=0)
    available_households: Optional[int] = Field(None, ge=0)
    available_population: Optional[int] = Field(None, ge=0)
    area_sq_m: Optional[float] = Field(None, ge=0.0)
    sanitation_units: Optional[int] = Field(None, ge=0)

    # Road & Transport Access
    road_width_m: Optional[float] = Field(None, ge=0.0)
    distance_to_highway_km: Optional[float] = Field(None, ge=0.0)
    all_weather_access: Optional[bool] = None

    # Water Availability
    water_supply_lpd_per_capita: Optional[float] = Field(None, ge=0.0)
    water_source_distance_m: Optional[float] = Field(None, ge=0.0)
    perennial_water_source: Optional[bool] = None

    # Healthcare Access
    distance_to_health_center_km: Optional[float] = Field(None, ge=0.0)
    has_on_site_health_center: bool = False

    # School Access
    distance_to_school_km: Optional[float] = Field(None, ge=0.0)

    # Emergency Services
    distance_to_emergency_km: Optional[float] = Field(None, ge=0.0)
    has_on_site_helipad_or_shelter: bool = False

    # Livelihood Access
    livelihood_potential: Optional[str] = None  # "high", "moderate", "low"
    distance_to_farmland_km: Optional[float] = Field(None, ge=0.0)
    distance_to_market_km: Optional[float] = Field(None, ge=0.0)

    # Expansion Potential
    expansion_potential: Optional[str] = None  # "high", "moderate", "low", "none"

    @classmethod
    def from_candidate_site_model(cls, site: Any) -> "SiteSuitabilityInput":
        """Construct from SQLAlchemy CandidateSite model instance with loaded relationships."""
        # Aggregate capacity
        max_hh = 0
        max_pop = 0
        avail_hh = 0
        avail_pop = 0
        water_lpd_total = None
        sanitation = None

        if hasattr(site, "capacities") and site.capacities:
            for cap in site.capacities:
                max_hh += cap.max_households or 0
                max_pop += cap.max_population or 0
                avail_hh += cap.available_households or 0
                avail_pop += cap.available_population or 0
                if cap.water_supply_lpd is not None:
                    water_lpd_total = (water_lpd_total or 0.0) + cap.water_supply_lpd
                if cap.sanitation_units is not None:
                    sanitation = (sanitation or 0) + cap.sanitation_units

        # Infer per capita water if total water and pop available
        water_per_capita = None
        if water_lpd_total is not None and max_pop > 0:
            water_per_capita = water_lpd_total / max_pop

        # Check infrastructure types
        has_health = False
        has_emergency = False
        if hasattr(site, "infrastructures") and site.infrastructures:
            for infra in site.infrastructures:
                infra_t = (infra.infra_type or "").lower()
                status = (infra.status or "").lower()
                if status in ("operational", "active"):
                    if "medical" in infra_t or "health" in infra_t or "clinic" in infra_t:
                        has_health = True
                    if "helipad" in infra_t or "shelter" in infra_t:
                        has_emergency = True

        return cls(
            site_id=site.id,
            name=site.name,
            district_id=site.district_id,
            terrain_slope_deg=site.terrain_slope_deg,
            area_sq_m=site.area_sq_m,
            elevation_m=site.elevation_m,
            max_households=max_hh if max_hh > 0 else None,
            max_population=max_pop if max_pop > 0 else None,
            available_households=avail_hh if avail_hh > 0 else None,
            available_population=avail_pop if avail_pop > 0 else None,
            sanitation_units=sanitation,
            water_supply_lpd_per_capita=water_per_capita,
            has_on_site_health_center=has_health,
            has_on_site_helipad_or_shelter=has_emergency,
        )

    @classmethod
    def from_synthetic_feature(cls, feature_or_props: Any) -> "SiteSuitabilityInput":
        """Construct from synthetic candidate site GeoJSON feature or properties dict."""
        props = feature_or_props
        if hasattr(feature_or_props, "properties"):
            props = feature_or_props.properties
        elif isinstance(feature_or_props, dict) and "properties" in feature_or_props:
            props = feature_or_props["properties"]

        # Extract nested dicts if present (loader schemas)
        suitability = {}
        capacity = {}
        if hasattr(props, "suitability"):
            suitability = props.suitability.model_dump() if hasattr(props.suitability, "model_dump") else props.suitability
        elif isinstance(props, dict) and "suitability" in props:
            suitability = props["suitability"]

        if hasattr(props, "capacity"):
            capacity = props.capacity.model_dump() if hasattr(props.capacity, "model_dump") else props.capacity
        elif isinstance(props, dict) and "capacity" in props:
            capacity = props["capacity"]

        site_id = getattr(props, "id", None) or (props.get("id") if isinstance(props, dict) else None)
        name = getattr(props, "name", None) or (props.get("name") if isinstance(props, dict) else "Synthetic Site")
        district_name = getattr(props, "district_name", None) or (props.get("district_name") if isinstance(props, dict) else None)

        def get_val(key, *sources, default=None):
            for src in sources:
                if src and isinstance(src, dict) and key in src and src[key] is not None:
                    return src[key]
                elif src and hasattr(src, key) and getattr(src, key) is not None:
                    return getattr(src, key)
            return default

        return cls(
            site_id=site_id,
            name=name,
            district_name=district_name,
            terrain_slope_deg=get_val("terrain_slope_deg", suitability, props),
            hazard_buffer_distance_m=get_val("hazard_buffer_distance_m", suitability, props),
            soil_stability=get_val("soil_stability", suitability, props),
            elevation_m=get_val("elevation_m", suitability, props),
            area_sq_m=get_val("area_sq_m", suitability, props),
            road_width_m=get_val("road_width_m", suitability, props),
            distance_to_highway_km=get_val("distance_to_highway_km", suitability, props),
            all_weather_access=get_val("all_weather_access", suitability, props),
            water_supply_lpd_per_capita=get_val("water_supply_lpd_per_capita", suitability, props),
            water_source_distance_m=get_val("water_source_distance_m", suitability, props),
            perennial_water_source=get_val("perennial_water_source", suitability, props),
            distance_to_health_center_km=get_val("distance_to_health_center_km", suitability, props),
            distance_to_school_km=get_val("distance_to_school_km", suitability, props),
            distance_to_emergency_km=get_val("distance_to_emergency_km", suitability, props),
            distance_to_market_km=get_val("distance_to_market_km", suitability, props),
            distance_to_farmland_km=get_val("distance_to_farmland_km", suitability, props),
            livelihood_potential=get_val("livelihood_potential", suitability, props),
            expansion_potential=get_val("expansion_potential", suitability, props),
            max_households=get_val("max_households", capacity, props),
            max_population=get_val("max_population", capacity, props),
            available_households=get_val("available_households", capacity, props, default=get_val("max_households", capacity, props)),
            available_population=get_val("available_population", capacity, props, default=get_val("max_population", capacity, props)),
            sanitation_units=get_val("sanitation_units", capacity, props),
        )


class SiteSuitabilityResult(BaseModel):
    """Complete, transparent, and explainable evaluation result envelope."""

    site_id: Optional[Union[int, str]] = None
    site_name: str
    is_eligible: bool = Field(
        ...,
        description="True ONLY if all hard constraints pass and overall score meets eligibility threshold.",
    )
    decision: SuitabilityDecision = Field(
        ..., description="Categorical suitability decision for officer review."
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted multi-criteria suitability score (0.0 - 100.0).",
    )
    criteria_scores: Dict[str, CriterionScoreResult] = Field(
        ..., description="Breakdown of normalized scores and weighted contributions for all 9 criteria."
    )
    hard_constraints: List[ConstraintEvaluation] = Field(
        ..., description="List of all hard constraints evaluated and their individual pass/fail status."
    )
    failed_constraints: List[str] = Field(
        default_factory=list,
        description="Identifiers/names of failed hard constraints, if any.",
    )
    summary_reasons: List[str] = Field(
        default_factory=list,
        description="Human-readable audit and rationale statements suitable for officer review.",
    )
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of evaluation.",
    )
    config_version: str = "1.0.0"
