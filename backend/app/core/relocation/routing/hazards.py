"""Hazard exposure evaluation and dynamic penalty calculations for road segments."""

import math
from typing import Any, Dict, List, Optional, Tuple

from app.core.relocation.routing.contracts import (
    HazardExposureDetail,
    HazardType,
    RouteSegment,
    SegmentHazardStatus,
)
from app.core.relocation.routing.network import RoadSegmentEdge, haversine_distance_km


def distance_point_to_line_segment_m(
    point: Tuple[float, float],
    seg_start: Tuple[float, float],
    seg_end: Tuple[float, float],
    samples: int = 10,
) -> float:
    """Approximate minimum distance in meters from a point to a geodesic line segment."""
    lon_p, lat_p = point
    lon1, lat1 = seg_start
    lon2, lat2 = seg_end

    min_dist_km = min(
        haversine_distance_km(point, seg_start),
        haversine_distance_km(point, seg_end),
    )

    # Sample intermediate points along the segment for high accuracy
    for i in range(1, samples):
        t = i / float(samples)
        interp_lon = lon1 + t * (lon2 - lon1)
        interp_lat = lat1 + t * (lat2 - lat1)
        d = haversine_distance_km(point, (interp_lon, interp_lat))
        if d < min_dist_km:
            min_dist_km = d

    return min_dist_km * 1000.0


def distance_point_to_linestring_m(
    point: Tuple[float, float],
    linestring: List[Tuple[float, float]],
) -> float:
    """Calculate minimum distance in meters from a point to a LineString geometry."""
    if not linestring:
        return float("inf")
    if len(linestring) == 1:
        return haversine_distance_km(point, linestring[0]) * 1000.0

    min_dist_m = float("inf")
    for i in range(len(linestring) - 1):
        d_m = distance_point_to_line_segment_m(point, linestring[i], linestring[i + 1])
        if d_m < min_dist_m:
            min_dist_m = d_m
    return min_dist_m


class HazardAwareRouteEvaluator:
    """Evaluates road segments against active hazard events, applying penalties or blocking cut-off links."""

    # Default buffer radii in meters
    DEFAULT_CRITICAL_BUFFER_M = 800.0
    DEFAULT_HIGH_BUFFER_M = 1200.0
    DEFAULT_MODERATE_BUFFER_M = 1500.0

    # Cost penalty multipliers (applied to base segment distance)
    PENALTY_MULTIPLIERS = {
        "critical": 5.0,     # Heavily penalized if not blocked
        "high": 1.5,         # +150% distance penalty
        "moderate": 0.6,     # +60% distance penalty
        "low": 0.2,          # +20% distance penalty
    }

    def __init__(self, hazard_events: Optional[List[Dict[str, Any]]] = None) -> None:
        self.hazard_events = hazard_events or []

    def evaluate_segment(
        self,
        edge: RoadSegmentEdge,
        custom_hazard_context: Optional[Dict[str, Any]] = None,
    ) -> RouteSegment:
        """Evaluate a road segment edge against known hazard events, returning an evaluated RouteSegment."""
        exposures: List[HazardExposureDetail] = []
        is_blocked = False
        blockage_reasons: List[str] = []
        max_penalty_mult = 0.0

        # Check explicit overrides from custom context if provided
        context_events = (custom_hazard_context or {}).get("hazard_events", self.hazard_events)
        blocked_segment_ids = set((custom_hazard_context or {}).get("blocked_segment_ids", []))

        # Check direct segment blockage override
        clean_seg_id = edge.segment_id.replace("_rev", "")
        if edge.segment_id in blocked_segment_ids or clean_seg_id in blocked_segment_ids:
            is_blocked = True
            blockage_reasons.append(f"Segment '{edge.segment_id}' is explicitly marked as blocked in hazard context.")

        for evt in context_events:
            loc = evt.get("location")
            if not loc or not isinstance(loc, dict):
                continue
            coords = loc.get("coordinates")
            if not coords or len(coords) < 2:
                continue

            hazard_point = (float(coords[0]), float(coords[1]))
            dist_m = distance_point_to_linestring_m(hazard_point, edge.geometry)

            severity = str(evt.get("severity", "moderate")).lower()
            htype = str(evt.get("hazard_type", "unknown")).lower()
            evt_id = evt.get("id", "UNKNOWN-EVT")
            desc = evt.get("description", "")

            # Buffer thresholds based on severity
            if severity == "critical":
                buffer_m = self.DEFAULT_CRITICAL_BUFFER_M
            elif severity == "high":
                buffer_m = self.DEFAULT_HIGH_BUFFER_M
            else:
                buffer_m = self.DEFAULT_MODERATE_BUFFER_M

            if dist_m <= buffer_m:
                # Segment is within active hazard footprint
                penalty_mult = self.PENALTY_MULTIPLIERS.get(severity, 0.5)

                # Hard blockage rule:
                # 1. Critical event directly intersecting primary highway corridor with road cut-off description
                # 2. Or explicit road blockage attribute on the event
                has_road_cutoff_narrative = (
                    "highway cut off" in desc.lower()
                    or "road blocked" in desc.lower()
                    or "road cut off" in desc.lower()
                )
                is_cut_off = (
                    bool(evt.get("blocks_road"))
                    or (
                        severity == "critical"
                        and dist_m <= 150.0
                        and edge.road_type == "primary"
                        and has_road_cutoff_narrative
                    )
                )

                if is_cut_off:
                    is_blocked = True
                    reason = (
                        f"Road segment cut off by {severity} {htype} event '{evt_id}' "
                        f"(within {dist_m:.0f}m of roadway; {desc})"
                    )
                    blockage_reasons.append(reason)
                    exposures.append(
                        HazardExposureDetail(
                            hazard_type=htype,
                            severity=severity,
                            event_id=evt_id,
                            distance_to_segment_m=round(dist_m, 1),
                            buffer_m=buffer_m,
                            applied_penalty_multiplier=float("inf"),
                            blockage_reason=reason,
                            description=desc,
                        )
                    )
                else:
                    max_penalty_mult = max(max_penalty_mult, penalty_mult)
                    exposures.append(
                        HazardExposureDetail(
                            hazard_type=htype,
                            severity=severity,
                            event_id=evt_id,
                            distance_to_segment_m=round(dist_m, 1),
                            buffer_m=buffer_m,
                            applied_penalty_multiplier=penalty_mult,
                            blockage_reason=None,
                            description=desc,
                        )
                    )

        # Determine overall hazard status
        if is_blocked:
            status = SegmentHazardStatus.BLOCKED
            hazard_penalty = float("inf")
            primary_reason = "; ".join(blockage_reasons)
        elif max_penalty_mult > 0.0:
            status = SegmentHazardStatus.PENALIZED
            hazard_penalty = round(edge.distance_km * max_penalty_mult, 3)
            primary_reason = None
        else:
            status = SegmentHazardStatus.NORMAL
            hazard_penalty = 0.0
            primary_reason = None

        return RouteSegment(
            segment_id=edge.segment_id,
            from_node=edge.from_node,
            to_node=edge.to_node,
            geometry=edge.geometry,
            distance_km=edge.distance_km,
            base_speed_kmh=edge.speed_kmh,
            estimated_time_minutes=edge.calculate_travel_time_minutes(),
            road_type=edge.road_type,
            road_width_m=edge.road_width_m,
            hazard_status=status,
            hazard_penalty=hazard_penalty,
            hazard_exposures=exposures,
            blockage_reason=primary_reason,
        )
