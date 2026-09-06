/**
 * Dashboard & Domain API Read Types
 * Strictly mirrors backend Chunk M2-05, M3-13, M4-01, M4-04, and M4-06 Pydantic schemas.
 */

export interface FreshnessEvaluationRead {
  status: "FRESH" | "STALE" | "UNAVAILABLE" | "UNKNOWN" | "CLOCK_SKEW";
  age_seconds: number | null;
  threshold_seconds: number;
  is_usable: boolean;
  reason: string;
  evaluated_at: string;
}

export interface DataSourceTelemetryRead {
  source_id: number;
  name: string;
  source_type: string;
  provider: string;
  provider_id: string | null;
  category: string | null;
  provider_mode: string;
  provider_health: "HEALTHY" | "DEGRADED" | "UNAVAILABLE";
  freshness: FreshnessEvaluationRead;
  last_successful_update: string | null;
  last_attempted_update: string | null;
  latest_run_status: string | null;
  is_synthetic: boolean;
  is_active: boolean;
  records_ingested_total: number;
  records_failed_total: number;
}

export interface TelemetryOverviewRead {
  total_sources: number;
  healthy_count: number;
  degraded_count: number;
  unavailable_count: number;
  fresh_count: number;
  stale_count: number;
  unknown_count: number;
  synthetic_count: number;
  evaluated_at: string;
}

export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface CandidateSiteRead {
  id: number;
  name: string;
  district_id: number;
  location: GeoJSONPoint;
  boundary?: { type: "Polygon"; coordinates: number[][][] } | null;
  area_sq_m: number | null;
  terrain_slope_deg: number | null;
  elevation_m: number | null;
  status: "proposed" | "approved" | "rejected" | "active" | string;
  created_at: string;
  updated_at: string;
}

export interface RelocationAssignmentRead {
  id: number;
  village_id: number;
  village_name: string | null;
  candidate_site_id: number;
  candidate_site_name: string | null;
  assigned_households: number;
  assigned_population: number | null;
  status: string;
  approved_by_officer_id: number | null;
  assigned_at: string;
  updated_at: string;
}

export interface ScenarioParameters {
  rainfall_multiplier: number;
  seismic_intensity_mmi: number | null;
  road_blockage_percentage: number;
  [key: string]: unknown;
}

export interface ScenarioDefinitionRead {
  scenario_type: string;
  name: string;
  description: string;
  default_parameters: ScenarioParameters;
  is_canonical: boolean;
  tags: string[];
}
