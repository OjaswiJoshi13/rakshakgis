"""Canonical Himalayan pilot region profile for RakshakGIS."""

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
    RelocationPriorityCutoffs,
    RelocationPriorityParameters,
    RelocationPriorityWeights,
    RiskScoreBands,
    ScenarioBounds,
    SiteCapacityAssumptions,
    UncertaintyNotes,
    VulnerabilityParameters,
    VulnerabilityWeights,
)

HIMALAYAN_PILOT_PROFILE = RegionProfile(
    metadata=ProfileMetadata(
        id=RegionProfileId.HIMALAYAN_PILOT,
        name="Himalayan Pilot Region Profile",
        description=(
            "High-altitude mountain terrain profile tailored for landslide, cloudburst, "
            "flash flood, and seismic multi-hazard assessment in Uttarakhand pilot districts (e.g. Chamoli)."
        ),
        region_type=RegionType.HIMALAYAN,
        is_pilot=True,
        pilot_label="Pilot / Demonstration Configuration (Uttarakhand Himalayan Belt)",
        methodology_notice=(
            "Demonstration / pilot configuration for SIH Problem Statement 26191. "
            "Not certified official government statutory thresholds."
        ),
        version="1.0.0",
        author="RakshakGIS Team M3",
    ),
    risk_weights=CompositeRiskWeights(
        hazard_weight=0.30,
        flood_weight=0.20,
        rainfall_weight=0.15,
        seismic_weight=0.15,
        demographic_weight=0.10,
        vulnerability_weight=0.10,
    ),
    risk_bands=RiskScoreBands(
        safe_max=25.0,
        moderate_max=50.0,
        high_max=70.0,
        very_high_max=85.0,
        critical_max=100.0,
    ),
    hazard_parameters=HazardParameters(
        weights=HazardWeights(
            landslide=0.45,
            rainfall=0.25,
            seismic=0.20,
            flood=0.10,
            coastal_storm_surge=0.0,
        ),
        thresholds=HazardThresholds(
            slope_warning_deg=25.0,
            slope_critical_deg=35.0,
            rainfall_heavy_24h_mm=64.5,
            rainfall_very_heavy_24h_mm=115.5,
            seismic_critical_mmi=7.0,
            glof_susceptibility_enabled=True,
        ),
    ),
    vulnerability_parameters=VulnerabilityParameters(
        component_weights=VulnerabilityWeights(
            social_weight=0.25,
            economic_weight=0.25,
            structural_weight=0.25,
            road_connectivity_weight=0.25,
        ),
        demographic_factors=DemographicVulnerabilityFactors(
            elderly_multiplier=1.25,
            children_multiplier=1.20,
            disabled_multiplier=1.50,
        ),
    ),
    red_zone_thresholds=RedZoneThresholds(
        permanent_criteria=PermanentRedZoneCriteria(
            min_slope_deg=35.0,
            min_historical_landslides=1,
            active_subsidence_triggers_permanent=True,
            default_danger_level=DangerLevel.UNINHABITABLE,
        ),
        dynamic_triggers=DynamicRedZoneTriggers(
            rainfall_trigger_24h_mm=64.5,
            seismic_trigger_mmi=6.0,
            slope_trigger_min_deg=25.0,
            default_danger_level=DangerLevel.VERY_HIGH,
        ),
    ),
    relocation_priority_parameters=RelocationPriorityParameters(
        cutoffs=RelocationPriorityCutoffs(
            monitor_max=39.99,
            medium_term_min=40.0,
            short_term_min=60.0,
            immediate_min=80.0,
        ),
        weights=RelocationPriorityWeights(
            risk_weight=0.40,
            exposure_weight=0.25,
            vulnerability_weight=0.20,
            historical_impact_weight=0.10,
            accessibility_weight=0.05,
        ),
    ),
    site_capacity_assumptions=SiteCapacityAssumptions(
        max_safe_slope_deg=15.0,
        hazard_buffer_m=500.0,
        water_supply_lpd_per_capita=70.0,
        land_area_sq_m_per_household=120.0,
        min_road_access_width_m=3.75,
    ),
    scenario_bounds=ScenarioBounds(
        min_rainfall_multiplier=0.5,
        max_rainfall_multiplier=3.0,
        default_rainfall_multiplier=1.5,
        min_seismic_intensity_mmi=3.0,
        max_seismic_intensity_mmi=9.0,
        max_road_blockage_percentage=100.0,
    ),
    uncertainty_notes=UncertaintyNotes(
        provisional_parameters=[
            "Dynamic Red Zone rainfall trigger of 64.5 mm/24h is provisional based on IMD heavy rainfall classification; local geological thresholds may vary by watershed.",
            "Seismic critical intensity MMI VII is provisional for Himalayan Zone IV/V building stock vulnerability.",
            "Relocation site slope threshold of 15.0 degrees is an engineering assumption for hill terrace stability.",
        ],
        data_gap_notes=[
            "Glacial Lake Outburst Flood (GLOF) volume and hydrograph data require watershed-specific bathymetry.",
            "Detailed structural masonry vs RCC vulnerability breakdown requires localized block-level surveys.",
        ],
        configuration_required=[
            "Watershed-specific discharge curve for Chamoli Alaknanda/Dhauliganga river reaches when available from CWC.",
        ],
    ),
)
