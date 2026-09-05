"""Data contracts, schemas, and result envelopes for Permanent Red Zone Demarcation (Chunk M3-10)."""

from datetime import datetime
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import MultiPolygon

from app.core.profiles.models import DangerLevel
from app.core.risk.classification.contracts import RiskBand
from app.core.risk.red_zone.errors import InvalidGeophysicalDataError
from app.data.providers.contracts import ProviderProvenance


# =====================================================================
# Status & Type Enums
# =====================================================================


class RedZoneStatus(str, Enum):
    """Evaluation status for a candidate Permanent Red Zone."""

    PROPOSED = "proposed"  # Meets criteria; proposed/candidate permanent red zone
    NOT_DEMARCATED = "not_demarcated"  # Evaluated; does not breach permanent criteria
    MONITOR = "monitor"  # Steep slope with Safe/Moderate composite risk without subsidence
    INSUFFICIENT_DATA = "insufficient_data"  # Missing required geophysical indicators


class RedZoneType(str, Enum):
    """Geophysical threat classification for demarcated perimeters."""

    LANDSLIDE_DANGER = "landslide_danger"
    ACTIVE_SUBSIDENCE = "active_subsidence"
    FLOOD_INUNDATION = "flood_inundation"
    COMPOUND_DANGER = "compound_danger"


# =====================================================================
# Input Contracts
# =====================================================================


class GeophysicalObservationInput(BaseModel):
    """Site-specific geophysical and hazard observations for red-zone evaluation."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    village_id: Optional[str] = None
    name: Optional[str] = None
    village_name: Optional[str] = None
    location: Optional[Union[Tuple[float, float], List[float], Dict[str, Any], Any]] = None  # (lon, lat) or Point
    location_geometry: Optional[Any] = None
    geometry: Optional[Any] = None  # Polygon, MultiPolygon, or GeoJSON dict
    slope_deg: Optional[float] = None
    historical_landslide_count: Optional[int] = None
    active_subsidence: Optional[bool] = None
    risk_score: Optional[float] = None
    risk_band: Optional[Union[RiskBand, str]] = None
    upstream_risk_band: Optional[Union[RiskBand, str]] = None
    is_available: bool = True
    provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None

    @model_validator(mode="before")
    @classmethod
    def harmonize_synonyms(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # village_name -> name
            if "name" not in values and "village_name" in values:
                values["name"] = values["village_name"]
            elif "village_name" not in values and "name" in values:
                values["village_name"] = values["name"]

            # location_geometry -> geometry or location
            if "location_geometry" in values and values["location_geometry"] is not None:
                loc_geom = values["location_geometry"]
                if hasattr(loc_geom, "geom_type") and loc_geom.geom_type == "Point":
                    if "location" not in values or values["location"] is None:
                        values["location"] = loc_geom
                else:
                    if "geometry" not in values or values["geometry"] is None:
                        values["geometry"] = loc_geom

            # upstream_risk_band -> risk_band
            if "risk_band" not in values and "upstream_risk_band" in values:
                values["risk_band"] = values["upstream_risk_band"]
            elif "upstream_risk_band" not in values and "risk_band" in values:
                values["upstream_risk_band"] = values["risk_band"]

        return values

    @model_validator(mode="after")
    def validate_geophysical_inputs(self) -> "GeophysicalObservationInput":
        if self.slope_deg is not None:
            if math.isnan(self.slope_deg) or math.isinf(self.slope_deg):
                raise InvalidGeophysicalDataError("slope_deg cannot be NaN or infinite.")
            if not (0.0 <= self.slope_deg <= 90.0):
                raise InvalidGeophysicalDataError(
                    f"slope_deg must be within [0.0, 90.0] degrees, got {self.slope_deg}."
                )

        if self.historical_landslide_count is not None:
            if self.historical_landslide_count < 0:
                raise InvalidGeophysicalDataError(
                    f"historical_landslide_count cannot be negative, got {self.historical_landslide_count}."
                )

        if self.risk_score is not None:
            if math.isnan(self.risk_score) or math.isinf(self.risk_score):
                raise InvalidGeophysicalDataError("risk_score cannot be NaN or infinite.")
            if not (0.0 <= self.risk_score <= 100.0):
                raise InvalidGeophysicalDataError(
                    f"risk_score must be within [0.0, 100.0], got {self.risk_score}."
                )

        return self


# =====================================================================
# Explainability & Audit Trail Contracts
# =====================================================================


class TriggerAudit(BaseModel):
    """Granular audit record of evaluated geophysical conditions and thresholds."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    village_id: Optional[str] = None
    active_subsidence_triggered: bool = False
    compound_landslide_triggered: bool = False
    compound_hazard_triggered: bool = False
    slope_threshold_deg: float = 35.0
    observed_slope_deg: Optional[float] = None
    slope_threshold_met: bool = False
    landslide_threshold_count: int = 1
    observed_landslide_count: Optional[int] = None
    historical_landslides_threshold_met: bool = False
    active_subsidence_observed: Optional[bool] = None
    risk_corroboration: Optional[str] = None
    risk_band_corroborated: bool = False
    missing_indicators: List[str] = Field(default_factory=list)


class PermanentRedZoneExplainability(BaseModel):
    """Detailed audit trail and governance metadata for a demarcated candidate zone."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    decision_reason: str = ""
    trigger_summary: str = ""
    trigger_audit: Optional[TriggerAudit] = None
    trigger_audits: List[TriggerAudit] = Field(default_factory=list)
    active_subsidence_triggered: bool = False
    compound_hazard_triggered: bool = False
    slope_threshold_met: bool = False
    historical_landslides_threshold_met: bool = False
    risk_band_corroborated: bool = False
    monitoring_recommended: bool = False
    missing_required_indicators: List[str] = Field(default_factory=list)
    source_village_ids: List[str] = Field(default_factory=list)
    source_village_provenance: Dict[str, Any] = Field(default_factory=dict)
    source_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    is_dissolved: bool = False
    dissolved_zone_count: int = 1
    profile_id: str = "himalayan_pilot"
    buffer_applied_m: Optional[float] = None
    governance_notice: str = (
        "PROPOSED/CANDIDATE ONLY: This is an analytical demarcation candidate generated for decision support. "
        "It does NOT constitute an official statutory disaster zone, legal property restriction, or evacuation order. "
        "Official declaration requires review and authorization by the competent disaster management officer (M6-08 workflow)."
    )


# =====================================================================
# Result & Output Envelopes
# =====================================================================


class PermanentRedZoneCandidate(BaseModel):
    """Authoritative result envelope for a candidate Permanent Red Zone demarcation."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    candidate_id: str = ""
    zone_id: str = ""
    name: str = ""
    status: RedZoneStatus
    zone_type: Optional[RedZoneType] = None
    danger_level: Optional[DangerLevel] = None
    geometry: Optional[Union[MultiPolygon, Dict[str, Any]]] = None
    srid: int = 4326
    area_sq_km: Optional[float] = None
    buffer_distance_applied_m: Optional[float] = None
    contributing_village_ids: List[str] = Field(default_factory=list)
    is_candidate: bool = False
    is_active: bool = False  # Governance invariant: candidates are NEVER automatically active/declared
    declared_by_officer_id: Optional[int] = None  # Governance invariant: None for candidate output
    declared_at: Optional[datetime] = None  # Governance invariant: None for candidate output
    explainability: PermanentRedZoneExplainability
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
    def validate_invariants(self) -> "PermanentRedZoneCandidate":
        # Governance Invariant: candidate demarcation output cannot claim official activation or officer sign-off
        if self.is_active:
            raise ValueError("Candidate permanent red zone cannot have is_active=True without officer declaration (must be False for candidate zones).")
        if self.declared_by_officer_id is not None:
            raise ValueError("Candidate permanent red zone cannot have declared_by_officer_id set by scoring engine (declared_by_officer_id must be None).")
        if self.declared_at is not None:
            raise ValueError("Candidate permanent red zone cannot have declared_at set by scoring engine (declared_at must be None).")

        # Candidate Status Invariants
        if self.status == RedZoneStatus.PROPOSED:
            if not self.is_candidate:
                raise ValueError("is_candidate must be True when status is PROPOSED.")
            if self.geometry is None:
                raise ValueError("geometry cannot be None when candidate is PROPOSED.")
            if isinstance(self.geometry, dict):
                if self.geometry.get("type") != "MultiPolygon":
                    raise ValueError(f"geometry must be MultiPolygon, got {self.geometry.get('type')}.")
            elif hasattr(self.geometry, "geom_type"):
                if self.geometry.geom_type != "MultiPolygon":
                    raise ValueError(f"geometry must be MultiPolygon, got {self.geometry.geom_type}.")
            if self.danger_level is None:
                raise ValueError("danger_level cannot be None when candidate is PROPOSED.")
            if self.zone_type is None:
                raise ValueError("zone_type cannot be None when candidate is PROPOSED.")
        else:
            if self.is_candidate:
                raise ValueError(f"is_candidate must be False when status is {self.status.value}.")

        return self
