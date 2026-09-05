"""Deterministic scoring functions for the 9 candidate site suitability criteria."""

import math
from typing import Optional, Tuple

from app.core.relocation.suitability.contracts import CriterionType, SiteSuitabilityInput, SuitabilityThresholdsConfig
from app.core.relocation.suitability.errors import InvalidSiteDataError


def _validate_numeric(name: str, value: Optional[float]) -> None:
    """Validate that a float value is not NaN or infinite."""
    if value is not None:
        if math.isnan(value) or math.isinf(value):
            raise InvalidSiteDataError(f"Attribute '{name}' cannot be NaN or infinite, got: {value}")


def score_hazard_safety(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 1: Hazard Safety (Weight: 30%).

    Evaluates terrain slope stability and hazard buffer distance from active hazard runouts.
    - Slope <= 5.0 deg -> 100.0
    - Slope between 5.0 and max_safe_slope (15.0 deg) -> linear drop from 100 to 50
    - Slope > max_safe_slope -> drops steeply towards 0.0
    - Hazard buffer >= 1200m -> 100.0
    - Hazard buffer between 500m and 1200m -> linear interpolation from 50 to 100
    - Hazard buffer < 500m -> penalized towards 0.0
    """
    _validate_numeric("terrain_slope_deg", site.terrain_slope_deg)
    _validate_numeric("hazard_buffer_distance_m", site.hazard_buffer_distance_m)

    slope = site.terrain_slope_deg
    if slope is None:
        slope_score = 30.0  # Unknown slope penalty
        slope_audit = "Slope unknown; defaulted to low baseline 30.0"
    elif slope <= 5.0:
        slope_score = 100.0
        slope_audit = f"Slope {slope:.1f}° is gentle (<=5°): optimal stability (100.0)"
    elif slope <= thresholds.max_safe_slope_deg:
        # Linear drop 100 -> 50 between 5.0 and max_safe_slope_deg
        ratio = (slope - 5.0) / (thresholds.max_safe_slope_deg - 5.0)
        slope_score = 100.0 - (ratio * 50.0)
        slope_audit = f"Slope {slope:.1f}° within safe limit ({thresholds.max_safe_slope_deg:.1f}°): score {slope_score:.1f}"
    else:
        # Exceeds max safe slope: drops rapidly
        excess = slope - thresholds.max_safe_slope_deg
        slope_score = max(0.0, 40.0 - (excess * 8.0))
        slope_audit = f"Slope {slope:.1f}° exceeds safe threshold ({thresholds.max_safe_slope_deg:.1f}°): penalized to {slope_score:.1f}"

    buffer_dist = site.hazard_buffer_distance_m
    if buffer_dist is None:
        buffer_score = 70.0  # Moderate default if no active observation
        buffer_audit = "Hazard buffer distance not provided; moderate baseline 70.0"
    elif buffer_dist >= 1200.0:
        buffer_score = 100.0
        buffer_audit = f"Hazard buffer {buffer_dist:.0f}m >= 1200m: maximum safety buffer (100.0)"
    elif buffer_dist >= thresholds.min_hazard_buffer_m:
        ratio = (buffer_dist - thresholds.min_hazard_buffer_m) / (1200.0 - thresholds.min_hazard_buffer_m)
        buffer_score = 50.0 + (ratio * 50.0)
        buffer_audit = f"Hazard buffer {buffer_dist:.0f}m >= {thresholds.min_hazard_buffer_m:.0f}m: score {buffer_score:.1f}"
    else:
        ratio = buffer_dist / max(1.0, thresholds.min_hazard_buffer_m)
        buffer_score = max(0.0, ratio * 40.0)
        buffer_audit = f"Hazard buffer {buffer_dist:.0f}m violates mandatory buffer {thresholds.min_hazard_buffer_m:.0f}m: penalized to {buffer_score:.1f}"

    # Soil stability adjustment if provided
    soil = (site.soil_stability or "").lower()
    soil_mod = 1.0
    if "consolidated" in soil or "stable" in soil:
        soil_mod = 1.0
    elif "debris" in soil or "fractured" in soil or "scree" in soil:
        soil_mod = 0.85

    score = min(100.0, max(0.0, ((slope_score * 0.55) + (buffer_score * 0.45)) * soil_mod))
    desc = f"Hazard safety score: {score:.1f}/100. Slope ({slope_score:.1f}), Buffer ({buffer_score:.1f})"
    audit = f"{slope_audit}; {buffer_audit}"
    return score, desc, audit


def score_capacity(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 2: Capacity & Resource Limits (Weight: 20%).

    Evaluates available households, population capacity, total usable land area, and sanitation.
    - >= 150 households -> 100.0
    - 20 to 150 households -> linear scaling [50, 100]
    - < 20 households -> bottleneck [0, 45]
    """
    _validate_numeric("area_sq_m", site.area_sq_m)

    avail_hh = site.available_households if site.available_households is not None else site.max_households
    if avail_hh is None or avail_hh <= 0:
        return 0.0, "Zero or unknown household capacity: 0.0/100", "Missing or zero capacity"

    if avail_hh >= 150:
        hh_score = 100.0
    elif avail_hh >= thresholds.min_viable_households:
        ratio = (avail_hh - thresholds.min_viable_households) / (150.0 - thresholds.min_viable_households)
        hh_score = 50.0 + (ratio * 50.0)
    else:
        # Capacity bottleneck (insufficient for full community transfer)
        ratio = avail_hh / thresholds.min_viable_households
        hh_score = max(0.0, ratio * 45.0)

    # Area scaling: >= 50,000 m2 -> 100, down to 10,000 m2 -> 40
    area = site.area_sq_m
    if area is None:
        area_score = hh_score
    elif area >= 60000.0:
        area_score = 100.0
    elif area >= 20000.0:
        ratio = (area - 20000.0) / 40000.0
        area_score = 60.0 + (ratio * 40.0)
    else:
        ratio = max(0.0, area / 20000.0)
        area_score = ratio * 60.0

    score = min(100.0, max(0.0, (hh_score * 0.70) + (area_score * 0.30)))
    desc = f"Capacity score: {score:.1f}/100. Usable households: {avail_hh}"
    audit = f"Households component: {hh_score:.1f}; Land area component: {area_score:.1f}"
    return score, desc, audit


def score_road_access(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 3: Road & Transport Access (Weight: 10%).

    Evaluates road carriageway width, distance to highway, and all-weather access.
    """
    _validate_numeric("road_width_m", site.road_width_m)
    _validate_numeric("distance_to_highway_km", site.distance_to_highway_km)

    width = site.road_width_m
    if width is None:
        width_score = 50.0
    elif width >= 6.0:
        width_score = 100.0
    elif width >= 3.5:
        width_score = 60.0 + ((width - 3.5) / 2.5) * 40.0
    else:
        width_score = max(0.0, (width / 3.5) * 50.0)

    dist_hw = site.distance_to_highway_km
    if dist_hw is None:
        hw_score = 60.0
    elif dist_hw <= 0.5:
        hw_score = 100.0
    elif dist_hw <= 3.0:
        hw_score = 100.0 - ((dist_hw - 0.5) / 2.5) * 40.0
    else:
        hw_score = max(0.0, 60.0 - ((dist_hw - 3.0) * 10.0))

    all_weather_mult = 1.0 if site.all_weather_access is not False else 0.70

    score = min(100.0, max(0.0, ((width_score * 0.50) + (hw_score * 0.50)) * all_weather_mult))
    desc = f"Road access score: {score:.1f}/100. Road width: {width or 'N/A'}m, Hwy dist: {dist_hw or 'N/A'}km"
    audit = f"Width score: {width_score:.1f}; Highway proximity: {hw_score:.1f}; All-weather mult: {all_weather_mult}"
    return score, desc, audit


def score_water_availability(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 4: Water Availability (Weight: 10%).

    Evaluates daily per-capita water supply (LPD), distance to source, and perennial reliability.
    """
    _validate_numeric("water_supply_lpd_per_capita", site.water_supply_lpd_per_capita)
    _validate_numeric("water_source_distance_m", site.water_source_distance_m)

    lpd = site.water_supply_lpd_per_capita
    if lpd is None:
        lpd_score = 50.0
    elif lpd >= 85.0:
        lpd_score = 100.0
    elif lpd >= thresholds.min_water_lpd_per_capita:
        ratio = (lpd - thresholds.min_water_lpd_per_capita) / (85.0 - thresholds.min_water_lpd_per_capita)
        lpd_score = 70.0 + (ratio * 30.0)
    else:
        ratio = max(0.0, lpd / thresholds.min_water_lpd_per_capita)
        lpd_score = ratio * 60.0

    dist_src = site.water_source_distance_m
    if dist_src is None:
        src_score = 70.0
    elif dist_src <= 250.0:
        src_score = 100.0
    elif dist_src <= 800.0:
        src_score = 100.0 - ((dist_src - 250.0) / 550.0) * 40.0
    else:
        src_score = max(0.0, 60.0 - ((dist_src - 800.0) / 600.0) * 40.0)

    perennial_mult = 1.0 if site.perennial_water_source is not False else 0.75

    score = min(100.0, max(0.0, ((lpd_score * 0.65) + (src_score * 0.35)) * perennial_mult))
    desc = f"Water availability score: {score:.1f}/100. Per capita supply: {lpd or 'N/A'} LPD"
    audit = f"Supply score: {lpd_score:.1f}; Source distance score: {src_score:.1f}; Perennial mult: {perennial_mult}"
    return score, desc, audit


def score_healthcare_access(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 5: Healthcare Access (Weight: 10%).

    Evaluates proximity to primary health center or on-site operational medical infrastructure.
    """
    _validate_numeric("distance_to_health_center_km", site.distance_to_health_center_km)

    if site.has_on_site_health_center:
        return 100.0, "Healthcare score: 100.0/100 (On-site operational medical center)", "On-site medical asset present"

    dist = site.distance_to_health_center_km
    if dist is None:
        return 50.0, "Healthcare score: 50.0/100 (Distance unknown, default baseline)", "Distance to health center unknown"

    if dist <= 1.0:
        score = 100.0
    elif dist <= 5.0:
        score = 100.0 - ((dist - 1.0) / 4.0) * 50.0  # 1km -> 100, 5km -> 50
    elif dist <= 10.0:
        score = max(10.0, 50.0 - ((dist - 5.0) / 5.0) * 40.0)
    else:
        score = max(0.0, 10.0 - (dist - 10.0))

    desc = f"Healthcare access score: {score:.1f}/100. Distance to PHC: {dist:.1f}km"
    audit = f"Distance {dist:.1f}km evaluated on medical access curve"
    return score, desc, audit


def score_school_access(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 6: School Access (Weight: 5%).

    Evaluates proximity to primary/secondary education facilities.
    """
    _validate_numeric("distance_to_school_km", site.distance_to_school_km)

    dist = site.distance_to_school_km
    if dist is None:
        return 50.0, "School access score: 50.0/100 (Distance unknown, default baseline)", "Distance to school unknown"

    if dist <= 0.8:
        score = 100.0
    elif dist <= 3.0:
        score = 100.0 - ((dist - 0.8) / 2.2) * 50.0  # 0.8km -> 100, 3km -> 50
    else:
        score = max(0.0, 50.0 - ((dist - 3.0) * 15.0))

    desc = f"School access score: {score:.1f}/100. Distance: {dist:.1f}km"
    audit = f"Distance {dist:.1f}km evaluated on school access curve"
    return score, desc, audit


def score_emergency_services(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 7: Emergency Services (Weight: 5%).

    Evaluates proximity to emergency response / SDRF station or on-site helipad / relief shelter.
    """
    _validate_numeric("distance_to_emergency_km", site.distance_to_emergency_km)

    if site.has_on_site_helipad_or_shelter:
        return 100.0, "Emergency services score: 100.0/100 (On-site helipad/shelter present)", "On-site emergency asset present"

    dist = site.distance_to_emergency_km
    if dist is None:
        return 50.0, "Emergency services score: 50.0/100 (Distance unknown, default baseline)", "Distance to emergency unknown"

    if dist <= 2.0:
        score = 100.0
    elif dist <= 6.0:
        score = 100.0 - ((dist - 2.0) / 4.0) * 50.0  # 2km -> 100, 6km -> 50
    else:
        score = max(0.0, 50.0 - ((dist - 6.0) * 10.0))

    desc = f"Emergency services score: {score:.1f}/100. Distance: {dist:.1f}km"
    audit = f"Distance {dist:.1f}km evaluated on emergency access curve"
    return score, desc, audit


def score_livelihood_access(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 8: Livelihood Access (Weight: 5%).

    Evaluates agricultural and market economic potential for relocated community sustainability.
    """
    _validate_numeric("distance_to_farmland_km", site.distance_to_farmland_km)
    _validate_numeric("distance_to_market_km", site.distance_to_market_km)

    lp = (site.livelihood_potential or "").lower()
    if lp == "high":
        base_score = 90.0
    elif lp == "moderate":
        base_score = 65.0
    elif lp == "low":
        base_score = 35.0
    else:
        base_score = 50.0

    # Farmland proximity bonus/adjustment
    farm_dist = site.distance_to_farmland_km
    farm_adj = 0.0
    if farm_dist is not None:
        if farm_dist <= 0.6:
            farm_adj = 10.0
        elif farm_dist > 2.0:
            farm_adj = -10.0

    score = min(100.0, max(0.0, base_score + farm_adj))
    desc = f"Livelihood access score: {score:.1f}/100. Rating: '{lp or 'N/A'}'"
    audit = f"Base rating: {base_score:.1f}; Farmland proximity adjustment: {farm_adj:+.1f}"
    return score, desc, audit


def score_expansion_potential(
    site: SiteSuitabilityInput, thresholds: SuitabilityThresholdsConfig
) -> Tuple[float, str, str]:
    """Score Criterion 9: Expansion Potential (Weight: 5%).

    Evaluates buffer zone for future growth and community expansion.
    """
    ep = (site.expansion_potential or "").lower()
    if ep == "high":
        score = 100.0
    elif ep == "moderate":
        score = 70.0
    elif ep == "low":
        score = 40.0
    elif ep == "none":
        score = 15.0
    else:
        # If area is very large, infer expansion potential
        if site.area_sq_m and site.area_sq_m >= 60000.0:
            score = 80.0
        elif site.area_sq_m and site.area_sq_m >= 35000.0:
            score = 60.0
        else:
            score = 30.0

    desc = f"Expansion potential score: {score:.1f}/100. Level: '{ep or 'N/A'}'"
    audit = f"Expansion rating '{ep or 'N/A'}' mapped to score {score:.1f}"
    return score, desc, audit
