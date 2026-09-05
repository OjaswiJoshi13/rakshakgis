"""GIS and spatial geometry utilities for Permanent Red Zone Demarcation (Chunk M3-10)."""

import hashlib
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pyproj
from shapely import make_valid
from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union

from app.core.profiles.models import DangerLevel
from app.core.risk.red_zone.contracts import (
    PermanentRedZoneCandidate,
    PermanentRedZoneExplainability,
    RedZoneStatus,
    RedZoneType,
    TriggerAudit,
)
from app.core.risk.red_zone.errors import RedZoneConfigError, SpatialGeometryError


WGS84_CRS = pyproj.CRS("EPSG:4326")
GEOD = pyproj.Geod(ellps="WGS84")


def create_geodesic_buffer(
    point_or_lon: Union[Point, float],
    lat_or_buffer: Optional[float] = None,
    buffer_m: Optional[float] = None,
    *,
    buffer_distance_m: Optional[float] = None,
) -> MultiPolygon:
    """Create a geodesic circular buffer in meters around a WGS84 point, returned as a MultiPolygon in EPSG:4326.

    Can be called flexibly:
        create_geodesic_buffer(lon, lat, buffer_m)
        create_geodesic_buffer(point, buffer_distance_m=500.0)
        create_geodesic_buffer(point, 500.0)
    """
    if isinstance(point_or_lon, Point):
        lon = float(point_or_lon.x)
        lat = float(point_or_lon.y)
        dist = buffer_distance_m if buffer_distance_m is not None else lat_or_buffer
    else:
        lon = float(point_or_lon)
        lat = float(lat_or_buffer) if lat_or_buffer is not None else float("nan")
        dist = buffer_distance_m if buffer_distance_m is not None else buffer_m

    if dist is None:
        raise SpatialGeometryError("Missing buffer distance parameter.")
    if math.isnan(dist) or math.isinf(dist) or dist <= 0.0:
        raise SpatialGeometryError(f"Invalid buffer distance: {dist}. Buffer distance must be positive.")
    if math.isnan(lon) or math.isinf(lon) or not (-180.0 <= lon <= 180.0):
        raise SpatialGeometryError(f"Invalid longitude for buffer: {lon}. Must be within [-180.0, 180.0].")
    if math.isnan(lat) or math.isinf(lat) or not (-90.0 <= lat <= 90.0):
        raise SpatialGeometryError(f"Invalid latitude for buffer: {lat}. Must be within [-90.0, 90.0]. Invalid point coordinates.")

    # Centered azimuthal equidistant projection for metric accuracy
    aeqd_crs = pyproj.CRS(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    proj_aeqd_to_wgs84 = pyproj.Transformer.from_crs(aeqd_crs, WGS84_CRS, always_xy=True).transform

    point_local = Point(0.0, 0.0)
    # 64 quad segments for smooth circular boundary
    buffered_local = point_local.buffer(dist, quad_segs=16)

    buffered_wgs84 = transform(proj_aeqd_to_wgs84, buffered_local)
    if not buffered_wgs84.is_valid:
        buffered_wgs84 = make_valid(buffered_wgs84)

    return normalize_to_multipolygon(buffered_wgs84)


def normalize_to_multipolygon(geom: Any) -> MultiPolygon:
    """Normalize any Polygon or MultiPolygon representation into a valid Shapely MultiPolygon in EPSG:4326."""
    if geom is None:
        raise SpatialGeometryError("Cannot normalize None geometry.")

    if isinstance(geom, dict):
        try:
            shapely_geom = shape(geom)
        except Exception as e:
            raise SpatialGeometryError(f"Failed to parse GeoJSON geometry: {e}") from e
    else:
        shapely_geom = geom

    if not hasattr(shapely_geom, "geom_type"):
        raise SpatialGeometryError(f"Unrecognized geometry type: {type(geom)}")

    if not shapely_geom.is_valid:
        shapely_geom = make_valid(shapely_geom)

    if shapely_geom.geom_type == "Polygon":
        return MultiPolygon([shapely_geom])
    elif shapely_geom.geom_type == "MultiPolygon":
        return shapely_geom
    elif shapely_geom.geom_type == "GeometryCollection":
        polys = [g for g in shapely_geom.geoms if g.geom_type == "Polygon"]
        if not polys:
            raise SpatialGeometryError("GeometryCollection contains no polygonal components.")
        return MultiPolygon(polys)
    else:
        raise SpatialGeometryError(
            f"Expected Polygon or MultiPolygon, got {shapely_geom.geom_type}. "
            "Point geometries must be buffered via create_geodesic_buffer() first."
        )


def calculate_geodesic_area_sq_km(geom: Union[Polygon, MultiPolygon, Dict[str, Any]]) -> float:
    """Calculate geodesic (ellipsoidal) area in square kilometers for an EPSG:4326 polygon/multipolygon."""
    mp = normalize_to_multipolygon(geom)
    total_area_m2 = 0.0

    for poly in mp.geoms:
        # Geod.geometry_area_perimeter returns (area, perimeter)
        area_m2, _ = GEOD.geometry_area_perimeter(poly)
        total_area_m2 += abs(area_m2)

    return total_area_m2 / 1_000_000.0


def dissolve_overlapping_candidates(
    candidates: Sequence[PermanentRedZoneCandidate],
    default_danger_level: Optional[DangerLevel] = None,
) -> List[PermanentRedZoneCandidate]:
    """Dissolve overlapping proposed permanent red zones into contiguous MultiPolygons.

    Preserves full source provenance, contributing village IDs, and trigger audits.
    Non-proposed or non-demarcated candidates are preserved unchanged.
    """
    if not candidates:
        return []

    proposed = [c for c in candidates if c.status == RedZoneStatus.PROPOSED and c.geometry is not None]
    non_proposed = [c for c in candidates if c not in proposed]

    if not proposed:
        return list(candidates)

    # Convert all geometries to shapely MultiPolygon
    items: List[Tuple[PermanentRedZoneCandidate, MultiPolygon]] = []
    for c in proposed:
        mp = normalize_to_multipolygon(c.geometry)
        items.append((c, mp))

    # Graph-based connected components for spatial intersection
    n = len(items)
    adj: List[List[int]] = [[] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            geom_i = items[i][1]
            geom_j = items[j][1]
            if geom_i.intersects(geom_j):
                adj[i].append(j)
                adj[j].append(i)

    visited = [False] * n
    dissolved_results: List[PermanentRedZoneCandidate] = []

    for i in range(n):
        if visited[i]:
            continue

        # BFS / DFS to find connected component
        component_indices: List[int] = []
        queue = [i]
        visited[i] = True

        while queue:
            curr = queue.pop(0)
            component_indices.append(curr)
            for neighbor in adj[curr]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)

        intersecting = [items[idx][0] for idx in component_indices]
        geoms_to_union = [items[idx][1] for idx in component_indices]

        # Union geometries
        if len(geoms_to_union) == 1:
            union_geom = geoms_to_union[0]
        else:
            union_geom = unary_union(geoms_to_union)

        if not union_geom.is_valid:
            union_geom = make_valid(union_geom)
        comp_mp = normalize_to_multipolygon(union_geom)

        if len(intersecting) == 1:
            single = intersecting[0]
            # Strict DangerLevel resolution order:
            # 1. Explicit default_danger_level supplied by caller
            # 2. Existing danger_level from the proposed candidate
            # 3. If neither exists, raise an explicit configuration/contract error
            resolved_danger_level = default_danger_level or single.danger_level
            if resolved_danger_level is None:
                raise RedZoneConfigError(
                    f"Unable to resolve danger_level for candidate '{single.candidate_id or single.zone_id}': "
                    "neither default_danger_level nor an existing candidate danger_level was provided. "
                    "A danger_level must be explicitly supplied under the red zone contract."
                )

            # Ensure geometry is MultiPolygon and contributing_village_ids populated
            v_id = single.explainability.source_village_ids[0] if single.explainability.source_village_ids else (single.metadata_json.get("village_id") or "UNKNOWN")
            updated = single.model_copy(
                update={
                    "geometry": comp_mp,
                    "contributing_village_ids": single.contributing_village_ids or [v_id],
                    "danger_level": resolved_danger_level,
                }
            )
            dissolved_results.append(updated)
        else:
            # Overlapping candidates merged
            village_ids = sorted(
                list(
                    set(
                        v_id
                        for c in intersecting
                        for v_id in (c.contributing_village_ids or c.explainability.source_village_ids or [c.metadata_json.get("village_id")])
                        if v_id
                    )
                )
            )
            provenance_dict: Dict[str, Any] = {}
            provenance_list: List[Dict[str, Any]] = []
            trigger_audits_list: List[TriggerAudit] = []

            for c in intersecting:
                provenance_list.extend(c.explainability.source_provenance)
                if c.explainability.trigger_audit:
                    trigger_audits_list.append(c.explainability.trigger_audit)
                for v in (c.contributing_village_ids or c.explainability.source_village_ids):
                    if v and v not in provenance_dict:
                        provenance_dict[v] = c.explainability.source_village_provenance.get(v) or c.metadata_json

            names = sorted(list(set(c.name for c in intersecting)))
            zone_types = set(c.zone_type for c in intersecting if c.zone_type is not None)
            merged_type = (
                RedZoneType.COMPOUND_DANGER
                if len(zone_types) > 1
                else next(iter(zone_types), RedZoneType.LANDSLIDE_DANGER)
            )

            # Deterministic hash for dissolved zone ID
            id_seed = "-".join(sorted(c.zone_id or c.candidate_id for c in intersecting))
            hash_suffix = hashlib.sha256(id_seed.encode("utf-8")).hexdigest()[:8].upper()
            dissolved_zone_id = f"PRZ-DISSOLVED-{hash_suffix}"
            dissolved_name = f"Dissolved Permanent Red Zone ({', '.join(names)})"
            dissolved_area = calculate_geodesic_area_sq_km(comp_mp)

            subsidence_trig = any(c.explainability.active_subsidence_triggered for c in intersecting)
            compound_trig = any(c.explainability.compound_hazard_triggered for c in intersecting)

            trigger_summary = (
                f"Continuous high-risk spatial perimeter dissolved across {len(intersecting)} "
                f"overlapping settlements: {', '.join(village_ids)}."
            )

            merged_audit = TriggerAudit(
                village_id=dissolved_zone_id,
                active_subsidence_triggered=subsidence_trig,
                compound_landslide_triggered=compound_trig,
                compound_hazard_triggered=compound_trig,
                slope_threshold_deg=intersecting[0].explainability.trigger_audit.slope_threshold_deg if intersecting[0].explainability.trigger_audit else 35.0,
                observed_slope_deg=max(
                    (
                        (c.explainability.trigger_audit.observed_slope_deg or 0.0)
                        for c in intersecting
                        if c.explainability and c.explainability.trigger_audit
                    ),
                    default=0.0,
                ),
                slope_threshold_met=any(c.explainability.slope_threshold_met for c in intersecting),
                landslide_threshold_count=intersecting[0].explainability.trigger_audit.landslide_threshold_count if (intersecting[0].explainability and intersecting[0].explainability.trigger_audit) else 1,
                observed_landslide_count=max(
                    (
                        (c.explainability.trigger_audit.observed_landslide_count or 0)
                        for c in intersecting
                        if c.explainability and c.explainability.trigger_audit
                    ),
                    default=0,
                ),
                historical_landslides_threshold_met=any(c.explainability.historical_landslides_threshold_met for c in intersecting),
                active_subsidence_observed=subsidence_trig,
                risk_corroboration="Merged multi-settlement dissolved perimeter.",
                risk_band_corroborated=any(c.explainability.risk_band_corroborated for c in intersecting),
                missing_indicators=[],
            )

            explainability = PermanentRedZoneExplainability(
                decision_reason=trigger_summary,
                trigger_summary=trigger_summary,
                trigger_audit=merged_audit,
                trigger_audits=trigger_audits_list,
                active_subsidence_triggered=subsidence_trig,
                compound_hazard_triggered=compound_trig,
                slope_threshold_met=any(c.explainability.slope_threshold_met for c in intersecting),
                historical_landslides_threshold_met=any(c.explainability.historical_landslides_threshold_met for c in intersecting),
                risk_band_corroborated=any(c.explainability.risk_band_corroborated for c in intersecting),
                monitoring_recommended=False,
                missing_required_indicators=[],
                source_village_ids=village_ids,
                source_village_provenance=provenance_dict,
                source_provenance=provenance_list,
                is_dissolved=True,
                dissolved_zone_count=len(intersecting),
                profile_id=intersecting[0].explainability.profile_id,
                buffer_applied_m=intersecting[0].explainability.buffer_applied_m,
            )

            # Strict DangerLevel resolution order without unapproved fallbacks:
            # 1. Explicit default_danger_level supplied by caller
            # 2. Existing danger_level from intersecting proposed candidates
            # 3. If neither exists, raise an explicit configuration/contract error
            resolved_danger_level = default_danger_level
            if resolved_danger_level is None:
                for c in intersecting:
                    if c.danger_level is not None:
                        resolved_danger_level = c.danger_level
                        break

            if resolved_danger_level is None:
                raise RedZoneConfigError(
                    f"Unable to resolve danger_level for dissolved candidate '{dissolved_zone_id}': "
                    "neither default_danger_level nor an existing candidate danger_level was provided. "
                    "A danger_level must be explicitly supplied under the red zone contract."
                )

            merged_candidate = PermanentRedZoneCandidate(
                candidate_id=dissolved_zone_id,
                zone_id=dissolved_zone_id,
                name=dissolved_name,
                status=RedZoneStatus.PROPOSED,
                zone_type=merged_type,
                danger_level=resolved_danger_level,
                geometry=comp_mp,
                srid=4326,
                area_sq_km=dissolved_area,
                buffer_distance_applied_m=intersecting[0].buffer_distance_applied_m,
                contributing_village_ids=village_ids,
                is_candidate=True,
                is_active=False,
                declared_by_officer_id=None,
                declared_at=None,
                explainability=explainability,
                metadata_json={
                    "dissolved_from": [c.zone_id or c.candidate_id for c in intersecting],
                    "contributing_settlement_count": len(intersecting),
                },
            )
            dissolved_results.append(merged_candidate)

    # Return dissolved proposed candidates along with untouched non-proposed candidates
    return dissolved_results + non_proposed
