"""Deterministic, explainable evacuation and access routing engine with hazard-aware optimization."""

import heapq
import math
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.profiles.models import RegionProfile
from app.core.profiles.registry import get_profile
from app.core.relocation.routing.contracts import (
    EvacuationRoutingResult,
    HazardExposureDetail,
    RouteExplainability,
    RouteQuery,
    RouteResult,
    RouteSegment,
    RouteStatus,
    RouteType,
    SegmentHazardStatus,
)
from app.core.relocation.routing.errors import (
    InsufficientRoutingDataError,
    InvalidRouteInputError,
    NoFeasibleRouteError,
)
from app.core.relocation.routing.hazards import HazardAwareRouteEvaluator
from app.core.relocation.routing.network import (
    BaseRoadNetworkProvider,
    RoadNetwork,
    RoadNode,
    RoadSegmentEdge,
    SyntheticHimalayanRoadProvider,
    haversine_distance_km,
)


class EvacuationRoutingEngine:
    """Core deterministic routing engine computing safe evacuation routes and alternatives."""

    def __init__(
        self,
        road_provider: Optional[BaseRoadNetworkProvider] = None,
        hazard_evaluator: Optional[HazardAwareRouteEvaluator] = None,
    ) -> None:
        self.road_provider = road_provider or SyntheticHimalayanRoadProvider()
        self.hazard_evaluator = hazard_evaluator or HazardAwareRouteEvaluator()

    @classmethod
    def from_region_profile(
        cls,
        profile: RegionProfile,
        hazard_events: Optional[List[Dict[str, Any]]] = None,
    ) -> "EvacuationRoutingEngine":
        """Instantiate routing engine configured with regional profile settings and hazard events."""
        evaluator = HazardAwareRouteEvaluator(hazard_events=hazard_events)
        return cls(
            road_provider=SyntheticHimalayanRoadProvider(),
            hazard_evaluator=evaluator,
        )

    def route(self, query: RouteQuery) -> EvacuationRoutingResult:
        """Execute deterministic evacuation routing from origin to destination."""
        # 1. Validate input coordinates
        if query.origin is None or query.destination is None:
            raise InvalidRouteInputError("Both origin and destination coordinates must be provided.")

        lon_orig, lat_orig = query.origin
        lon_dest, lat_dest = query.destination

        for val, name in [
            (lon_orig, "origin longitude"),
            (lat_orig, "origin latitude"),
            (lon_dest, "destination longitude"),
            (lat_dest, "destination latitude"),
        ]:
            if math.isnan(val) or math.isinf(val):
                raise InvalidRouteInputError(f"Coordinate {name} cannot be NaN or Infinite.")

        if not (-180.0 <= lon_orig <= 180.0) or not (-90.0 <= lat_orig <= 90.0):
            raise InvalidRouteInputError(f"Origin coordinates ({lon_orig}, {lat_orig}) are out of geographic bounds.")
        if not (-180.0 <= lon_dest <= 180.0) or not (-90.0 <= lat_dest <= 90.0):
            raise InvalidRouteInputError(f"Destination coordinates ({lon_dest}, {lat_dest}) are out of geographic bounds.")

        # 2. Retrieve road network
        network = self.road_provider.get_road_network(query.region_profile_id)
        if not network.nodes:
            return EvacuationRoutingResult(
                status=RouteStatus.INSUFFICIENT_DATA,
                unassigned_reason="No road network data is available for the specified regional profile.",
            )

        # 3. Snap origin and destination to nearest network nodes
        try:
            start_node, d_start = network.find_nearest_node(query.origin, max_distance_km=15.0)
            end_node, d_end = network.find_nearest_node(query.destination, max_distance_km=15.0)
        except InsufficientRoutingDataError as e:
            return EvacuationRoutingResult(
                status=RouteStatus.INSUFFICIENT_DATA,
                unassigned_reason=str(e),
            )

        # 4. Resolve Primary Route
        primary_route, blocked_segments_encountered = self._dijkstra_solve(
            network=network,
            start_node=start_node,
            end_node=end_node,
            origin_coord=query.origin,
            dest_coord=query.destination,
            route_type=RouteType.PRIMARY,
            custom_hazard_context=query.hazard_context,
        )

        if primary_route is None:
            return EvacuationRoutingResult(
                status=RouteStatus.NO_ROUTE,
                assignment_id=query.assignment_id,
                unassigned_reason=(
                    f"No feasible evacuation route exists between origin ({lon_orig:.4f}, {lat_orig:.4f}) and "
                    f"destination ({lon_dest:.4f}, {lat_dest:.4f}). "
                    f"Avoided {len(blocked_segments_encountered)} blocked hazard corridors."
                ),
            )

        # 5. Resolve Alternative Route (if requested)
        alt_route: Optional[RouteResult] = None
        alt_status_str = "Alternative route generation not requested."

        if query.require_alternative:
            primary_seg_ids = {s.segment_id for s in primary_route.segments}
            primary_seg_ids.update({f"{s.segment_id}_rev" for s in primary_route.segments})
            clean_primary_ids = {s.replace("_rev", "") for s in primary_seg_ids}

            alt_route, _ = self._dijkstra_solve(
                network=network,
                start_node=start_node,
                end_node=end_node,
                origin_coord=query.origin,
                dest_coord=query.destination,
                route_type=RouteType.ALTERNATIVE,
                custom_hazard_context=query.hazard_context,
                penalized_segment_ids=clean_primary_ids,
                diversion_penalty_km=50.0,
            )

            if alt_route is not None:
                # Verify genuine distinctness
                alt_seg_ids = {s.segment_id.replace("_rev", "") for s in alt_route.segments}
                shared = clean_primary_ids.intersection(alt_seg_ids)
                overlap_ratio = len(shared) / max(1, len(clean_primary_ids))

                if overlap_ratio >= 0.85:
                    alt_route = None
                    alt_status_str = "NO_FEASIBLE_ALTERNATIVE: Secondary path is substantially identical to primary route."
                else:
                    alt_status_str = (
                        f"Feasible alternative resolved with {len(alt_route.segments)} segments "
                        f"({len(shared)} shared corridor segments; {overlap_ratio * 100:.0f}% overlap)."
                    )
            else:
                alt_status_str = "NO_FEASIBLE_ALTERNATIVE: No secondary path exists without traversing blocked segments."

        # Update primary route explainability with alternative status
        primary_route.explainability.alternative_status = alt_status_str

        return EvacuationRoutingResult(
            status=RouteStatus.FEASIBLE,
            primary_route=primary_route,
            alternative_route=alt_route,
            assignment_id=query.assignment_id,
        )

    def _dijkstra_solve(
        self,
        network: RoadNetwork,
        start_node: RoadNode,
        end_node: RoadNode,
        origin_coord: Tuple[float, float],
        dest_coord: Tuple[float, float],
        route_type: RouteType,
        custom_hazard_context: Optional[Dict[str, Any]] = None,
        penalized_segment_ids: Optional[Set[str]] = None,
        diversion_penalty_km: float = 0.0,
    ) -> Tuple[Optional[RouteResult], List[str]]:
        """Solve deterministic shortest path on road network graph using Dijkstra with exact tuple tie-breaking."""
        penalized_ids = penalized_segment_ids or set()
        blocked_avoided: List[str] = []

        # Priority queue entry: (effective_cost, segment_count, node_id, path_edges)
        # Exact deterministic tie-breaker: round cost to 6 decimals, hop count, node_id string
        pq: List[Tuple[float, int, str, List[RouteSegment]]] = []
        heapq.heappush(pq, (0.0, 0, start_node.node_id, []))

        best_cost: Dict[str, float] = {start_node.node_id: 0.0}

        while pq:
            curr_cost, seg_count, curr_node_id, curr_path = heapq.heappop(pq)

            if curr_cost > best_cost.get(curr_node_id, float("inf")):
                continue

            if curr_node_id == end_node.node_id:
                # Target reached! Construct RouteResult
                route = self._assemble_route_result(
                    segments=curr_path,
                    origin_coord=origin_coord,
                    dest_coord=dest_coord,
                    route_type=route_type,
                    blocked_avoided=blocked_avoided,
                )
                return route, blocked_avoided

            # Explore outgoing edges deterministically
            outgoing_edges = network.get_outgoing_edges(curr_node_id)
            for edge in outgoing_edges:
                evaluated_seg = self.hazard_evaluator.evaluate_segment(
                    edge, custom_hazard_context=custom_hazard_context
                )

                # Hard Safety Constraint: Skip BLOCKED edges entirely
                if evaluated_seg.hazard_status == SegmentHazardStatus.BLOCKED:
                    blocked_avoided.append(
                        f"{evaluated_seg.segment_id}: {evaluated_seg.blockage_reason or 'Hazard cut-off'}"
                    )
                    continue

                clean_id = edge.segment_id.replace("_rev", "")
                diversion_cost = diversion_penalty_km if clean_id in penalized_ids else 0.0

                edge_cost = evaluated_seg.distance_km + evaluated_seg.hazard_penalty + diversion_cost
                new_cost = curr_cost + edge_cost
                next_node_id = edge.to_node

                if new_cost < best_cost.get(next_node_id, float("inf")):
                    best_cost[next_node_id] = new_cost
                    next_path = curr_path + [evaluated_seg]
                    # Key deterministic tie-breaker: cost, hops, next_node_id
                    heapq.heappush(
                        pq,
                        (
                            round(new_cost, 6),
                            seg_count + 1,
                            str(next_node_id),
                            next_path,
                        ),
                    )

        return None, blocked_avoided

    def _assemble_route_result(
        self,
        segments: List[RouteSegment],
        origin_coord: Tuple[float, float],
        dest_coord: Tuple[float, float],
        route_type: RouteType,
        blocked_avoided: List[str],
    ) -> RouteResult:
        """Synthesize a complete RouteResult with continuous geometry and explainability."""
        route_id = f"RTE-{uuid.uuid4().hex[:8].upper()}"
        total_distance = sum(s.distance_km for s in segments)
        total_hazard_penalty = sum(s.hazard_penalty for s in segments)
        effective_cost = total_distance + total_hazard_penalty

        # Compute travel time strictly from segments
        if all(s.estimated_time_minutes is not None for s in segments):
            total_time_min: Optional[float] = round(sum(s.estimated_time_minutes or 0.0 for s in segments), 1)
        else:
            total_time_min = None

        # Build continuous LineString coordinates
        combined_coords: List[Tuple[float, float]] = []
        for i, seg in enumerate(segments):
            for pt in seg.geometry:
                if not combined_coords or combined_coords[-1] != pt:
                    combined_coords.append(pt)

        # Aggregate hazard exposures
        all_exposures: List[HazardExposureDetail] = []
        penalties_applied: List[str] = []
        for seg in segments:
            for exp in seg.hazard_exposures:
                all_exposures.append(exp)
            if seg.hazard_status == SegmentHazardStatus.PENALIZED:
                penalties_applied.append(
                    f"Segment '{seg.segment_id}': +{seg.hazard_penalty:.2f} km penalty ({seg.road_type})"
                )

        hazard_summary = (
            f"Traversed {len(segments)} road segments with {len(penalties_applied)} penalized caution zones. "
            f"Bypassed {len(blocked_avoided)} hazard cut-offs."
        )

        rationale = (
            f"{route_type.value.capitalize()} route selected with lowest deterministic effective cost "
            f"({effective_cost:.2f}) over {total_distance:.2f} km physical road distance."
        )

        explainability = RouteExplainability(
            selection_rationale=rationale,
            hazard_summary=hazard_summary,
            penalties_applied=penalties_applied,
            blocked_segments_avoided=list(set(blocked_avoided)),
            alternative_status="Evaluating alternatives...",
            data_provenance={
                "network_provider": "SyntheticHimalayanRoadProvider",
                "is_synthetic": True,
                "disclaimer": "DEMO / DECISION SUPPORT ONLY for SIH Problem Statement 26191.",
            },
            uncertainty_notes=[
                "Calculated using design speeds; real transit time subject to dynamic weather and congestion."
            ],
        )

        return RouteResult(
            route_id=route_id,
            route_name=f"{route_type.value.capitalize()} Evacuation Corridor ({total_distance:.1f} km)",
            status=RouteStatus.FEASIBLE,
            route_type=route_type,
            origin=origin_coord,
            destination=dest_coord,
            geometry=combined_coords,
            distance_km=round(total_distance, 2),
            estimated_time_minutes=total_time_min,
            base_distance_km=round(total_distance, 2),
            total_hazard_penalty=round(total_hazard_penalty, 2),
            effective_cost=round(effective_cost, 2),
            segments=segments,
            hazard_exposure_summary=all_exposures,
            is_feasible=True,
            explainability=explainability,
        )
