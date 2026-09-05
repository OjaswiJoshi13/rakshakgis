"""Exception hierarchy for Evacuation & Access Routing Engine (Chunk M4-05)."""

from typing import Any, Dict, Optional


class RoutingError(Exception):
    """Base exception for all evacuation and access routing engine errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidRouteInputError(RoutingError):
    """Raised when origin/destination coordinates or routing parameters violate domain constraints."""

    pass


class InsufficientRoutingDataError(RoutingError):
    """Raised when road network data or critical routing attributes are missing or unavailable."""

    pass


class NoFeasibleRouteError(RoutingError):
    """Raised when all available graph paths are blocked by hazards or disconnected."""

    pass


class RouteBlockedError(RoutingError):
    """Raised when a specific road segment or corridor is completely cut off by hazard events."""

    pass
