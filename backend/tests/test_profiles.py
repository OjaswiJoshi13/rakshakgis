"""Automated test suite for RakshakGIS Region Profiles Configuration (Chunk M3-01)."""

import pytest
from pydantic import ValidationError

from app.core.profiles import (
    COASTAL_TEMPLATE_PROFILE,
    HIMALAYAN_PILOT_PROFILE,
    RIVERINE_TEMPLATE_PROFILE,
    CompositeRiskWeights,
    DangerLevel,
    HazardParameters,
    HazardThresholds,
    HazardWeights,
    MultiHazardRiskWeights,
    PermanentRedZoneCriteria,
    ProfileMetadata,
    ProfileValidationError,
    RedZoneThresholds,
    RegionProfile,
    RegionProfileId,
    RegionProfileRegistry,
    RegionType,
    RelocationPriorityBand,
    RelocationPriorityCutoffs,
    RelocationPriorityParameters,
    RelocationPriorityWeights,
    RiskBand,
    RiskScoreBands,
    ScenarioBounds,
    SiteCapacityAssumptions,
    UnknownRegionProfileError,
    UncertaintyNotes,
    VulnerabilityParameters,
    VulnerabilityWeights,
    get_profile,
    list_profile_ids,
    list_profiles,
    register_profile,
    validate_profile,
)


def test_himalayan_profile_loads_successfully():
    """Requirement 1: Himalayan profile loads successfully and contains expected structure."""
    profile = HIMALAYAN_PILOT_PROFILE
    assert profile is not None
    assert profile.metadata.id == RegionProfileId.HIMALAYAN_PILOT
    assert profile.metadata.name == "Himalayan Pilot Region Profile"
    assert profile.metadata.region_type == RegionType.HIMALAYAN
    assert profile.metadata.is_pilot is True
    assert profile.metadata.pilot_label is not None
    assert "Pilot / Demonstration" in profile.metadata.pilot_label
    assert profile.is_pilot is True
    assert profile.id == "himalayan_pilot"


def test_profile_identifier_is_stable_and_deterministic():
    """Requirement 2: Profile identifier is stable, deterministic, and typed."""
    assert RegionProfileId.HIMALAYAN_PILOT.value == "himalayan_pilot"
    assert RegionProfileId.RIVERINE_TEMPLATE.value == "riverine_template"
    assert RegionProfileId.COASTAL_TEMPLATE.value == "coastal_template"

    profile = get_profile(RegionProfileId.HIMALAYAN_PILOT)
    assert profile.id == "himalayan_pilot"


def test_registry_can_enumerate_profiles():
    """Requirement 3: Registry can enumerate profiles deterministically."""
    ids = list_profile_ids()
    assert isinstance(ids, list)
    assert len(ids) >= 3
    assert ids == sorted(ids)  # Deterministic ascending order
    assert "himalayan_pilot" in ids
    assert "riverine_template" in ids
    assert "coastal_template" in ids

    profiles = list_profiles()
    assert len(profiles) == len(ids)
    assert [p.id for p in profiles] == ids


def test_registry_can_resolve_himalayan_profile():
    """Requirement 4: Registry can resolve the Himalayan profile by enum and string."""
    # Resolve by Enum
    profile_from_enum = get_profile(RegionProfileId.HIMALAYAN_PILOT)
    assert profile_from_enum.id == "himalayan_pilot"

    # Resolve by exact string
    profile_from_str = get_profile("himalayan_pilot")
    assert profile_from_str.id == "himalayan_pilot"

    # Resolve case-insensitively with leading/trailing whitespace
    profile_from_case = get_profile("  HIMALAYAN_PILOT  ")
    assert profile_from_case.id == "himalayan_pilot"


def test_unknown_profile_produces_clean_error():
    """Requirement 5: Unknown profile produces a clean, structured domain error."""
    with pytest.raises(UnknownRegionProfileError) as exc_info:
        get_profile("non_existent_desert_profile")

    err = exc_info.value
    assert err.status_code == 404
    assert err.code == "UNKNOWN_REGION_PROFILE"
    assert "non_existent_desert_profile" in err.message
    assert "Available profiles" in err.message
    assert err.details["requested_profile"] == "non_existent_desert_profile"


def test_configuration_validation_rejects_malformed_profiles():
    """Requirement 6: Configuration validation rejects malformed profiles across multiple invariants."""
    # 6a: Multi-hazard composite risk weights sum != 1.0
    with pytest.raises(ProfileValidationError) as exc:
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(
            update={"risk_weights": CompositeRiskWeights(hazard_weight=0.5, flood_weight=0.5, rainfall_weight=0.5)}
        )
        validate_profile(bad_profile)
    assert "Multi-hazard composite risk weights must sum to 1.0" in str(exc.value)

    # 6b: Risk bands ordering violated (safe > moderate)
    with pytest.raises(ProfileValidationError) as exc:
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(
            update={"risk_bands": RiskScoreBands(safe_max=60.0, moderate_max=50.0, high_max=70.0, very_high_max=85.0, critical_max=100.0)}
        )
        validate_profile(bad_profile)
    assert "Risk score bands must be strictly ascending" in str(exc.value)

    # 6c: Hazard weights sum != 1.0
    with pytest.raises(ProfileValidationError) as exc:
        bad_hw = HazardParameters(
            weights=HazardWeights(landslide=0.8, flood=0.8),
            thresholds=HIMALAYAN_PILOT_PROFILE.hazard_parameters.thresholds,
        )
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(update={"hazard_parameters": bad_hw})
        validate_profile(bad_profile)
    assert "Hazard weights must sum to 1.0" in str(exc.value)

    # 6d: Inverted slope threshold (warning >= critical)
    with pytest.raises(ProfileValidationError) as exc:
        bad_ht = HazardParameters(
            weights=HIMALAYAN_PILOT_PROFILE.hazard_parameters.weights,
            thresholds=HazardThresholds(
                slope_warning_deg=40.0,
                slope_critical_deg=30.0,
                rainfall_heavy_24h_mm=64.5,
                rainfall_very_heavy_24h_mm=115.5,
            ),
        )
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(update={"hazard_parameters": bad_ht})
        validate_profile(bad_profile)
    assert "slope warning threshold (40.0°) must be less than critical slope threshold (30.0°)" in str(exc.value)

    # 6e: Relocation safe slope > hazard slope warning threshold
    with pytest.raises(ProfileValidationError) as exc:
        bad_sc = HIMALAYAN_PILOT_PROFILE.site_capacity_assumptions.model_copy(
            update={"max_safe_slope_deg": 30.0}  # slope_warning_deg is 25.0
        )
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(update={"site_capacity_assumptions": bad_sc})
        validate_profile(bad_profile)
    assert "safe slope limit (30.0°) cannot exceed regional hazard slope warning threshold (25.0°)" in str(exc.value)

    # 6f: Missing pilot label on pilot profile
    with pytest.raises(ProfileValidationError) as exc:
        bad_meta = HIMALAYAN_PILOT_PROFILE.metadata.model_copy(update={"pilot_label": None})
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(update={"metadata": bad_meta})
        validate_profile(bad_profile)
    assert "Pilot profiles must have an explicit 'pilot_label'" in str(exc.value)

    # 6g: Relocation priority factor weights sum != 1.0
    with pytest.raises(ProfileValidationError) as exc:
        bad_rp = RelocationPriorityParameters(
            cutoffs=HIMALAYAN_PILOT_PROFILE.relocation_priority_parameters.cutoffs,
            weights=RelocationPriorityWeights(risk_weight=0.8, exposure_weight=0.5, vulnerability_weight=0.2, historical_impact_weight=0.1, accessibility_weight=0.05),
        )
        bad_profile = HIMALAYAN_PILOT_PROFILE.model_copy(update={"relocation_priority_parameters": bad_rp})
        validate_profile(bad_profile)
    assert "Relocation priority factor weights must sum to 1.0" in str(exc.value)


def test_valid_profiles_pass_validation():
    """Requirement 7: Valid canonical profiles pass deterministic validation cleanly."""
    validate_profile(HIMALAYAN_PILOT_PROFILE)
    validate_profile(RIVERINE_TEMPLATE_PROFILE)
    validate_profile(COASTAL_TEMPLATE_PROFILE)


def test_no_accidental_mutation_of_canonical_profile():
    """Requirement 8: Canonical profiles are immutable and protected against accidental mutation."""
    profile = get_profile(RegionProfileId.HIMALAYAN_PILOT)

    # Direct attribute mutation must raise ValidationError due to frozen=True
    with pytest.raises(ValidationError):
        profile.metadata.name = "Mutated Name"

    with pytest.raises(ValidationError):
        profile.risk_weights.hazard_weight = 0.99

    with pytest.raises(ValidationError):
        profile.site_capacity_assumptions.water_supply_lpd_per_capita = 999.0

    # Ensure canonical profile in registry remains unaltered
    fresh_profile = get_profile(RegionProfileId.HIMALAYAN_PILOT)
    assert fresh_profile.metadata.name == "Himalayan Pilot Region Profile"
    assert fresh_profile.risk_weights.hazard_weight == 0.30
    assert fresh_profile.site_capacity_assumptions.water_supply_lpd_per_capita == 70.0


def test_regional_configuration_is_separate_from_reusable_logic():
    """Requirement 9: Core computational logic consumes profile abstraction without region string checks."""

    # Reusable multi-hazard risk formula simulator consuming RegionProfile abstraction
    def compute_mock_composite_risk(
        profile: RegionProfile, h: float, f: float, r: float, s: float, d: float, v: float
    ) -> float:
        # Zero 'if region == "himalayan"' string conditionals
        weights = profile.risk_weights
        score = (
            weights.hazard_weight * h
            + weights.flood_weight * f
            + weights.rainfall_weight * r
            + weights.seismic_weight * s
            + weights.demographic_weight * d
            + weights.vulnerability_weight * v
        )
        return round(score, 2)

    # Specification 6-factor formula: 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V
    # Inputs: H=80, F=60, R=70, S=50, D=40, V=30
    score = compute_mock_composite_risk(
        HIMALAYAN_PILOT_PROFILE, 80.0, 60.0, 70.0, 50.0, 40.0, 30.0
    )
    # 0.30*80 + 0.20*60 + 0.15*70 + 0.15*50 + 0.10*40 + 0.10*30 = 24 + 12 + 10.5 + 7.5 + 4 + 3 = 61.0
    assert score == 61.0


def test_exact_specification_defined_constants():
    """Requirement 10: Specific constants from specification match exactly."""
    profile = HIMALAYAN_PILOT_PROFILE

    # 1. Risk score bands (0-25 Safe, 25-50 Moderate, 50-70 High, 70-85 Very High, 85-100 Critical)
    assert profile.risk_bands.safe_max == 25.0
    assert profile.risk_bands.moderate_max == 50.0
    assert profile.risk_bands.high_max == 70.0
    assert profile.risk_bands.very_high_max == 85.0
    assert profile.risk_bands.critical_max == 100.0

    # 2. Composite risk formula weights (0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V)
    assert profile.risk_weights.hazard_weight == 0.30
    assert profile.risk_weights.flood_weight == 0.20
    assert profile.risk_weights.rainfall_weight == 0.15
    assert profile.risk_weights.seismic_weight == 0.15
    assert profile.risk_weights.demographic_weight == 0.10
    assert profile.risk_weights.vulnerability_weight == 0.10

    # 3. Relocation priority formula weights (0.40 Risk + 0.25 Exp + 0.20 Vuln + 0.10 Hist + 0.05 Acc)
    rp_weights = profile.relocation_priority_parameters.weights
    assert rp_weights.risk_weight == 0.40
    assert rp_weights.exposure_weight == 0.25
    assert rp_weights.vulnerability_weight == 0.20
    assert rp_weights.historical_impact_weight == 0.10
    assert rp_weights.accessibility_weight == 0.05

    # 4. Relocation priority cutoffs (<40 Monitor, 40-59 Medium-Term, 60-79 Short-Term, 80-100 Immediate)
    rp_cutoffs = profile.relocation_priority_parameters.cutoffs
    assert rp_cutoffs.immediate_min == 80.0
    assert rp_cutoffs.short_term_min == 60.0
    assert rp_cutoffs.medium_term_min == 40.0
    assert rp_cutoffs.monitor_max == 39.99

    # 5. Slope thresholds
    assert profile.hazard_parameters.thresholds.slope_warning_deg == 25.0
    assert profile.hazard_parameters.thresholds.slope_critical_deg == 35.0

    # 6. Rainfall IMD classification thresholds
    assert profile.hazard_parameters.thresholds.rainfall_heavy_24h_mm == 64.5
    assert profile.hazard_parameters.thresholds.rainfall_very_heavy_24h_mm == 115.5

    # 7. Safe relocation site maximum slope limit
    assert profile.site_capacity_assumptions.max_safe_slope_deg == 15.0

    # 8. Standard rural hill water supply requirement
    assert profile.site_capacity_assumptions.water_supply_lpd_per_capita == 70.0

    # 9. Pilot labeling and non-official methodology disclaimer
    assert profile.is_pilot is True
    assert "Not certified official government statutory thresholds" in profile.metadata.methodology_notice
    assert "Pilot / Demonstration" in profile.metadata.pilot_label


def test_custom_registry_instance_isolation():
    """Verify that custom registry instances can be created without affecting global registry."""
    custom_registry = RegionProfileRegistry(load_defaults=False)
    assert custom_registry.count() == 0
    assert custom_registry.list_profile_ids() == []

    # Register only Himalayan profile
    custom_registry.register(HIMALAYAN_PILOT_PROFILE)
    assert custom_registry.count() == 1
    assert custom_registry.has_profile("himalayan_pilot") is True
    assert custom_registry.has_profile("riverine_template") is False

    # Global registry remains untouched
    assert len(list_profile_ids()) >= 3
