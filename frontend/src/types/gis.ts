/**
 * GIS and GeoJSON Domain Types & Layer Configuration
 * Strictly typed definitions conforming to RFC 7946 GeoJSON and backend API models.
 */

import { CandidateSiteRead } from "@/types/dashboard";

export type GeoJSONPosition = [number, number] | [number, number, number];

export interface GeoJSONPointGeometry {
  type: "Point";
  coordinates: [number, number];
}

export interface GeoJSONLineStringGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export interface GeoJSONPolygonGeometry {
  type: "Polygon";
  coordinates: [number, number][][];
}

export interface GeoJSONMultiPolygonGeometry {
  type: "MultiPolygon";
  coordinates: [number, number][][][];
}

export type GeoJSONGeometry =
  | GeoJSONPointGeometry
  | GeoJSONLineStringGeometry
  | GeoJSONPolygonGeometry
  | GeoJSONMultiPolygonGeometry;

export interface GeoJSONFeature<
  G extends GeoJSONGeometry = GeoJSONGeometry,
  P extends Record<string, unknown> = Record<string, unknown>
> {
  type: "Feature";
  id?: string | number;
  geometry: G;
  properties: P;
}

export interface GeoJSONFeatureCollection<
  G extends GeoJSONGeometry = GeoJSONGeometry,
  P extends Record<string, unknown> = Record<string, unknown>
> {
  type: "FeatureCollection";
  features: GeoJSONFeature<G, P>[];
}

/**
 * Persisted route schema conforming to M4-05 backend router.
 */
export interface RouteRead {
  id: number;
  name: string;
  origin_village_id: number | null;
  origin_village_name: string | null;
  destination_site_id: number | null;
  destination_site_name: string | null;
  path: GeoJSONLineStringGeometry;
  distance_km: number;
  estimated_travel_time_min: number | null;
  route_type: "evacuation" | "alternate" | "relief" | string;
  is_blocked: boolean;
  blockage_reason: string | null;
  elevation_gain_m: number | null;
  max_slope_deg: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Red Zone schema conforming to M3-10 backend engine and PostgreSQL red_zones table.
 */
export interface RedZoneRead {
  id: string | number;
  name: string;
  zone_type: "landslide_danger" | "active_subsidence" | "flood_inundation" | "compound_danger" | string;
  danger_level: "very_high" | "critical" | "uninhabitable" | string;
  geometry: GeoJSONMultiPolygonGeometry | GeoJSONPolygonGeometry;
  area_sq_km?: number | null;
  is_active?: boolean;
  declared_by_officer_id?: number | null;
  declared_at?: string | null;
  contributing_village_ids?: string[];
  explainability?: {
    decision_reason?: string;
    trigger_summary?: string;
    governance_notice?: string;
    is_dissolved?: boolean;
  };
  created_at?: string;
  updated_at?: string;
}

/**
 * Permanent Red Zone Candidate result envelope conforming to M3-10 PermanentRedZoneCandidate.
 */
export interface PermanentRedZoneCandidate {
  candidate_id?: string;
  zone_id?: string;
  name: string;
  status: "proposed" | "not_demarcated" | "monitor" | "insufficient_data" | string;
  zone_type?: "landslide_danger" | "active_subsidence" | "flood_inundation" | "compound_danger" | string;
  danger_level?: "very_high" | "critical" | "uninhabitable" | string;
  geometry?: GeoJSONMultiPolygonGeometry | GeoJSONPolygonGeometry | null;
  area_sq_km?: number | null;
  contributing_village_ids?: string[];
  is_candidate?: boolean;
  is_active?: boolean;
  explainability?: {
    decision_reason?: string;
    trigger_summary?: string;
    governance_notice?: string;
  };
}

/**
 * Administrative village schema conforming to PostgreSQL villages table.
 */
export interface VillageRead {
  id: number;
  name: string;
  census_code?: string | null;
  block_id?: number;
  location: GeoJSONPointGeometry;
  boundary?: GeoJSONPolygonGeometry | null;
  elevation_m?: number | null;
  slope_deg?: number | null;
  is_active?: boolean;
}

export type LayerCategory =
  | "candidate_sites"
  | "routes"
  | "habitations"
  | "red_zones"
  | "hazards";

export type LayerStatus = "available" | "unavailable" | "pending_dependency";

export interface MapLayerConfig {
  id: string;
  name: string;
  category: LayerCategory;
  description: string;
  sourceId: string;
  layerType: "circle" | "line" | "fill";
  paint: Record<string, unknown>;
  layout?: Record<string, unknown>;
  defaultVisible: boolean;
  status: LayerStatus;
  pendingNote?: string;
  geometryType: "Point" | "LineString" | "Polygon" | "MultiPolygon";
}

export interface SelectedFeatureInfo {
  id: string | number;
  layerId: string;
  layerCategory: LayerCategory;
  geometryType: string;
  coordinates?: [number, number];
  properties: Record<string, unknown>;
}

/**
 * Validates whether a position tuple contains valid WGS84 coordinate numbers [lon, lat].
 */
export function isValidPosition(pos: unknown): pos is [number, number] {
  if (!Array.isArray(pos) || pos.length < 2) return false;
  const [lon, lat] = pos;
  return (
    typeof lon === "number" &&
    typeof lat === "number" &&
    Number.isFinite(lon) &&
    Number.isFinite(lat) &&
    lon >= -180 &&
    lon <= 180 &&
    lat >= -90 &&
    lat <= 90
  );
}

/**
 * Validates whether a linear ring conforms to RFC 7946:
 * - At least 4 positions
 * - Every position is valid [lon, lat]
 * - First position is equivalent to the final position (ring closure)
 */
export function isValidLinearRing(ring: unknown): ring is [number, number][] {
  if (!Array.isArray(ring) || ring.length < 4) return false;
  if (!ring.every(isValidPosition)) return false;
  const first = ring[0];
  const last = ring[ring.length - 1];
  return first[0] === last[0] && first[1] === last[1];
}

/**
 * Defensively guards against malformed geometry.
 */
export function isValidGeometry(geom: unknown): geom is GeoJSONGeometry {
  if (!geom || typeof geom !== "object") return false;
  const g = geom as { type?: string; coordinates?: unknown };
  if (!g.type || !g.coordinates) return false;

  switch (g.type) {
    case "Point":
      return isValidPosition(g.coordinates);
    case "LineString":
      return (
        Array.isArray(g.coordinates) &&
        g.coordinates.length >= 2 &&
        g.coordinates.every(isValidPosition)
      );
    case "Polygon":
      return (
        Array.isArray(g.coordinates) &&
        g.coordinates.length >= 1 &&
        g.coordinates.every(isValidLinearRing)
      );
    case "MultiPolygon":
      return (
        Array.isArray(g.coordinates) &&
        g.coordinates.every(
          (poly) =>
            Array.isArray(poly) &&
            poly.length >= 1 &&
            poly.every(isValidLinearRing)
        )
      );
    default:
      return false;
  }
}

/**
 * Validates a GeoJSON Feature.
 */
export function isValidFeature(feat: unknown): feat is GeoJSONFeature {
  if (!feat || typeof feat !== "object") return false;
  const f = feat as { type?: string; geometry?: unknown; properties?: unknown };
  return f.type === "Feature" && isValidGeometry(f.geometry);
}

/**
 * Calculates a standard bounding box [[minLon, minLat], [maxLon, maxLat]]
 * from a list of valid features for region-agnostic viewport fitting.
 */
export function calculateBounds(
  features: GeoJSONFeature[]
): [[number, number], [number, number]] | null {
  if (!features || features.length === 0) return null;

  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;
  let validPointsCount = 0;

  const processCoord = (lon: number, lat: number) => {
    if (lon < minLon) minLon = lon;
    if (lat < minLat) minLat = lat;
    if (lon > maxLon) maxLon = lon;
    if (lat > maxLat) maxLat = lat;
    validPointsCount++;
  };

  for (const feat of features) {
    if (!feat.geometry) continue;
    const geom = feat.geometry;

    if (geom.type === "Point" && isValidPosition(geom.coordinates)) {
      processCoord(geom.coordinates[0], geom.coordinates[1]);
    } else if (geom.type === "LineString" && Array.isArray(geom.coordinates)) {
      for (const pt of geom.coordinates) {
        if (isValidPosition(pt)) processCoord(pt[0], pt[1]);
      }
    } else if (geom.type === "Polygon" && Array.isArray(geom.coordinates)) {
      for (const ring of geom.coordinates) {
        for (const pt of ring) {
          if (isValidPosition(pt)) processCoord(pt[0], pt[1]);
        }
      }
    } else if (geom.type === "MultiPolygon" && Array.isArray(geom.coordinates)) {
      for (const poly of geom.coordinates) {
        if (Array.isArray(poly)) {
          for (const ring of poly) {
            if (Array.isArray(ring)) {
              for (const pt of ring) {
                if (isValidPosition(pt)) processCoord(pt[0], pt[1]);
              }
            }
          }
        }
      }
    }
  }

  if (validPointsCount === 0 || !Number.isFinite(minLon)) return null;

  // Add slight padding margin if points are identical to prevent zero-size box
  if (minLon === maxLon && minLat === maxLat) {
    return [
      [minLon - 0.05, minLat - 0.05],
      [maxLon + 0.05, maxLat + 0.05],
    ];
  }

  return [
    [minLon, minLat],
    [maxLon, maxLat],
  ];
}

/**
 * Transforms CandidateSiteRead backend models into GeoJSON FeatureCollection.
 */
export function candidateSitesToGeoJSON(
  sites: CandidateSiteRead[]
): GeoJSONFeatureCollection<GeoJSONPointGeometry> {
  const validFeatures: GeoJSONFeature<GeoJSONPointGeometry>[] = [];

  for (const s of sites) {
    if (s.location && isValidPosition(s.location.coordinates)) {
      validFeatures.push({
        type: "Feature",
        id: s.id,
        geometry: {
          type: "Point",
          coordinates: [s.location.coordinates[0], s.location.coordinates[1]],
        },
        properties: {
          id: s.id,
          name: s.name,
          district_id: s.district_id,
          elevation_m: s.elevation_m,
          terrain_slope_deg: s.terrain_slope_deg,
          area_sq_m: s.area_sq_m,
          status: s.status,
          created_at: s.created_at,
          category: "candidate_sites",
        },
      });
    }
  }

  return {
    type: "FeatureCollection",
    features: validFeatures,
  };
}

/**
 * Transforms CandidateSiteRead polygon boundaries into GeoJSON FeatureCollection.
 */
export function candidateSiteBoundariesToGeoJSON(
  sites: CandidateSiteRead[]
): GeoJSONFeatureCollection<GeoJSONPolygonGeometry> {
  const validFeatures: GeoJSONFeature<GeoJSONPolygonGeometry>[] = [];

  for (const s of sites) {
    if (s.boundary && isValidGeometry(s.boundary)) {
      validFeatures.push({
        type: "Feature",
        id: `boundary-${s.id}`,
        geometry: s.boundary as GeoJSONPolygonGeometry,
        properties: {
          site_id: s.id,
          site_name: s.name,
          category: "candidate_sites_boundary",
        },
      });
    }
  }

  return {
    type: "FeatureCollection",
    features: validFeatures,
  };
}

/**
 * Transforms RouteRead backend models into GeoJSON FeatureCollection.
 */
export function routesToGeoJSON(
  routes: RouteRead[]
): GeoJSONFeatureCollection<GeoJSONLineStringGeometry> {
  const validFeatures: GeoJSONFeature<GeoJSONLineStringGeometry>[] = [];

  for (const r of routes) {
    if (r.path && isValidGeometry(r.path)) {
      validFeatures.push({
        type: "Feature",
        id: r.id,
        geometry: r.path,
        properties: {
          id: r.id,
          name: r.name,
          route_type: r.route_type,
          distance_km: r.distance_km,
          estimated_travel_time_min: r.estimated_travel_time_min,
          is_blocked: r.is_blocked,
          blockage_reason: r.blockage_reason,
          origin_village_name: r.origin_village_name,
          destination_site_name: r.destination_site_name,
          elevation_gain_m: r.elevation_gain_m,
          max_slope_deg: r.max_slope_deg,
          category: "routes",
        },
      });
    }
  }

  return {
    type: "FeatureCollection",
    features: validFeatures,
  };
}

/**
 * Transforms RedZoneRead or PermanentRedZoneCandidate backend models into GeoJSON FeatureCollection.
 * Consumes backend-calculated danger levels, area, and geometries without client recalculation.
 * Safely skips malformed or missing geometries; never fabricates coordinates or fallback to [0,0].
 */
export function redZonesToGeoJSON(
  redZones: (RedZoneRead | PermanentRedZoneCandidate)[]
): GeoJSONFeatureCollection<GeoJSONMultiPolygonGeometry | GeoJSONPolygonGeometry> {
  const validFeatures: GeoJSONFeature<GeoJSONMultiPolygonGeometry | GeoJSONPolygonGeometry>[] = [];

  for (const rz of redZones) {
    if (!rz) continue;
    const geom = rz.geometry;
    if (geom && isValidGeometry(geom) && (geom.type === "Polygon" || geom.type === "MultiPolygon")) {
      const id =
        "id" in rz && rz.id !== undefined && rz.id !== null
          ? rz.id
          : "candidate_id" in rz && rz.candidate_id
          ? rz.candidate_id
          : "zone_id" in rz && rz.zone_id
          ? rz.zone_id
          : `red-zone-${validFeatures.length + 1}`;

      validFeatures.push({
        type: "Feature",
        id,
        geometry: geom as GeoJSONMultiPolygonGeometry | GeoJSONPolygonGeometry,
        properties: {
          id,
          name: rz.name,
          zone_type: rz.zone_type || "landslide_danger",
          danger_level: rz.danger_level || "critical",
          area_sq_km: rz.area_sq_km ?? null,
          is_active: rz.is_active ?? false,
          contributing_village_ids: rz.contributing_village_ids || [],
          governance_notice:
            rz.explainability?.governance_notice ||
            "PROPOSED CANDIDATE ONLY: Statutory legal declaration requires officer review (M6-08 workflow).",
          decision_reason: rz.explainability?.decision_reason || "",
          category: "red_zones",
        },
      });
    }
  }

  return {
    type: "FeatureCollection",
    features: validFeatures,
  };
}

/**
 * Transforms VillageRead backend models into GeoJSON FeatureCollection.
 * Validates Point coordinates and skips invalid/missing entries without fake coordinates.
 */
export function villagesToGeoJSON(
  villages: VillageRead[]
): GeoJSONFeatureCollection<GeoJSONPointGeometry> {
  const validFeatures: GeoJSONFeature<GeoJSONPointGeometry>[] = [];

  for (const v of villages) {
    if (!v) continue;
    if (v.location && isValidPosition(v.location.coordinates)) {
      validFeatures.push({
        type: "Feature",
        id: v.id,
        geometry: {
          type: "Point",
          coordinates: [v.location.coordinates[0], v.location.coordinates[1]],
        },
        properties: {
          id: v.id,
          name: v.name,
          census_code: v.census_code ?? null,
          block_id: v.block_id ?? null,
          elevation_m: v.elevation_m ?? null,
          slope_deg: v.slope_deg ?? null,
          is_active: v.is_active ?? true,
          category: "habitations",
        },
      });
    }
  }

  return {
    type: "FeatureCollection",
    features: validFeatures,
  };
}
