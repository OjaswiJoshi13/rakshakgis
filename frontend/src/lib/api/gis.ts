/**
 * GIS Data API Service (Chunk M5-07)
 * Centralized typed network operations for spatial datasets:
 * - Candidate Relocation Sites (Points & Boundaries)
 * - Evacuation & Access Corridors (LineStrings)
 * - Permanent & Dynamic Red Zones (MultiPolygons)
 * - Habitations / Settlements (Points & Boundaries)
 */

import { apiClient } from "./client";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
import { CandidateSiteRead } from "@/types/dashboard";
import { RedZoneRead, RouteRead, VillageRead } from "@/types/gis";

export interface CandidateSitesQueryParams {
  page?: number;
  page_size?: number;
  district_id?: number;
  status?: string;
  min_elevation_m?: number;
  max_elevation_m?: number;
  min_area_sq_m?: number;
  max_area_sq_m?: number;
  search?: string;
}

export interface RoutesQueryParams {
  page?: number;
  page_size?: number;
  origin_village_id?: number;
  destination_site_id?: number;
  route_type?: string;
  is_blocked?: boolean;
}

export interface RedZonesQueryParams {
  page?: number;
  page_size?: number;
  zone_type?: string;
  danger_level?: string;
  is_active?: boolean;
}

export interface VillagesQueryParams {
  page?: number;
  page_size?: number;
  district_id?: number;
  block_id?: number;
  is_active?: boolean;
}

/**
 * Retrieves paginated candidate relocation sites via GET /sites.
 */
export async function fetchCandidateSites(
  params?: CandidateSitesQueryParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<CandidateSiteRead>> {
  return apiClient.get<PaginatedResponse<CandidateSiteRead>>("/sites", {
    params: params as Record<string, string | number | boolean | undefined | null>,
    signal,
  });
}

/**
 * Retrieves paginated evacuation & access routes via GET /routes.
 */
export async function fetchRoutes(
  params?: RoutesQueryParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<RouteRead>> {
  return apiClient.get<PaginatedResponse<RouteRead>>("/routes", {
    params: params as Record<string, string | number | boolean | undefined | null>,
    signal,
  });
}

/**
 * Retrieves demarcated permanent & dynamic red zones via GET /red-zones.
 * Safely consumes backend M3-10 contracts.
 */
export async function fetchRedZones(
  params?: RedZonesQueryParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<RedZoneRead>> {
  return apiClient.get<PaginatedResponse<RedZoneRead>>("/red-zones", {
    params: params as Record<string, string | number | boolean | undefined | null>,
    signal,
  });
}

/**
 * Retrieves administrative village habitations via GET /villages.
 */
export async function fetchVillages(
  params?: VillagesQueryParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<VillageRead>> {
  return apiClient.get<PaginatedResponse<VillageRead>>("/villages", {
    params: params as Record<string, string | number | boolean | undefined | null>,
    signal,
  });
}

/**
 * Searches spatial GIS entities via GET /gis/search.
 */
export async function searchGis(
  q: string,
  types?: string,
  limit: number = 20,
  signal?: AbortSignal
): Promise<ResponseEnvelope<any[]>> {
  return apiClient.get<ResponseEnvelope<any[]>>("/gis/search", {
    params: { q, types, limit },
    signal,
  });
}

/**
 * Retrieves GeoJSON vector layers via GET /map/layers.
 */
export async function fetchMapLayers(
  layerType?: string,
  regionId?: string,
  signal?: AbortSignal
): Promise<ResponseEnvelope<Record<string, any>>> {
  return apiClient.get<ResponseEnvelope<Record<string, any>>>("/map/layers", {
    params: { layer_type: layerType, region_id: regionId },
    signal,
  });
}

/**
 * Retrieves comprehensive village disaster dossier via GET /villages/{id}/analysis.
 */
export async function fetchVillageAnalysis(
  id: number | string,
  signal?: AbortSignal
): Promise<ResponseEnvelope<any>> {
  return apiClient.get<ResponseEnvelope<any>>(`/villages/${id}/analysis`, { signal });
}

/**
 * Retrieves village risk score and factors via GET /villages/{id}/risk.
 */
export async function fetchVillageRisk(
  id: number | string,
  signal?: AbortSignal
): Promise<ResponseEnvelope<any>> {
  return apiClient.get<ResponseEnvelope<any>>(`/villages/${id}/risk`, { signal });
}

/**
 * Retrieves platform multi-hazard risk summary via GET /risk/summary.
 */
export async function fetchRiskSummary(
  regionId?: string,
  signal?: AbortSignal
): Promise<ResponseEnvelope<any>> {
  return apiClient.get<ResponseEnvelope<any>>("/risk/summary", {
    params: { region_id: regionId },
    signal,
  });
}

/**
 * Triggers multi-hazard dynamic risk recalculation via POST /risk/recalculate.
 */
export async function recalculateRisk(
  payload: any,
  signal?: AbortSignal
): Promise<ResponseEnvelope<any>> {
  return apiClient.post<ResponseEnvelope<any>>("/risk/recalculate", payload, { signal });
}

