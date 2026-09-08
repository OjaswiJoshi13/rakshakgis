"""Typed data contracts, schemas, and result envelopes for Relocation Matching & Assignment (Chunk M4-04)."""

from datetime import datetime, timezone
from enum import Enum
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.relocation.capacity.contracts import SiteCapacityInput, SiteCapacityResult
from app.core.relocation.matching.errors import InvalidMatchingInputError
from app.core.relocation.suitability.contracts import (
    SiteSuitabilityInput,
    SiteSuitabilityResult,
    SuitabilityDecision,
)
from app.schemas.sites import parse_geometry_to_geojson_point


class AssignmentStatus(str, Enum):
    """Assignment outcome status for an affected village."""

    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"


class RejectionReasonCode(str, Enum):
    """Authoritative rejection reason codes for candidate sites evaluated during matching."""

    UNSAFE_SITE = "unsafe_site"                     # M4-02 hard safety constraint failed or overall score < threshold
    LOW_SUITABILITY = "low_suitability"             # Site classified as unsuitable
    INSUFFICIENT_CAPACITY = "insufficient_capacity" # Remaining capacity < village incoming household demand
    UNKNOWN_CAPACITY = "unknown_capacity"           # Critical capacity dimension missing / unknown
    SITE_UNAVAILABLE = "site_unavailable"           # Site marked rejected or inactive in registry
    NO_FEASIBLE_SITE = "no_feasible_site"           # Village-level failure when all evaluated sites failed


class MatchingAlgorithmType(str, Enum):
    """Algorithm identifier for the matching engine."""

    GREEDY_PRIORITY = "greedy_priority"


class VillageDemandInput(BaseModel):
    """Input representation of a village requiring relocation matching."""

    model_config = ConfigDict(frozen=True)

    village_id: Union[int, str]
    village_name: str
    priority_score: float = Field(..., ge=0.0, le=100.0, description="M3-12 relocation priority score (0-100)")
    priority_band: Optional[str] = Field(None, description="Urgency band: immediate, short_term, medium_term, monitor")
    incoming_households: int = Field(..., ge=0, description="Number of households requiring relocation")
    incoming_population: Optional[int] = Field(None, ge=0, description="Total estimated population requiring relocation")
    location: Optional[Tuple[float, float]] = Field(None, description="Coordinates (longitude, latitude) in WGS84")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def validate_numerical_inputs(cls, data: Any) -> Any:
        """Validate that all numerical fields are non-negative, finite, and not NaN."""
        if not isinstance(data, dict):
            return data

        for field_name in ("priority_score", "incoming_households", "incoming_population"):
            val = data.get(field_name)
            if val is not None and isinstance(val, (int, float)):
                if math.isnan(val):
                    raise InvalidMatchingInputError(f"Field '{field_name}' cannot be NaN.")
                if math.isinf(val):
                    raise InvalidMatchingInputError(f"Field '{field_name}' cannot be Infinity.")
                if val < 0:
                    raise InvalidMatchingInputError(f"Field '{field_name}' cannot be negative ({val}).")

        score = data.get("priority_score")
        if score is not None and isinstance(score, (int, float)) and score > 100.0:
            raise InvalidMatchingInputError(f"Field 'priority_score' cannot exceed 100.0 ({score}).")

        return data

    @classmethod
    def from_village_model(
        cls,
        village: Any,
        priority: Optional[Any] = None,
        incoming_households: Optional[int] = None,
        incoming_population: Optional[int] = None,
    ) -> "VillageDemandInput":
        """Construct VillageDemandInput from SQLAlchemy Village model instance."""
        # 1. Location
        loc_tuple = None
        if hasattr(village, "location") and village.location is not None:
            pt = parse_geometry_to_geojson_point(village.location)
            if pt:
                loc_tuple = pt.coordinates

        # 2. Priority
        p_score = 50.0
        p_band = None
        if priority is not None:
            p_score = priority.priority_score
            p_band = priority.priority_band
        elif hasattr(village, "relocation_priorities") and village.relocation_priorities:
            # Pick the active or most recent priority
            active_priorities = [p for p in village.relocation_priorities if getattr(p, "is_active", True)]
            target_p = active_priorities[0] if active_priorities else village.relocation_priorities[0]
            p_score = target_p.priority_score
            p_band = target_p.priority_band

        # 3. Demand
        hh = incoming_households
        pop = incoming_population
        if hh is None and priority is not None and getattr(priority, "estimated_households", None) is not None:
            hh = priority.estimated_households
        if pop is None and priority is not None and getattr(priority, "estimated_people", None) is not None:
            pop = priority.estimated_people

        if hh is None and hasattr(village, "population_profile") and village.population_profile:
            hh = village.population_profile.households
            if pop is None:
                pop = village.population_profile.total_population

        if hh is None:
            hh = 0

        return cls(
            village_id=village.id,
            village_name=village.name,
            priority_score=round(float(p_score), 2),
            priority_band=str(p_band) if p_band else None,
            incoming_households=hh,
            incoming_population=pop,
            location=loc_tuple,
            metadata={"district_id": getattr(village, "district_id", None)},
        )

    @classmethod
    def from_synthetic_feature(
        cls,
        feature_or_props: Any,
        priority_score: Optional[float] = None,
        priority_band: Optional[str] = None,
        incoming_households: Optional[int] = None,
    ) -> "VillageDemandInput":
        """Construct VillageDemandInput from synthetic GeoJSON village feature or properties."""
        props = feature_or_props
        coords = None
        if hasattr(feature_or_props, "properties"):
            props = feature_or_props.properties
            if hasattr(feature_or_props, "geometry") and hasattr(feature_or_props.geometry, "coordinates"):
                c = feature_or_props.geometry.coordinates
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    coords = (float(c[0]), float(c[1]))
        elif isinstance(feature_or_props, dict):
            if "properties" in feature_or_props:
                props = feature_or_props["properties"]
            if "geometry" in feature_or_props and "coordinates" in feature_or_props["geometry"]:
                c = feature_or_props["geometry"]["coordinates"]
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    coords = (float(c[0]), float(c[1]))

        def get_val(key: str, default: Any = None) -> Any:
            if isinstance(props, dict):
                return props.get(key, default)
            return getattr(props, key, default)

        v_id = get_val("id") or get_val("village_id") or "VILLAGE-SYNTHETIC"
        v_name = get_val("name") or get_val("village_name") or "Synthetic Village"

        # Demographics
        demographics = get_val("demographics", {})
        hh = incoming_households
        pop = None
        if hh is None:
            if isinstance(demographics, dict):
                hh = demographics.get("households", 0)
                pop = demographics.get("total_population", 0)
            else:
                hh = getattr(demographics, "households", 0)
                pop = getattr(demographics, "total_population", 0)

        # Priority
        score = priority_score
        band = priority_band
        if score is None:
            # Check properties for risk score or synthetic indicator
            risk = get_val("risk", {})
            if isinstance(risk, dict):
                score = risk.get("composite_score", 50.0)
            else:
                score = getattr(risk, "composite_score", 50.0)

        return cls(
            village_id=v_id,
            village_name=v_name,
            priority_score=round(float(score), 2),
            priority_band=str(band) if band else None,
            incoming_households=int(hh or 0),
            incoming_population=int(pop) if pop else None,
            location=coords,
            metadata={"is_synthetic": True},
        )


class MatchingSiteCandidate(BaseModel):
    """Candidate relocation site wrapper evaluated during matching."""

    site_id: Union[int, str]
    site_name: str
    location: Optional[Tuple[float, float]] = Field(None, description="Coordinates (longitude, latitude) in WGS84")
    status: str = Field(default="approved", description="Site status: proposed, approved, active, rejected")
    suitability_input: Optional[SiteSuitabilityInput] = None
    capacity_input: Optional[SiteCapacityInput] = None
    precomputed_suitability: Optional[SiteSuitabilityResult] = None
    precomputed_capacity: Optional[SiteCapacityResult] = None
    initial_available_capacity: Optional[int] = None

    @classmethod
    def from_candidate_site_model(
        cls, site: Any, overrides: Optional[Dict[str, Any]] = None
    ) -> "MatchingSiteCandidate":
        """Construct MatchingSiteCandidate from CandidateSite SQLAlchemy model instance."""
        loc_tuple = None
        if hasattr(site, "location") and site.location is not None:
            pt = parse_geometry_to_geojson_point(site.location)
            if pt:
                loc_tuple = pt.coordinates

        suit_input = SiteSuitabilityInput.from_candidate_site_model(site)
        cap_input = SiteCapacityInput.from_candidate_site_model(site, incoming_households=0, overrides=overrides)

        # Derive available capacity from site capacities relationship or capacity_households
        avail_cap = None
        if hasattr(site, "capacities") and site.capacities:
            cap_rec = site.capacities[0]
            max_hh = getattr(cap_rec, "max_households", None)
            alloc_hh = getattr(cap_rec, "allocated_households", 0) or 0
            if max_hh is not None:
                avail_cap = max(0, max_hh - alloc_hh)
        elif hasattr(site, "capacity_households") and site.capacity_households is not None:
            avail_cap = site.capacity_households

        return cls(
            site_id=site.id,
            site_name=site.name,
            location=loc_tuple,
            status=(site.status or "approved").lower(),
            suitability_input=suit_input,
            capacity_input=cap_input,
            initial_available_capacity=avail_cap,
        )

    @classmethod
    def from_synthetic_feature(
        cls, feature_or_props: Any, overrides: Optional[Dict[str, Any]] = None
    ) -> "MatchingSiteCandidate":
        """Construct MatchingSiteCandidate from synthetic candidate site GeoJSON feature."""
        props = feature_or_props
        coords = None
        if hasattr(feature_or_props, "properties"):
            props = feature_or_props.properties
            if hasattr(feature_or_props, "geometry") and hasattr(feature_or_props.geometry, "coordinates"):
                c = feature_or_props.geometry.coordinates
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    coords = (float(c[0]), float(c[1]))
        elif isinstance(feature_or_props, dict):
            if "properties" in feature_or_props:
                props = feature_or_props["properties"]
            if "geometry" in feature_or_props and "coordinates" in feature_or_props["geometry"]:
                c = feature_or_props["geometry"]["coordinates"]
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    coords = (float(c[0]), float(c[1]))

        def get_val(key: str, default: Any = None) -> Any:
            if isinstance(props, dict):
                return props.get(key, default)
            return getattr(props, key, default)

        s_id = get_val("id") or "SITE-SYNTHETIC"
        s_name = get_val("name") or "Synthetic Relocation Site"
        status = (get_val("status") or "approved").lower()

        # Build suitability and capacity inputs from synthetic properties
        suitability_dict = get_val("suitability", {})
        capacity_dict = get_val("capacity", {})

        def s_get(k: str, default: Any = None) -> Any:
            if isinstance(suitability_dict, dict):
                return suitability_dict.get(k, default)
            return getattr(suitability_dict, k, default)

        def c_get(k: str, default: Any = None) -> Any:
            if isinstance(capacity_dict, dict):
                return capacity_dict.get(k, default)
            return getattr(capacity_dict, k, default)

        max_hh = c_get("max_households", 0)
        max_pop = c_get("max_population", 0)
        avail_hh = c_get("available_households", max_hh)
        water_lpd = s_get("water_supply_lpd_per_capita", 70.0)

        suit_input = SiteSuitabilityInput(
            site_id=s_id,
            name=s_name,
            terrain_slope_deg=s_get("terrain_slope_deg", 10.0),
            hazard_buffer_distance_m=s_get("hazard_buffer_distance_m", 800.0),
            max_households=max_hh,
            available_households=avail_hh,
            road_width_m=s_get("road_width_m", 4.0),
            water_supply_lpd_per_capita=water_lpd,
            distance_to_highway_km=s_get("distance_to_highway_km", 2.0),
            distance_to_health_center_km=s_get("distance_to_health_center_km", 3.0),
            distance_to_school_km=s_get("distance_to_school_km", 2.5),
            distance_to_emergency_km=s_get("distance_to_emergency_km", 4.0),
            livelihood_potential=s_get("livelihood_potential", "moderate"),
            expansion_potential=s_get("expansion_potential", "moderate"),
        )

        cap_input = SiteCapacityInput.from_synthetic_feature(
            feature_or_props, incoming_households=0, overrides=overrides
        )

        return cls(
            site_id=s_id,
            site_name=s_name,
            location=coords,
            status=status,
            suitability_input=suit_input,
            capacity_input=cap_input,
        )


class CandidateEvaluationAudit(BaseModel):
    """Detailed explainability audit of an individual candidate site evaluated for a village."""

    model_config = ConfigDict(frozen=True)

    site_id: Union[int, str]
    site_name: str
    is_feasible: bool
    rejection_code: Optional[RejectionReasonCode] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    suitability_score: Optional[float] = None
    suitability_decision: Optional[str] = None
    available_capacity_before: Optional[int] = None
    capacity_margin: Optional[int] = None
    distance_km: Optional[float] = None
    rank_score: Optional[float] = None


class VillageAssignmentResult(BaseModel):
    """Result envelope for a single village relocation assignment."""

    model_config = ConfigDict(frozen=True)

    village_id: Union[int, str]
    village_name: str
    priority_score: float
    priority_band: Optional[str] = None
    incoming_households: int
    incoming_population: Optional[int] = None
    status: AssignmentStatus
    assigned_site_id: Optional[Union[int, str]] = None
    assigned_site_name: Optional[str] = None
    suitability_score: Optional[float] = None
    distance_km: Optional[float] = None
    available_capacity_before: Optional[int] = None
    available_capacity_after: Optional[int] = None
    selection_reason: Optional[str] = None
    unassigned_reason: Optional[str] = None
    unassigned_code: Optional[RejectionReasonCode] = None
    evaluated_candidates: List[CandidateEvaluationAudit] = Field(default_factory=list)


class RelocationMatchingResult(BaseModel):
    """Standardized batch result envelope for Relocation Matching & Assignment Engine."""

    model_config = ConfigDict(frozen=True)

    matching_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    algorithm: MatchingAlgorithmType = MatchingAlgorithmType.GREEDY_PRIORITY
    total_villages: int
    assigned_villages_count: int
    unassigned_villages_count: int
    total_households_demanded: int
    total_households_allocated: int
    total_households_unassigned: int
    assignments: List[VillageAssignmentResult] = Field(default_factory=list)
    site_remaining_capacities: Dict[str, int] = Field(default_factory=dict)
    summary_narrative: str
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region_profile_id: str = "himalayan_pilot"
    governance_notice: str = (
        "DECISION SUPPORT ONLY: Relocation matching recommendations are deterministic planning proposals "
        "for District Magistrate, District Officer, and Rehabilitation Committee sign-off. "
        "They do NOT constitute an automatic legal eviction or mandatory relocation order."
    )
