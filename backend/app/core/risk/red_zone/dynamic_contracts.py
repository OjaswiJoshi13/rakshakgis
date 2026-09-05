"""Data contracts, schemas, and result envelopes for Dynamic Red Zones & Threshold Triggers (Chunk M3-11)."""

from datetime import datetime
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import MultiPolygon

from app.core.profiles.models import DangerLevel, RegionProfile
from app.core.risk.red_zone.contracts import RedZoneType
from app.core.risk.red_zone.errors import InvalidGeophysicalDataError, RedZoneConfigError
from app.data.providers.contracts import ProviderProvenance


# =====================================================================
# Status, Indicator & Operator Enums
# =====================================================================


class DynamicTriggerStatus(str, Enum):
    """Evaluation status for dynamic threshold triggers and temporary red zones."""

    NO_TRIGGER = "no_trigger"
    TRIGGERED = "triggered"
    INSUFFICIENT_DATA = "insufficient_data"


class DynamicHazardIndicator(str, Enum):
    """Hazard indicators supported by the dynamic threshold trigger engine."""

    RAINFALL_24H = "rainfall_24h"
    SEISMIC_MMI = "seismic_mmi"
    SLOPE_DEG = "slope_deg"
    WATER_LEVEL_ABOVE_DANGER = "water_level_above_danger"
    LANDSLIDE_DEBRIS_VOLUME = "landslide_debris_volume"
    LANDSLIDE_ACTIVITY = "landslide_activity"
    CUSTOM = "custom"


class ComparisonOperator(str, Enum):
    """Comparison operator used to evaluate observed telemetry against configured thresholds."""

    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="

    def evaluate(self, observed: float, threshold: float) -> bool:
        """Deterministically evaluate observed value against threshold."""
        if self == ComparisonOperator.GREATER_THAN:
            return observed > threshold
        elif self == ComparisonOperator.GREATER_THAN_OR_EQUAL:
            return observed >= threshold
        elif self == ComparisonOperator.LESS_THAN:
            return observed < threshold
        elif self == ComparisonOperator.LESS_THAN_OR_EQUAL:
            return observed <= threshold
        elif self == ComparisonOperator.EQUAL:
            return observed == threshold
        raise ValueError(f"Unsupported comparison operator: {self}")


# =====================================================================
# Threshold Configuration Contract
# =====================================================================


class DynamicThresholdConfig(BaseModel):
    """Strongly typed dynamic hazard threshold configuration.

    Resolves criteria strictly from an authoritative RegionProfile,
    guaranteeing zero hardcoded constants in engine logic.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    rainfall_trigger_24h_mm: float = Field(..., ge=0.0)
    seismic_trigger_mmi: Optional[float] = Field(default=None, ge=1.0, le=12.0)
    slope_trigger_min_deg: float = Field(..., ge=0.0, le=90.0)
    water_level_trigger_m_above_danger: Optional[float] = Field(default=None, ge=0.0)
    landslide_debris_volume_trigger_m3: Optional[float] = Field(default=None, ge=0.0)

    rainfall_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL
    seismic_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL
    slope_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL
    water_level_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL
    landslide_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL

    default_danger_level: DangerLevel = DangerLevel.VERY_HIGH
    buffer_distance_m: float = Field(default=500.0, gt=0.0)

    @model_validator(mode="before")
    @classmethod
    def validate_finite_inputs(cls, values: Any) -> Any:
        if isinstance(values, dict):
            for k, v in values.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    raise RedZoneConfigError(f"Dynamic threshold '{k}' cannot be NaN or infinite.")
        return values

    @model_validator(mode="after")
    def validate_finite_bounds(self) -> "DynamicThresholdConfig":
        for field_name in (
            "rainfall_trigger_24h_mm",
            "seismic_trigger_mmi",
            "slope_trigger_min_deg",
            "water_level_trigger_m_above_danger",
            "landslide_debris_volume_trigger_m3",
            "buffer_distance_m",
        ):
            val = getattr(self, field_name)
            if val is not None:
                if math.isnan(val) or math.isinf(val):
                    raise RedZoneConfigError(f"Dynamic threshold '{field_name}' cannot be NaN or infinite.")
        return self

    @classmethod
    def from_profile(
        cls,
        profile: RegionProfile,
        *,
        water_level_trigger_m: Optional[float] = None,
        landslide_debris_volume_trigger_m3: Optional[float] = None,
        buffer_distance_m: Optional[float] = None,
        rainfall_operator: Optional[ComparisonOperator] = None,
        seismic_operator: Optional[ComparisonOperator] = None,
        slope_operator: Optional[ComparisonOperator] = None,
    ) -> "DynamicThresholdConfig":
        """Factory resolving dynamic trigger thresholds directly from an active RegionProfile."""
        try:
            dyn_triggers = profile.red_zone_thresholds.dynamic_triggers
            buffer_dist = (
                buffer_distance_m
                if buffer_distance_m is not None
                else float(profile.site_capacity_assumptions.hazard_buffer_m)
            )

            kwargs: Dict[str, Any] = {
                "rainfall_trigger_24h_mm": float(dyn_triggers.rainfall_trigger_24h_mm),
                "seismic_trigger_mmi": (
                    float(dyn_triggers.seismic_trigger_mmi)
                    if dyn_triggers.seismic_trigger_mmi is not None
                    else None
                ),
                "slope_trigger_min_deg": float(dyn_triggers.slope_trigger_min_deg),
                "default_danger_level": dyn_triggers.default_danger_level,
                "buffer_distance_m": float(buffer_dist),
            }

            if water_level_trigger_m is not None:
                kwargs["water_level_trigger_m_above_danger"] = float(water_level_trigger_m)
            if landslide_debris_volume_trigger_m3 is not None:
                kwargs["landslide_debris_volume_trigger_m3"] = float(landslide_debris_volume_trigger_m3)
            if rainfall_operator is not None:
                kwargs["rainfall_operator"] = rainfall_operator
            if seismic_operator is not None:
                kwargs["seismic_operator"] = seismic_operator
            if slope_operator is not None:
                kwargs["slope_operator"] = slope_operator

            return cls(**kwargs)
        except Exception as e:
            raise RedZoneConfigError(f"Failed to resolve dynamic red zone thresholds from profile: {e}") from e


# =====================================================================
# Observation Input Contract
# =====================================================================


class DynamicHazardObservation(BaseModel):
    """Dynamic hazard observation or telemetry reading for real-time trigger evaluation."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    observation_id: Optional[str] = None
    record_id: Optional[str] = None
    village_id: Optional[str] = None
    village_name: Optional[str] = None
    name: Optional[str] = None
    hazard_type: Optional[str] = None
    indicator: Optional[Union[DynamicHazardIndicator, str]] = None
    observed_value: Optional[float] = None
    rainfall_24h_mm: Optional[float] = None
    seismic_intensity_mmi: Optional[float] = None
    water_level_m_above_danger: Optional[float] = None
    debris_volume_cu_m: Optional[float] = None
    slope_deg: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[Union[Tuple[float, float], List[float], Dict[str, Any], Any]] = None
    location_geometry: Optional[Any] = None
    geometry: Optional[Any] = None
    observed_at: Optional[Union[datetime, str]] = None
    is_available: bool = True
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def harmonize_synonyms(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # record_id <-> observation_id
            if "observation_id" not in values and "record_id" in values:
                values["observation_id"] = values["record_id"]
            elif "record_id" not in values and "observation_id" in values:
                values["record_id"] = values["observation_id"]

            # village_name <-> name
            if "name" not in values and "village_name" in values:
                values["name"] = values["village_name"]
            elif "village_name" not in values and "name" in values:
                values["village_name"] = values["name"]

            # location_geometry <-> location or geometry
            if "location_geometry" in values and values["location_geometry"] is not None:
                loc_geom = values["location_geometry"]
                if hasattr(loc_geom, "geom_type") and loc_geom.geom_type == "Point":
                    if "location" not in values or values["location"] is None:
                        values["location"] = loc_geom
                else:
                    if "geometry" not in values or values["geometry"] is None:
                        values["geometry"] = loc_geom

            # Infer observed_value and indicator from hazard-specific fields
            if values.get("observed_value") is None:
                if values.get("rainfall_24h_mm") is not None:
                    values["observed_value"] = values["rainfall_24h_mm"]
                    if not values.get("indicator"):
                        values["indicator"] = DynamicHazardIndicator.RAINFALL_24H
                    if not values.get("hazard_type"):
                        values["hazard_type"] = "rainfall"
                    if not values.get("unit"):
                        values["unit"] = "mm"
                elif values.get("seismic_intensity_mmi") is not None:
                    values["observed_value"] = values["seismic_intensity_mmi"]
                    if not values.get("indicator"):
                        values["indicator"] = DynamicHazardIndicator.SEISMIC_MMI
                    if not values.get("hazard_type"):
                        values["hazard_type"] = "seismic"
                    if not values.get("unit"):
                        values["unit"] = "MMI"
                elif values.get("water_level_m_above_danger") is not None:
                    values["observed_value"] = values["water_level_m_above_danger"]
                    if not values.get("indicator"):
                        values["indicator"] = DynamicHazardIndicator.WATER_LEVEL_ABOVE_DANGER
                    if not values.get("hazard_type"):
                        values["hazard_type"] = "flood"
                    if not values.get("unit"):
                        values["unit"] = "m"
                elif values.get("debris_volume_cu_m") is not None:
                    values["observed_value"] = values["debris_volume_cu_m"]
                    if not values.get("indicator"):
                        values["indicator"] = DynamicHazardIndicator.LANDSLIDE_DEBRIS_VOLUME
                    if not values.get("hazard_type"):
                        values["hazard_type"] = "landslide"
                    if not values.get("unit"):
                        values["unit"] = "m3"
                elif values.get("slope_deg") is not None:
                    values["observed_value"] = values["slope_deg"]
                    if not values.get("indicator"):
                        values["indicator"] = DynamicHazardIndicator.SLOPE_DEG
                    if not values.get("hazard_type"):
                        values["hazard_type"] = "slope"
                    if not values.get("unit"):
                        values["unit"] = "deg"
        return values

    @model_validator(mode="after")
    def validate_numeric_invariants(self) -> "DynamicHazardObservation":
        # Validate observed_value
        if self.observed_value is not None:
            if math.isnan(self.observed_value) or math.isinf(self.observed_value):
                raise InvalidGeophysicalDataError("observed_value cannot be NaN or infinite.")

        # Validate rainfall
        if self.rainfall_24h_mm is not None:
            if math.isnan(self.rainfall_24h_mm) or math.isinf(self.rainfall_24h_mm):
                raise InvalidGeophysicalDataError("rainfall_24h_mm cannot be NaN or infinite.")
            if self.rainfall_24h_mm < 0.0:
                raise InvalidGeophysicalDataError(
                    f"rainfall_24h_mm cannot be negative, got {self.rainfall_24h_mm}."
                )

        # Validate seismic
        if self.seismic_intensity_mmi is not None:
            if math.isnan(self.seismic_intensity_mmi) or math.isinf(self.seismic_intensity_mmi):
                raise InvalidGeophysicalDataError("seismic_intensity_mmi cannot be NaN or infinite.")
            if not (1.0 <= self.seismic_intensity_mmi <= 12.0):
                raise InvalidGeophysicalDataError(
                    f"seismic_intensity_mmi must be within [1.0, 12.0], got {self.seismic_intensity_mmi}."
                )

        # Validate slope
        if self.slope_deg is not None:
            if math.isnan(self.slope_deg) or math.isinf(self.slope_deg):
                raise InvalidGeophysicalDataError("slope_deg cannot be NaN or infinite.")
            if not (0.0 <= self.slope_deg <= 90.0):
                raise InvalidGeophysicalDataError(
                    f"slope_deg must be within [0.0, 90.0] degrees, got {self.slope_deg}."
                )

        # Validate water level
        if self.water_level_m_above_danger is not None:
            if math.isnan(self.water_level_m_above_danger) or math.isinf(self.water_level_m_above_danger):
                raise InvalidGeophysicalDataError("water_level_m_above_danger cannot be NaN or infinite.")
            if self.water_level_m_above_danger < 0.0:
                raise InvalidGeophysicalDataError(
                    f"water_level_m_above_danger cannot be negative, got {self.water_level_m_above_danger}."
                )

        # Validate debris volume
        if self.debris_volume_cu_m is not None:
            if math.isnan(self.debris_volume_cu_m) or math.isinf(self.debris_volume_cu_m):
                raise InvalidGeophysicalDataError("debris_volume_cu_m cannot be NaN or infinite.")
            if self.debris_volume_cu_m < 0.0:
                raise InvalidGeophysicalDataError(
                    f"debris_volume_cu_m cannot be negative, got {self.debris_volume_cu_m}."
                )

        return self


# =====================================================================
# Explainability & Audit Trail Contracts
# =====================================================================


class SingleTriggerEvaluation(BaseModel):
    """Granular audit record for an individual indicator evaluation."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    indicator: str
    observed_value: Optional[float] = None
    configured_threshold: Optional[float] = None
    operator: ComparisonOperator = ComparisonOperator.GREATER_THAN_OR_EQUAL
    triggered: bool = False
    status: DynamicTriggerStatus
    unit: Optional[str] = None
    audit_note: str = ""


class DynamicRedZoneExplainability(BaseModel):
    """Structured explainability and audit trail for a dynamic candidate evaluation."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    decision_reason: str = ""
    summary: str = ""
    profile_id: str = "himalayan_pilot"
    profile_name: str = ""
    trigger_evaluations: List[SingleTriggerEvaluation] = Field(default_factory=list)
    triggered_indicators: List[str] = Field(default_factory=list)
    missing_indicators: List[str] = Field(default_factory=list)
    source_observation_ids: List[str] = Field(default_factory=list)
    source_village_ids: List[str] = Field(default_factory=list)
    source_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    buffer_applied_m: Optional[float] = None
    is_dissolved: bool = False
    dissolved_count: int = 1
    governance_notice: str = (
        "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: This is an event-driven temporary exclusion candidate generated for "
        "operational decision support and early warning. It does NOT constitute a statutory disaster declaration or "
        "permanent property restriction. Official action requires verification and authorization by the competent "
        "disaster management authority (Chunk M6-08 workflow)."
    )


# =====================================================================
# Result & Output Envelopes
# =====================================================================


class DynamicRedZoneCandidate(BaseModel):
    """Authoritative result envelope for a dynamic / temporary red zone demarcation."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    candidate_id: str = ""
    zone_id: str = ""
    name: str = ""
    status: DynamicTriggerStatus
    zone_type: Optional[RedZoneType] = None
    danger_level: Optional[DangerLevel] = None
    geometry: Optional[Union[MultiPolygon, Dict[str, Any]]] = None
    srid: int = 4326
    area_sq_km: Optional[float] = None
    buffer_distance_applied_m: Optional[float] = None
    contributing_observation_ids: List[str] = Field(default_factory=list)
    contributing_village_ids: List[str] = Field(default_factory=list)
    is_temporary: bool = True  # Strict semantic separation: M3-11 is temporary, M3-10 is permanent
    is_candidate: bool = False
    is_active: bool = False  # Governance invariant: candidates are NEVER automatically active/declared
    declared_by_officer_id: Optional[int] = None  # Governance invariant: None for candidate output
    declared_at: Optional[datetime] = None  # Governance invariant: None for candidate output
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    explainability: DynamicRedZoneExplainability
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def harmonize_ids(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "candidate_id" not in values and "zone_id" in values:
                values["candidate_id"] = values["zone_id"]
            elif "zone_id" not in values and "candidate_id" in values:
                values["zone_id"] = values["candidate_id"]
        return values

    @model_validator(mode="after")
    def validate_invariants(self) -> "DynamicRedZoneCandidate":
        # Governance Invariant: candidate demarcation cannot claim official activation or officer sign-off
        if self.is_active:
            raise ValueError(
                "Dynamic candidate red zone cannot have is_active=True without officer declaration (must be False)."
            )
        if self.declared_by_officer_id is not None:
            raise ValueError(
                "Dynamic candidate red zone cannot have declared_by_officer_id set by scoring engine (must be None)."
            )
        if self.declared_at is not None:
            raise ValueError(
                "Dynamic candidate red zone cannot have declared_at set by scoring engine (must be None)."
            )

        # Status Invariants
        if self.status == DynamicTriggerStatus.TRIGGERED:
            if not self.is_candidate:
                raise ValueError("is_candidate must be True when status is TRIGGERED.")
            if self.danger_level is None:
                raise ValueError("danger_level cannot be None when status is TRIGGERED.")
            if self.zone_type is None:
                raise ValueError("zone_type cannot be None when status is TRIGGERED.")
            if self.geometry is not None:
                if isinstance(self.geometry, dict):
                    if self.geometry.get("type") != "MultiPolygon":
                        raise ValueError(f"geometry must be MultiPolygon, got {self.geometry.get('type')}.")
                elif hasattr(self.geometry, "geom_type"):
                    if self.geometry.geom_type != "MultiPolygon":
                        raise ValueError(f"geometry must be MultiPolygon, got {self.geometry.geom_type}.")
        else:
            if self.is_candidate:
                raise ValueError(f"is_candidate must be False when status is {self.status.value}.")
            if self.danger_level is not None:
                raise ValueError(
                    f"danger_level must be None when status is not TRIGGERED (got {self.danger_level})."
                )

        return self
