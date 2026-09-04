"""Regional profiles configuration package for RakshakGIS.

Exports strongly typed domain models, deterministic validation engine,
canonical profiles (Himalayan pilot, Riverine template, Coastal template),
and the profile registry / resolver.
"""

from app.core.profiles.coastal import COASTAL_TEMPLATE_PROFILE
from app.core.profiles.himalayan import HIMALAYAN_PILOT_PROFILE
from app.core.profiles.models import (
    CompositeRiskWeights,
    DangerLevel,
    DemographicVulnerabilityFactors,
    DynamicRedZoneTriggers,
    HazardParameters,
    HazardThresholds,
    HazardWeights,
    MultiHazardRiskWeights,
    PermanentRedZoneCriteria,
    ProfileMetadata,
    RedZoneThresholds,
    RegionProfile,
    RegionProfileId,
    RegionType,
    RelocationPriorityBand,
    RelocationPriorityCutoffs,
    RelocationPriorityParameters,
    RelocationPriorityWeights,
    RiskBand,
    RiskScoreBands,
    ScenarioBounds,
    SiteCapacityAssumptions,
    UncertaintyNotes,
    VulnerabilityParameters,
    VulnerabilityWeights,
)
from app.core.profiles.registry import (
    RegionProfileRegistry,
    UnknownRegionProfileError,
    get_profile,
    list_profile_ids,
    list_profiles,
    register_profile,
)
from app.core.profiles.riverine import RIVERINE_TEMPLATE_PROFILE
from app.core.profiles.validation import ProfileValidationError, validate_profile

__all__ = [
    # Core Enums
    "RegionProfileId",
    "RegionType",
    "DangerLevel",
    "RelocationPriorityBand",
    "RiskBand",
    # Sub-models
    "ProfileMetadata",
    "CompositeRiskWeights",
    "MultiHazardRiskWeights",
    "RiskScoreBands",
    "HazardWeights",
    "HazardThresholds",
    "HazardParameters",
    "VulnerabilityWeights",
    "DemographicVulnerabilityFactors",
    "VulnerabilityParameters",
    "PermanentRedZoneCriteria",
    "DynamicRedZoneTriggers",
    "RedZoneThresholds",
    "RelocationPriorityCutoffs",
    "RelocationPriorityWeights",
    "RelocationPriorityParameters",
    "SiteCapacityAssumptions",
    "ScenarioBounds",
    "UncertaintyNotes",
    # Root Profile
    "RegionProfile",
    # Canonical Profiles
    "HIMALAYAN_PILOT_PROFILE",
    "RIVERINE_TEMPLATE_PROFILE",
    "COASTAL_TEMPLATE_PROFILE",
    # Validation
    "validate_profile",
    "ProfileValidationError",
    # Registry & Resolver
    "RegionProfileRegistry",
    "UnknownRegionProfileError",
    "get_profile",
    "list_profiles",
    "list_profile_ids",
    "register_profile",
]
