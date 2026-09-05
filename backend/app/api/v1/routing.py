"""API v1 Evacuation & Access Routing router (Chunk M4-05)."""

import json
import math
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Path, Query, status
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session, joinedload

from app.api.deps import UserRole, get_current_user, require_roles
from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.profiles.registry import get_profile
from app.core.relocation.routing import (
    EvacuationRoutingEngine,
    EvacuationRoutingResult,
    RouteQuery,
    RouteStatus,
)
from app.data.synthetic.loader import get_synthetic_hazard_events
from app.models.geographic import Village
from app.models.governance import User
from app.models.hazards import HazardObservation, LandslideEvent
from app.models.relocation import CandidateSite, RelocationAssignment, Route
from app.schemas.common import (
    PaginatedResponse,
    PaginationMetadata,
    ResponseEnvelope,
)
from app.schemas.routing import (
    GeoJSONLineString,
    RouteCreate,
    RouteGenerateRequest,
    RouteRead,
    parse_geometry_to_geojson_linestring,
)

routing_router = APIRouter()


def _geojson_linestring_to_wkt(linestring_schema: GeoJSONLineString) -> WKTElement:
    """Convert GeoJSONLineString schema to PostGIS WKTElement LINESTRING (SRID 4326)."""
    pts_wkt = ", ".join(f"{pt[0]} {pt[1]}" for pt in linestring_schema.coordinates)
    return WKTElement(f"LINESTRING({pts_wkt})", srid=4326)


def _load_available_hazard_events(db: Session) -> List[Dict[str, Any]]:
    """Load active hazard events from database or fallback to synthetic pilot fixtures."""
    events: List[Dict[str, Any]] = []

    try:
        obs = db.query(HazardObservation).limit(50).all()
        for o in obs:
            sh_pt = to_shape(o.location)
            events.append(
                {
                    "id": f"OBS-{o.id}",
                    "hazard_type": o.hazard_type,
                    "severity": o.severity,
                    "location": {"type": "Point", "coordinates": [sh_pt.x, sh_pt.y]},
                    "description": o.description or "",
                }
            )
    except Exception:
        pass

    # If database hazard observations are sparse or empty, load synthetic pilot hazard events
    if not events:
        try:
            events = get_synthetic_hazard_events()
        except Exception:
            events = []

    return events


@routing_router.post(
    "/generate",
    response_model=ResponseEnvelope[EvacuationRoutingResult],
    summary="Evaluate evacuation and access routing",
    description="Calculate deterministic hazard-aware primary evacuation route and alternative corridor. Pure evaluation (zero DB mutations).",
)
def generate_evacuation_route(
    req: RouteGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute pure evaluation of evacuation routing between origin and destination."""
    origin_coord: Optional[Tuple[float, float]] = req.origin
    dest_coord: Optional[Tuple[float, float]] = req.destination
    origin_name: Optional[str] = None
    dest_name: Optional[str] = None

    # Case 1: Resolve from RelocationAssignment
    if req.assignment_id is not None:
        assignment = (
            db.query(RelocationAssignment)
            .options(
                joinedload(RelocationAssignment.village),
                joinedload(RelocationAssignment.site),
            )
            .filter(RelocationAssignment.id == req.assignment_id)
            .first()
        )
        if not assignment:
            raise NotFoundError(f"Relocation assignment with ID {req.assignment_id} not found.")

        if not assignment.village or not assignment.village.location:
            raise BadRequestError(f"Relocation assignment {req.assignment_id} is missing origin village spatial location.")
        if not assignment.site or not assignment.site.location:
            raise BadRequestError(f"Relocation assignment {req.assignment_id} is missing destination site spatial location.")

        sh_v = to_shape(assignment.village.location)
        sh_s = to_shape(assignment.site.location)
        origin_coord = (sh_v.x, sh_v.y)
        dest_coord = (sh_s.x, sh_s.y)
        origin_name = assignment.village.name
        dest_name = assignment.site.name

    # Case 2: Resolve from village_id and site_id
    elif req.origin_village_id is not None or req.destination_site_id is not None:
        if req.origin_village_id is None or req.destination_site_id is None:
            raise BadRequestError("Both origin_village_id and destination_site_id must be provided together.")

        village = db.query(Village).filter(Village.id == req.origin_village_id).first()
        if not village:
            raise NotFoundError(f"Village with ID {req.origin_village_id} not found.")

        site = db.query(CandidateSite).filter(CandidateSite.id == req.destination_site_id).first()
        if not site:
            raise NotFoundError(f"Candidate site with ID {req.destination_site_id} not found.")

        sh_v = to_shape(village.location)
        sh_s = to_shape(site.location)
        origin_coord = (sh_v.x, sh_v.y)
        dest_coord = (sh_s.x, sh_s.y)
        origin_name = village.name
        dest_name = site.name

    # Case 3: Raw coordinates must be present if no entity IDs given
    if origin_coord is None or dest_coord is None:
        raise BadRequestError(
            "Either explicit origin and destination coordinates, origin_village_id and destination_site_id, "
            "or assignment_id must be provided."
        )

    # Resolve regional configuration profile
    pid = req.region_profile_id or "himalayan_pilot"
    try:
        profile = get_profile(pid)
    except Exception as e:
        raise NotFoundError(f"Regional profile '{pid}' not found: {str(e)}")

    # Load hazard events for hazard-aware routing
    if req.hazard_context and "hazard_events" in req.hazard_context:
        hazard_events = req.hazard_context["hazard_events"]
    else:
        hazard_events = _load_available_hazard_events(db)

    engine = EvacuationRoutingEngine.from_region_profile(profile, hazard_events=hazard_events)

    query = RouteQuery(
        origin=origin_coord,
        destination=dest_coord,
        assignment_id=req.assignment_id,
        origin_village_id=req.origin_village_id,
        destination_site_id=req.destination_site_id,
        region_profile_id=pid,
        routing_mode=req.routing_mode,
        require_alternative=req.require_alternative,
        hazard_context=req.hazard_context,
    )

    result = engine.route(query)
    if origin_name:
        result.origin_village_name = origin_name
    if dest_name:
        result.destination_site_name = dest_name

    return ResponseEnvelope(success=True, data=result)


@routing_router.post(
    "",
    response_model=ResponseEnvelope[RouteRead],
    status_code=status.HTTP_201_CREATED,
    summary="Persist an evacuation route",
    description="Store an evacuation or access route in the database. Requires ADMIN or DISTRICT_OFFICER role.",
)
def create_route(
    route_in: RouteCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
):
    """Persist an evacuation route record."""
    village = db.query(Village).filter(Village.id == route_in.origin_village_id).first()
    if not village:
        raise NotFoundError(f"Village with ID {route_in.origin_village_id} does not exist.")

    site = db.query(CandidateSite).filter(CandidateSite.id == route_in.destination_site_id).first()
    if not site:
        raise NotFoundError(f"Candidate site with ID {route_in.destination_site_id} does not exist.")

    wkt_path = _geojson_linestring_to_wkt(route_in.path)

    route = Route(
        name=route_in.name,
        origin_village_id=route_in.origin_village_id,
        destination_site_id=route_in.destination_site_id,
        path=wkt_path,
        distance_km=route_in.distance_km,
        estimated_travel_time_min=route_in.estimated_travel_time_min,
        route_type=route_in.route_type,
        safety_score=route_in.safety_score,
        is_blocked=route_in.is_blocked,
        blockage_reason=route_in.blockage_reason,
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    read_model = RouteRead(
        id=route.id,
        name=route.name,
        origin_village_id=route.origin_village_id,
        origin_village_name=village.name,
        destination_site_id=route.destination_site_id,
        destination_site_name=site.name,
        path=route_in.path,
        distance_km=route.distance_km,
        estimated_travel_time_min=route.estimated_travel_time_min,
        route_type=route.route_type,
        safety_score=route.safety_score,
        is_blocked=route.is_blocked,
        blockage_reason=route.blockage_reason,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )
    return ResponseEnvelope(success=True, data=read_model)


@routing_router.get(
    "",
    response_model=PaginatedResponse[RouteRead],
    summary="List persisted routes",
    description="Retrieve paginated persisted evacuation routes with optional filters.",
)
def list_routes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    origin_village_id: Optional[int] = Query(None, description="Filter by origin village ID"),
    destination_site_id: Optional[int] = Query(None, description="Filter by destination site ID"),
    route_type: Optional[str] = Query(None, description="Filter by route type (evacuation, alternate, relief)"),
    is_blocked: Optional[bool] = Query(None, description="Filter by blockage status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve paginated routes."""
    query = (
        db.query(Route)
        .options(
            joinedload(Route.origin_village),
            joinedload(Route.destination_site),
        )
    )

    if origin_village_id is not None:
        query = query.filter(Route.origin_village_id == origin_village_id)
    if destination_site_id is not None:
        query = query.filter(Route.destination_site_id == destination_site_id)
    if route_type is not None:
        query = query.filter(Route.route_type == route_type.lower().strip())
    if is_blocked is not None:
        query = query.filter(Route.is_blocked == is_blocked)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    records = (
        query.order_by(Route.created_at.desc(), Route.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: List[RouteRead] = []
    for r in records:
        geo = parse_geometry_to_geojson_linestring(r.path)
        items.append(
            RouteRead(
                id=r.id,
                name=r.name,
                origin_village_id=r.origin_village_id,
                origin_village_name=r.origin_village.name if r.origin_village else None,
                destination_site_id=r.destination_site_id,
                destination_site_name=r.destination_site.name if r.destination_site else None,
                path=geo or GeoJSONLineString(type="LineString", coordinates=[(0.0, 0.0), (0.0, 0.0)]),
                distance_km=r.distance_km,
                estimated_travel_time_min=r.estimated_travel_time_min,
                route_type=r.route_type,
                safety_score=r.safety_score,
                is_blocked=r.is_blocked,
                blockage_reason=r.blockage_reason,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )

    return PaginatedResponse(
        success=True,
        data=items,
        pagination=PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@routing_router.get(
    "/{id}",
    response_model=ResponseEnvelope[RouteRead],
    summary="Get route by ID",
    description="Retrieve details of a persisted route by its database ID.",
)
def get_route(
    id: int = Path(..., ge=1, description="Route database ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve route by ID."""
    route = (
        db.query(Route)
        .options(
            joinedload(Route.origin_village),
            joinedload(Route.destination_site),
        )
        .filter(Route.id == id)
        .first()
    )

    if not route:
        raise NotFoundError(f"Route with ID {id} was not found.")

    geo = parse_geometry_to_geojson_linestring(route.path)

    read_model = RouteRead(
        id=route.id,
        name=route.name,
        origin_village_id=route.origin_village_id,
        origin_village_name=route.origin_village.name if route.origin_village else None,
        destination_site_id=route.destination_site_id,
        destination_site_name=route.destination_site.name if route.destination_site else None,
        path=geo or GeoJSONLineString(type="LineString", coordinates=[(0.0, 0.0), (0.0, 0.0)]),
        distance_km=route.distance_km,
        estimated_travel_time_min=route.estimated_travel_time_min,
        route_type=route.route_type,
        safety_score=route.safety_score,
        is_blocked=route.is_blocked,
        blockage_reason=route.blockage_reason,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )
    return ResponseEnvelope(success=True, data=read_model)
