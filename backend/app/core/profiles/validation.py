"""Deterministic configuration validation for RakshakGIS regional profiles."""

import math
from typing import List

from app.core.profiles.models import RegionProfile

WEIGHT_TOLERANCE = 1e-4


class ProfileValidationError(ValueError):
    """Raised when a region profile fails deterministic consistency validation."""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]

    def __str__(self) -> str:
        if self.errors:
            return f"{self.message}: {'; '.join(self.errors)}"
        return self.message


def validate_profile(profile: RegionProfile) -> None:
    """Deterministically validate a region profile against mathematical and physical invariants.

    Raises:
        ProfileValidationError: If any consistency, range, weight, or ordering constraint is violated.
    """
    errors: List[str] = []

    # 1. Metadata Validation
    if not profile.metadata.name.strip():
        errors.append("Profile metadata 'name' cannot be empty or whitespace.")
    if not profile.metadata.methodology_notice.strip():
        errors.append("Profile metadata 'methodology_notice' cannot be empty or whitespace.")
    if profile.metadata.is_pilot and not profile.metadata.pilot_label:
        errors.append("Pilot profiles must have an explicit 'pilot_label' identifying demonstration status.")

    # 2. Multi-Hazard Composite Risk Weights (0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V)
    risk_w = profile.risk_weights
    risk_sum = (
        risk_w.hazard_weight
        + risk_w.flood_weight
        + risk_w.rainfall_weight
        + risk_w.seismic_weight
        + risk_w.demographic_weight
        + risk_w.vulnerability_weight
    )
    if not math.isclose(risk_sum, 1.0, abs_tol=WEIGHT_TOLERANCE):
        errors.append(
            f"Multi-hazard composite risk weights must sum to 1.0 (got {risk_sum:.4f})."
        )

    # 3. Risk Score Bands Ordering (Safe < Moderate < High < Very High <= Critical)
    bands = profile.risk_bands
    if not (0.0 <= bands.safe_max < bands.moderate_max < bands.high_max < bands.very_high_max <= bands.critical_max <= 100.0):
        errors.append(
            f"Risk score bands must be strictly ascending: "
            f"0 <= safe({bands.safe_max}) < moderate({bands.moderate_max}) < "
            f"high({bands.high_max}) < very_high({bands.very_high_max}) <= critical({bands.critical_max}) <= 100"
        )

    # 4. Hazard Weights Sum
    hw = profile.hazard_parameters.weights
    hazard_sum = hw.landslide + hw.flood + hw.rainfall + hw.seismic + hw.coastal_storm_surge
    if not math.isclose(hazard_sum, 1.0, abs_tol=WEIGHT_TOLERANCE):
        errors.append(
            f"Hazard weights must sum to 1.0 (got {hazard_sum:.4f})."
        )

    # 5. Hazard Threshold Ordering
    ht = profile.hazard_parameters.thresholds
    if ht.slope_warning_deg >= ht.slope_critical_deg:
        errors.append(
            f"Hazard slope warning threshold ({ht.slope_warning_deg}°) must be less than "
            f"critical slope threshold ({ht.slope_critical_deg}°)."
        )
    if ht.rainfall_heavy_24h_mm >= ht.rainfall_very_heavy_24h_mm:
        errors.append(
            f"Heavy rainfall threshold ({ht.rainfall_heavy_24h_mm} mm) must be less than "
            f"very heavy rainfall threshold ({ht.rainfall_very_heavy_24h_mm} mm)."
        )

    # 6. Vulnerability Component Weights Sum
    vw = profile.vulnerability_parameters.component_weights
    vuln_sum = vw.social_weight + vw.economic_weight + vw.structural_weight + vw.road_connectivity_weight
    if not math.isclose(vuln_sum, 1.0, abs_tol=WEIGHT_TOLERANCE):
        errors.append(
            f"Vulnerability component weights must sum to 1.0 (got {vuln_sum:.4f})."
        )

    # 7. Red Zone Thresholds
    rz_perm = profile.red_zone_thresholds.permanent_criteria
    rz_dyn = profile.red_zone_thresholds.dynamic_triggers
    if rz_perm.min_slope_deg <= 0.0:
        errors.append("Permanent Red Zone minimum slope must be strictly positive.")
    if rz_dyn.rainfall_trigger_24h_mm <= 0.0:
        errors.append("Dynamic Red Zone 24h rainfall trigger must be strictly positive.")
    if rz_dyn.slope_trigger_min_deg < 0.0:
        errors.append("Dynamic Red Zone minimum slope trigger cannot be negative.")

    # 8. Relocation Priority Cutoffs & Weights (0.40R + 0.25E + 0.20V + 0.10H + 0.05A)
    rp = profile.relocation_priority_parameters
    if not (0.0 <= rp.cutoffs.medium_term_min < rp.cutoffs.short_term_min < rp.cutoffs.immediate_min <= 100.0):
        errors.append(
            f"Relocation priority cutoffs must be strictly ascending: "
            f"0 <= medium_term({rp.cutoffs.medium_term_min}) < "
            f"short_term({rp.cutoffs.short_term_min}) < "
            f"immediate({rp.cutoffs.immediate_min}) <= 100"
        )
    rp_sum = (
        rp.weights.risk_weight
        + rp.weights.exposure_weight
        + rp.weights.vulnerability_weight
        + rp.weights.historical_impact_weight
        + rp.weights.accessibility_weight
    )
    if not math.isclose(rp_sum, 1.0, abs_tol=WEIGHT_TOLERANCE):
        errors.append(
            f"Relocation priority factor weights must sum to 1.0 (got {rp_sum:.4f})."
        )

    # 9. Site Capacity Assumptions vs Hazard Thresholds
    sc = profile.site_capacity_assumptions
    if sc.max_safe_slope_deg > ht.slope_warning_deg:
        errors.append(
            f"Relocation site safe slope limit ({sc.max_safe_slope_deg}°) cannot exceed "
            f"regional hazard slope warning threshold ({ht.slope_warning_deg}°)."
        )
    if sc.water_supply_lpd_per_capita <= 0.0:
        errors.append("Relocation site water supply assumption must be strictly positive.")
    if sc.hazard_buffer_m < 0.0:
        errors.append("Hazard buffer distance cannot be negative.")

    # 10. Scenario Simulation Bounds
    sb = profile.scenario_bounds
    if not (sb.min_rainfall_multiplier <= sb.default_rainfall_multiplier <= sb.max_rainfall_multiplier):
        errors.append(
            f"Rainfall multiplier ordering violated: min({sb.min_rainfall_multiplier}) <= "
            f"default({sb.default_rainfall_multiplier}) <= max({sb.max_rainfall_multiplier})"
        )
    if sb.min_seismic_intensity_mmi > sb.max_seismic_intensity_mmi:
        errors.append(
            f"Seismic intensity bounds inverted: min({sb.min_seismic_intensity_mmi}) > "
            f"max({sb.max_seismic_intensity_mmi})"
        )

    if errors:
        raise ProfileValidationError(
            f"Validation failed for profile '{profile.metadata.id.value}'",
            errors=errors,
        )
