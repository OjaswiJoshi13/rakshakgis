"""Evacuation & Access Routing Engine subsystem for RakshakGIS (Chunk M4-05)."""

from app.core.relocation.routing.contracts import (
    EvacuationRoutingResult,
    HazardExposureDetail,
    HazardType,
    RouteExplainability,
    RouteQuery,
    RouteResult,
    RouteSegment,
    RouteStatus,
    RouteType,
    SegmentHazardStatus,
)
from app.core.relocation.routing.engine import EvacuationRoutingEngine
from app.core.relocation.routing.errors import (
    InsufficientRoutingDataError,
    InvalidRouteInputError,
    NoFeasibleRouteError,
    RouteBlockedError,
    RoutingError,
)
from app.core.relocation.routing.hazards import (
    HazardAwareRouteEvaluator,
    distance_point_to_linestring_m,
)
from app.core.relocation.routing.network import (
    BaseRoadNetworkProvider,
    RoadNetwork,
    RoadNode,
    RoadSegmentEdge,
    SyntheticHimalayanRoadProvider,
    get_default_road_network_provider,
    haversine_distance_km,
)

__all__ = [
    "EvacuationRoutingEngine",
    "BaseRoadNetworkProvider",
    "SyntheticHimalayanRoadProvider",
    "get_default_road_network_provider",
    "HazardAwareRouteEvaluator",
    "haversine_distance_km",
    "distance_point_to_linestring_m",
    "RoadNetwork",
    "RoadNode",
    "RoadSegmentEdge",
    "RouteQuery",
    "RouteResult",
    "RouteSegment",
    "RouteStatus",
    "RouteType",
    "SegmentHazardStatus",
    "HazardExposureDetail",
    "HazardType",
    "RouteExplainability",
    "EvacuationRoutingResult",
    "RoutingError",
    "InvalidRouteInputError",
    "InsufficientRoutingDataError",
    "NoFeasibleRouteError",
    "RouteBlockedError",
]
