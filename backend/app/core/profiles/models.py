"""Strongly typed region profile schemas and enumerations for RakshakGIS."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RegionProfileId(str, Enum):
    """Stable identifiers for registered region profiles."""

    HIMALAYAN_PILOT = "himalayan_pilot"
    RIVERINE_TEMPLATE = "riverine_template"
    COASTAL_TEMPLATE = "coastal_template"


class RegionType(str, Enum):
    """Broad geographic typology for multi-hazard adaptation."""

    HIMALAYAN = "himalayan"
    RIVERINE = "riverine"
    COASTAL = "coastal"


class DangerLevel(str, Enum):
    """Red Zone danger categorization matching domain specifications."""

    VERY_HIGH = "very_high"
    CRITICAL = "critical"
    UNINHABITABLE = "uninhabitable"


class RelocationPriorityBand(str, Enum):
    """Village relocation urgency bands matching domain specification.

    Bands:
    - IMMEDIATE: 80–100
    - SHORT_TERM: 60–79
    - MEDIUM_TERM: 40–59
    - MONITOR: <40
    """

    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    MONITOR = "monitor"


class RiskBand(str, Enum):
    """Multi-hazard composite risk bands matching domain specification.

    Bands:
    - SAFE: 0–25
    - MODERATE: 25–50
    - HIGH: 50–70
    - VERY_HIGH: 70–85
    - CRITICAL: 85–100
    """

    SAFE = "safe"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class ProfileBaseModel(BaseModel):
    """Immutable base model preventing accidental mutation of profile state."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ProfileMetadata(ProfileBaseModel):
    """Metadata and provenance information for a regional profile."""

    id: RegionProfileId
    name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1)
    region_type: RegionType
    is_pilot: bool = False
    pilot_label: Optional[str] = None
    methodology_notice: str = Field(..., min_length=1)
    version: str = "1.0.0"
    author: Optional[str] = None


class CompositeRiskWeights(ProfileBaseModel):
    """Weights for the composite risk formula:
    Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V
    where:
      H = Hazard (Landslide / slope instability)
      F = Flood factor
      R = Rainfall factor
      S = Seismic factor
      D = Demographic / Exposure factor
      V = Vulnerability factor
    All weights must sum to 1.0.
    """

    hazard_weight: float = Field(default=0.30, ge=0.0, le=1.0)        # H
    flood_weight: float = Field(default=0.20, ge=0.0, le=1.0)         # F
    rainfall_weight: float = Field(default=0.15, ge=0.0, le=1.0)      # R
    seismic_weight: float = Field(default=0.15, ge=0.0, le=1.0)       # S
    demographic_weight: float = Field(default=0.10, ge=0.0, le=1.0)   # D
    vulnerability_weight: float = Field(default=0.10, ge=0.0, le=1.0) # V

    @property
    def w_h(self) -> float:
        return self.hazard_weight

    @property
    def w_f(self) -> float:
        return self.flood_weight

    @property
    def w_r(self) -> float:
        return self.rainfall_weight

    @property
    def w_s(self) -> float:
        return self.seismic_weight

    @property
    def w_d(self) -> float:
        return self.demographic_weight

    @property
    def w_v(self) -> float:
        return self.vulnerability_weight


# Backward-compatibility alias
MultiHazardRiskWeights = CompositeRiskWeights


class RiskScoreBands(ProfileBaseModel):
    """Threshold cutoffs for classifying 0-100 composite risk scores.

    Specification-defined cutoffs:
    - SAFE: 0 to 25
    - MODERATE: 25 to 50
    - HIGH: 50 to 70
    - VERY HIGH: 70 to 85
    - CRITICAL: 85 to 100
    """

    safe_max: float = Field(default=25.0, ge=0.0, le=100.0)
    moderate_max: float = Field(default=50.0, ge=0.0, le=100.0)
    high_max: float = Field(default=70.0, ge=0.0, le=100.0)
    very_high_max: float = Field(default=85.0, ge=0.0, le=100.0)
    critical_max: float = Field(default=100.0, ge=0.0, le=100.0)


class HazardWeights(ProfileBaseModel):
    """Relative importance weights across hazard types."""

    landslide: float = Field(default=0.0, ge=0.0, le=1.0)
    flood: float = Field(default=0.0, ge=0.0, le=1.0)
    rainfall: float = Field(default=0.0, ge=0.0, le=1.0)
    seismic: float = Field(default=0.0, ge=0.0, le=1.0)
    coastal_storm_surge: float = Field(default=0.0, ge=0.0, le=1.0)


class HazardThresholds(ProfileBaseModel):
    """Geophysical and meteorological trigger thresholds for hazards."""

    slope_warning_deg: float = Field(..., ge=0.0, le=90.0)
    slope_critical_deg: float = Field(..., ge=0.0, le=90.0)
    rainfall_heavy_24h_mm: float = Field(..., ge=0.0)
    rainfall_very_heavy_24h_mm: float = Field(..., ge=0.0)
    seismic_critical_mmi: Optional[float] = Field(default=None, ge=1.0, le=12.0)
    glof_susceptibility_enabled: bool = False


class HazardParameters(ProfileBaseModel):
    """Regional hazard parameters, weights, and triggers."""

    weights: HazardWeights
    thresholds: HazardThresholds


class VulnerabilityWeights(ProfileBaseModel):
    """Relative weights for vulnerability components (social, economic, structural, access)."""

    social_weight: float = Field(..., ge=0.0, le=1.0)
    economic_weight: float = Field(..., ge=0.0, le=1.0)
    structural_weight: float = Field(..., ge=0.0, le=1.0)
    road_connectivity_weight: float = Field(..., ge=0.0, le=1.0)


class DemographicVulnerabilityFactors(ProfileBaseModel):
    """Multipliers applied to high-risk demographic populations."""

    elderly_multiplier: float = Field(default=1.2, ge=1.0)
    children_multiplier: float = Field(default=1.2, ge=1.0)
    disabled_multiplier: float = Field(default=1.5, ge=1.0)


class VulnerabilityParameters(ProfileBaseModel):
    """Regional vulnerability parameters, weights, and multipliers."""

    component_weights: VulnerabilityWeights
    demographic_factors: DemographicVulnerabilityFactors = Field(
        default_factory=DemographicVulnerabilityFactors
    )


class PermanentRedZoneCriteria(ProfileBaseModel):
    """Criteria defining permanently uninhabitable or extreme danger zones."""

    min_slope_deg: float = Field(..., ge=0.0, le=90.0)
    min_historical_landslides: int = Field(default=1, ge=0)
    active_subsidence_triggers_permanent: bool = True
    default_danger_level: DangerLevel = DangerLevel.UNINHABITABLE


class DynamicRedZoneTriggers(ProfileBaseModel):
    """Real-time sensor and weather trigger criteria for dynamic exclusion zones."""

    rainfall_trigger_24h_mm: float = Field(..., ge=0.0)
    seismic_trigger_mmi: Optional[float] = Field(default=None, ge=1.0, le=12.0)
    slope_trigger_min_deg: float = Field(..., ge=0.0, le=90.0)
    default_danger_level: DangerLevel = DangerLevel.VERY_HIGH


class RedZoneThresholds(ProfileBaseModel):
    """Thresholds governing permanent and dynamic Red Zone demarcation."""

    permanent_criteria: PermanentRedZoneCriteria
    dynamic_triggers: DynamicRedZoneTriggers


class RelocationPriorityCutoffs(ProfileBaseModel):
    """Score thresholds defining relocation priority bands.

    Specification-defined cutoffs:
    - IMMEDIATE: 80–100
    - SHORT-TERM: 60–79
    - MEDIUM-TERM: 40–59
    - MONITOR: <40
    """

    monitor_max: float = Field(default=39.99, ge=0.0, le=100.0)
    medium_term_min: float = Field(default=40.0, ge=0.0, le=100.0)
    short_term_min: float = Field(default=60.0, ge=0.0, le=100.0)
    immediate_min: float = Field(default=80.0, ge=0.0, le=100.0)


class RelocationPriorityWeights(ProfileBaseModel):
    """Weights for the relocation priority formula:
    Priority = 0.40*Risk + 0.25*Exposure + 0.20*Vulnerability + 0.10*HistoricalImpact + 0.05*Accessibility
    All weights must sum to 1.0.
    """

    risk_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    exposure_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    vulnerability_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    historical_impact_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    accessibility_weight: float = Field(default=0.05, ge=0.0, le=1.0)


class RelocationPriorityParameters(ProfileBaseModel):
    """Scoring parameters and urgency cutoffs for relocation prioritization."""

    cutoffs: RelocationPriorityCutoffs = Field(default_factory=RelocationPriorityCutoffs)
    weights: RelocationPriorityWeights = Field(default_factory=RelocationPriorityWeights)

    @property
    def risk_weight(self) -> float:
        return self.weights.risk_weight

    @property
    def exposure_weight(self) -> float:
        return self.weights.exposure_weight

    @property
    def vulnerability_weight(self) -> float:
        return self.weights.vulnerability_weight

    @property
    def historical_impact_weight(self) -> float:
        return self.weights.historical_impact_weight

    @property
    def accessibility_weight(self) -> float:
        return self.weights.accessibility_weight


class SiteCapacityAssumptions(ProfileBaseModel):
    """Regional engineering and resource assumptions for candidate relocation sites."""

    max_safe_slope_deg: float = Field(..., ge=0.0, le=90.0)
    hazard_buffer_m: float = Field(..., ge=0.0)
    water_supply_lpd_per_capita: float = Field(default=70.0, ge=0.0)
    land_area_sq_m_per_household: float = Field(default=100.0, ge=0.0)
    min_road_access_width_m: Optional[float] = Field(default=3.5, ge=0.0)


class ScenarioBounds(ProfileBaseModel):
    """Realistic bounds and defaults for what-if scenario simulations in this region."""

    min_rainfall_multiplier: float = Field(default=0.5, ge=0.0)
    max_rainfall_multiplier: float = Field(default=3.0, ge=0.0)
    default_rainfall_multiplier: float = Field(default=1.0, ge=0.0)
    min_seismic_intensity_mmi: float = Field(default=1.0, ge=1.0, le=12.0)
    max_seismic_intensity_mmi: float = Field(default=10.0, ge=1.0, le=12.0)
    max_road_blockage_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    flood_prone_corridor_segments: List[str] = Field(
        default_factory=list,
        description="Region-specific road segment IDs vulnerable to flash flooding or valley inundation.",
    )


class UncertaintyNotes(ProfileBaseModel):
    """Explicit tracking of provisional, unknown, or configuration-required parameters."""

    provisional_parameters: List[str] = Field(default_factory=list)
    data_gap_notes: List[str] = Field(default_factory=list)
    configuration_required: List[str] = Field(default_factory=list)


class RegionProfile(ProfileBaseModel):
    """Complete strongly typed and immutable regional profile container."""

    metadata: ProfileMetadata
    risk_weights: CompositeRiskWeights = Field(default_factory=CompositeRiskWeights)
    risk_bands: RiskScoreBands = Field(default_factory=RiskScoreBands)
    hazard_parameters: HazardParameters
    vulnerability_parameters: VulnerabilityParameters
    red_zone_thresholds: RedZoneThresholds
    relocation_priority_parameters: RelocationPriorityParameters = Field(
        default_factory=RelocationPriorityParameters
    )
    site_capacity_assumptions: SiteCapacityAssumptions
    scenario_bounds: ScenarioBounds = Field(default_factory=ScenarioBounds)
    uncertainty_notes: UncertaintyNotes = Field(default_factory=UncertaintyNotes)

    @property
    def id(self) -> str:
        """Convenience property for profile identifier string."""
        return self.metadata.id.value

    @property
    def name(self) -> str:
        """Convenience property for profile human-readable name."""
        return self.metadata.name

    @property
    def is_pilot(self) -> bool:
        """Indicate whether this profile is a pilot / demonstration configuration."""
        return self.metadata.is_pilot

    @property
    def region_type(self) -> RegionType:
        """Geographic region typology."""
        return self.metadata.region_type
