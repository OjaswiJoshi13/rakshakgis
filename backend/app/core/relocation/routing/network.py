"""Road network graph representation and provider abstractions for evacuation routing."""

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.core.relocation.routing.contracts import RouteSegment, SegmentHazardStatus
from app.core.relocation.routing.errors import InsufficientRoutingDataError


def haversine_distance_km(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate the great-circle distance between two (lon, lat) points in kilometers."""
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    if math.isnan(lon1) or math.isnan(lat1) or math.isnan(lon2) or math.isnan(lat2):
        raise ValueError("Coordinates must be non-NaN numbers")

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return 6371.009 * c


class RoadNode(BaseModel):
    """A junction or endpoint in the road network."""

    node_id: str
    location: Tuple[float, float] = Field(..., description="(longitude, latitude)")
    elevation_m: Optional[float] = None
    name: Optional[str] = None


class RoadSegmentEdge(BaseModel):
    """A directed or bidirectional road segment connecting two nodes."""

    segment_id: str
    from_node: str
    to_node: str
    distance_km: float = Field(..., ge=0.0)
    speed_kmh: Optional[float] = Field(default=30.0, ge=0.0)
    geometry: List[Tuple[float, float]] = Field(..., description="LineString coordinates [(lon, lat), ...]")
    road_type: str = "primary"
    road_width_m: Optional[float] = 6.0
    bidirectional: bool = True

    def calculate_travel_time_minutes(self) -> Optional[float]:
        """Calculate estimated travel time in minutes based on distance and speed."""
        if self.speed_kmh is None or self.speed_kmh <= 0.0:
            return None
        return (self.distance_km / self.speed_kmh) * 60.0


class RoadNetwork:
    """In-memory spatial graph representation of a road network."""

    def __init__(self) -> None:
        self.nodes: Dict[str, RoadNode] = {}
        self.adjacency: Dict[str, List[RoadSegmentEdge]] = {}
        self.segments: Dict[str, RoadSegmentEdge] = {}

    def add_node(self, node: RoadNode) -> None:
        """Register a node in the graph."""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def add_segment(self, segment: RoadSegmentEdge) -> None:
        """Add an edge to the graph (and reverse edge if bidirectional)."""
        self.segments[segment.segment_id] = segment
        if segment.from_node not in self.adjacency:
            self.adjacency[segment.from_node] = []
        self.adjacency[segment.from_node].append(segment)

        if segment.bidirectional:
            rev_id = f"{segment.segment_id}_rev"
            rev_geom = list(reversed(segment.geometry))
            rev_edge = RoadSegmentEdge(
                segment_id=rev_id,
                from_node=segment.to_node,
                to_node=segment.from_node,
                distance_km=segment.distance_km,
                speed_kmh=segment.speed_kmh,
                geometry=rev_geom,
                road_type=segment.road_type,
                road_width_m=segment.road_width_m,
                bidirectional=False,
            )
            if segment.to_node not in self.adjacency:
                self.adjacency[segment.to_node] = []
            self.adjacency[segment.to_node].append(rev_edge)

    def get_outgoing_edges(self, node_id: str) -> List[RoadSegmentEdge]:
        """Return outgoing edges from the specified node deterministically ordered by segment_id."""
        edges = self.adjacency.get(node_id, [])
        return sorted(edges, key=lambda e: e.segment_id)

    def find_nearest_node(
        self, coord: Tuple[float, float], max_distance_km: float = 15.0
    ) -> Tuple[RoadNode, float]:
        """Find the nearest graph node to the specified coordinates.

        Raises InsufficientRoutingDataError if network is empty or nearest node exceeds max_distance_km.
        """
        if not self.nodes:
            raise InsufficientRoutingDataError("Road network contains no nodes.")

        best_node: Optional[RoadNode] = None
        min_dist = float("inf")

        # Deterministic node iteration
        for node_id in sorted(self.nodes.keys()):
            node = self.nodes[node_id]
            d = haversine_distance_km(coord, node.location)
            if d < min_dist:
                min_dist = d
                best_node = node

        if best_node is None or min_dist > max_distance_km:
            raise InsufficientRoutingDataError(
                f"Coordinates ({coord[0]:.4f}, {coord[1]:.4f}) are {min_dist:.1f} km from the nearest road "
                f"network node; exceeds threshold of {max_distance_km:.1f} km."
            )

        return best_node, min_dist


class BaseRoadNetworkProvider(ABC):
    """Abstract interface for road network data sources."""

    @abstractmethod
    def get_road_network(
        self,
        region_profile_id: str,
        bounding_box: Optional[Tuple[float, float, float, float]] = None,
    ) -> RoadNetwork:
        """Retrieve the road network for the specified region."""
        pass


class SyntheticHimalayanRoadProvider(BaseRoadNetworkProvider):
    """Deterministic synthetic road network for the Himalayan Pilot region (Joshimath-Pipalkoti corridor)."""

    def get_road_network(
        self,
        region_profile_id: str,
        bounding_box: Optional[Tuple[float, float, float, float]] = None,
    ) -> RoadNetwork:
        net = RoadNetwork()

        # Nodes
        # 1. Village Clusters (Joshimath upper area)
        net.add_node(RoadNode(node_id="N_SUNIL", location=(79.5575, 30.5347), name="Sunil Village Gateway"))
        net.add_node(RoadNode(node_id="N_RAVIGRAM", location=(79.5750, 30.5500), name="Ravigram Village Gateway"))
        net.add_node(RoadNode(node_id="N_JOSHIMATH_HUB", location=(79.5650, 30.5550), name="Joshimath Main Junction"))
        net.add_node(RoadNode(node_id="N_MARWARI", location=(79.5700, 30.5600), name="Marwari River Terrace"))

        # 2. Corridor 1: Lower Valley Highway (NH-7 river corridor towards Pipalkoti)
        net.add_node(RoadNode(node_id="N_VALLEY_1", location=(79.5350, 30.5350), name="Lower Valley Checkpoint 1"))
        net.add_node(RoadNode(node_id="N_HELANG_VALLEY", location=(79.5100, 30.5150), name="Helang Valley Bridge"))
        net.add_node(RoadNode(node_id="N_ANIMATH_VALLEY", location=(79.4700, 30.4700), name="Animath Lower Road"))
        net.add_node(RoadNode(node_id="N_PIPALKOTI", location=(79.4300, 30.4300), name="Pipalkoti Safe Relocation Center"))

        # 3. Corridor 2: Upper Ridge Bypass Road (High terrace safe from river runout)
        net.add_node(RoadNode(node_id="N_UPPER_RIDGE_1", location=(79.5400, 30.5500), name="Upper Ridge Pass 1"))
        net.add_node(RoadNode(node_id="N_UPPER_RIDGE_2", location=(79.4900, 30.5100), name="Upper Terrace Bypass 2"))
        net.add_node(RoadNode(node_id="N_UPPER_RIDGE_3", location=(79.4600, 30.4600), name="Upper Ridge Junction 3"))

        # 4. Eastern Relocation Site (Dhak)
        net.add_node(RoadNode(node_id="N_DHAK", location=(79.6100, 30.5100), name="Dhak Relocation Site Gateway"))

        # Road Segments
        # Village links to central hub
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VILL-SUNIL",
                from_node="N_SUNIL",
                to_node="N_JOSHIMATH_HUB",
                distance_km=2.8,
                speed_kmh=25.0,
                geometry=[(79.5575, 30.5347), (79.5610, 30.5450), (79.5650, 30.5550)],
                road_type="secondary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VILL-SUNIL-UPPER",
                from_node="N_SUNIL",
                to_node="N_UPPER_RIDGE_1",
                distance_km=3.4,
                speed_kmh=20.0,
                geometry=[(79.5575, 30.5347), (79.5500, 30.5420), (79.5400, 30.5500)],
                road_type="tertiary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VILL-RAVIGRAM",
                from_node="N_RAVIGRAM",
                to_node="N_JOSHIMATH_HUB",
                distance_km=1.9,
                speed_kmh=25.0,
                geometry=[(79.5750, 30.5500), (79.5700, 30.5520), (79.5650, 30.5550)],
                road_type="secondary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VILL-MARWARI",
                from_node="N_MARWARI",
                to_node="N_JOSHIMATH_HUB",
                distance_km=1.2,
                speed_kmh=20.0,
                geometry=[(79.5700, 30.5600), (79.5680, 30.5580), (79.5650, 30.5550)],
                road_type="tertiary",
            )
        )

        # Eastern Route to Dhak
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-DHAK-LINK",
                from_node="N_JOSHIMATH_HUB",
                to_node="N_DHAK",
                distance_km=6.8,
                speed_kmh=35.0,
                geometry=[(79.5650, 30.5550), (79.5850, 30.5300), (79.6100, 30.5100)],
                road_type="primary",
            )
        )

        # Corridor 1: Lower Valley Highway (Shorter in distance: 3.2 + 3.8 + 6.2 + 5.5 = 18.7 km)
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VALLEY-01",
                from_node="N_JOSHIMATH_HUB",
                to_node="N_VALLEY_1",
                distance_km=3.2,
                speed_kmh=35.0,
                geometry=[(79.5650, 30.5550), (79.5500, 30.5450), (79.5350, 30.5350)],
                road_type="primary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VALLEY-02",
                from_node="N_VALLEY_1",
                to_node="N_HELANG_VALLEY",
                distance_km=3.8,
                speed_kmh=35.0,
                geometry=[(79.5350, 30.5350), (79.5250, 30.5250), (79.5100, 30.5150)],
                road_type="primary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VALLEY-03",
                from_node="N_HELANG_VALLEY",
                to_node="N_ANIMATH_VALLEY",
                distance_km=6.2,
                speed_kmh=35.0,
                geometry=[(79.5100, 30.5150), (79.4900, 30.4900), (79.4700, 30.4700)],
                road_type="primary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-VALLEY-04",
                from_node="N_ANIMATH_VALLEY",
                to_node="N_PIPALKOTI",
                distance_km=5.5,
                speed_kmh=40.0,
                geometry=[(79.4700, 30.4700), (79.4500, 30.4500), (79.4300, 30.4300)],
                road_type="primary",
            )
        )

        # Corridor 2: Upper Ridge Bypass Road (Longer in distance: 3.5 + 6.8 + 6.0 + 4.9 = 21.2 km)
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-BYPASS-01",
                from_node="N_JOSHIMATH_HUB",
                to_node="N_UPPER_RIDGE_1",
                distance_km=3.5,
                speed_kmh=30.0,
                geometry=[(79.5650, 30.5550), (79.5520, 30.5530), (79.5400, 30.5500)],
                road_type="secondary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-BYPASS-02",
                from_node="N_UPPER_RIDGE_1",
                to_node="N_UPPER_RIDGE_2",
                distance_km=6.8,
                speed_kmh=30.0,
                geometry=[(79.5400, 30.5500), (79.5150, 30.5300), (79.4900, 30.5100)],
                road_type="secondary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-BYPASS-03",
                from_node="N_UPPER_RIDGE_2",
                to_node="N_UPPER_RIDGE_3",
                distance_km=6.0,
                speed_kmh=35.0,
                geometry=[(79.4900, 30.5100), (79.4750, 30.4850), (79.4600, 30.4600)],
                road_type="secondary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-BYPASS-04",
                from_node="N_UPPER_RIDGE_3",
                to_node="N_PIPALKOTI",
                distance_km=4.9,
                speed_kmh=35.0,
                geometry=[(79.4600, 30.4600), (79.4450, 30.4450), (79.4300, 30.4300)],
                road_type="secondary",
            )
        )

        # Cross-Connecting Link Roads (Enabling dynamic rerouting and alternatives)
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-LINK-HELANG",
                from_node="N_HELANG_VALLEY",
                to_node="N_UPPER_RIDGE_2",
                distance_km=3.2,
                speed_kmh=25.0,
                geometry=[(79.5100, 30.5150), (79.5000, 30.5120), (79.4900, 30.5100)],
                road_type="tertiary",
            )
        )
        net.add_segment(
            RoadSegmentEdge(
                segment_id="SEG-LINK-ANIMATH",
                from_node="N_ANIMATH_VALLEY",
                to_node="N_UPPER_RIDGE_3",
                distance_km=2.6,
                speed_kmh=25.0,
                geometry=[(79.4700, 30.4700), (79.4650, 30.4650), (79.4600, 30.4600)],
                road_type="tertiary",
            )
        )

        return net
