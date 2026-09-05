"""Deterministic spatial distance calculation and candidate site ranking for Relocation Matching."""

import math
from typing import Any, Dict, List, Optional, Tuple


def calculate_haversine_distance_km(
    coord1: Optional[Tuple[float, float]],
    coord2: Optional[Tuple[float, float]],
) -> Optional[float]:
    """Calculate the great-circle distance between two (longitude, latitude) points in kilometers.

    Uses the standard Haversine formulation with mean Earth radius R = 6371.009 km.
    Returns None if either coordinate is missing or None.
    """
    if coord1 is None or coord2 is None:
        return None

    lon1, lat1 = coord1
    lon2, lat2 = coord2

    # Guard against invalid NaN or non-finite values
    if math.isnan(lon1) or math.isnan(lat1) or math.isnan(lon2) or math.isnan(lat2):
        return None

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Numerical stability clamp for floating point inaccuracies
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    radius_km = 6371.009

    return round(radius_km * c, 2)


def compute_proximity_score(distance_km: Optional[float]) -> Optional[float]:
    """Compute a normalized [0.0, 100.0] accessibility score based on distance in kilometers.

    Exact approved linear formula:
      proximity_score = max(0.0, 100.0 - 2.0 * distance_km)
      Clamped to [0.0, 100.0].
      At 0 km: 100.0
      At 10 km: 80.0
      At 50 km: 0.0
      Beyond 50 km: 0.0
    """
    if distance_km is None:
        return None
    if math.isnan(distance_km) or math.isinf(distance_km):
        return None
    if distance_km < 0.0:
        raise ValueError(f"distance_km must be non-negative and finite, got {distance_km}")

    score = 100.0 - (2.0 * distance_km)
    return max(0.0, min(100.0, score))


def compute_matching_rank_score(
    suitability_score: float, distance_km: Optional[float]
) -> float:
    """Compute composite deterministic ranking score prioritizing suitability while rewarding proximity.

    Formula:
      rank_score = 0.70 * suitability_score + 0.30 * proximity_score (if distance available)
      rank_score = suitability_score (if distance unavailable / spatial coordinates absent)
    """
    prox_score = compute_proximity_score(distance_km)
    if prox_score is not None:
        score = (0.70 * suitability_score) + (0.30 * prox_score)
    else:
        score = suitability_score
    return score


def sort_feasible_candidates(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort feasible candidate site evaluations deterministically.

    Exact deterministic order:
      (-rank_score, -suitability_score, distance_km, str(site_id))
    """
    def sort_key(item: Dict[str, Any]) -> Tuple[float, float, float, str]:
        r_score = item.get("rank_score")
        r_val = float(r_score) if r_score is not None else 0.0

        s_score = item.get("suitability_score")
        s_val = float(s_score) if s_score is not None else 0.0

        d_km = item.get("distance_km")
        d_val = float(d_km) if d_km is not None else float("inf")

        site_id_str = str(item.get("site_id", ""))
        return (-r_val, -s_val, d_val, site_id_str)

    return sorted(candidates, key=sort_key)
