/**
 * Village Vulnerability & Habitation Analysis Domain Types (Chunk M5-06).
 *
 * Strictly models authoritative backend contracts:
 * - M3-06 Multi-Hazard Risk Computation & 6-factor breakdowns
 * - M3-07 Risk Classification Bands
 * - M3-09 Vulnerability & Exposure scoring
 * - M3-11 Dynamic Red Zone triggers
 * - M3-12 Relocation Priority scoring
 * - M4-04 Relocation Matching & Assignment
 * - M4-05 Evacuation & Access Routing
 * - M4-06 Scenario Simulator Pipeline
 */

import { RiskBand, RelocationPriorityBand } from "@/design-system/tokens";

/** Authoritative 6-factor risk breakdown from M3-06 / M4-06 */
export interface RiskFactorBreakdown {
  hazard_severity?: number;
  flood_exposure?: number;
  rainfall_intensity?: number;
  slope_landslide_susceptibility?: number;
  infrastructure_vulnerability?: number;
  social_vulnerability?: number;
  [key: string]: number | undefined;
}

/** Single village risk stage output from M4-06 pipeline */
export interface VillageRiskStageResult {
  village_id: string;
  village_name: string;
  risk_score: number;
  risk_band: string;
  factor_breakdown: RiskFactorBreakdown;
}

/** Priority stage output from M4-06 pipeline */
export interface PriorityStageResult {
  village_id: string;
  village_name: string;
  priority_score: number;
  priority_band: string;
}

/** Dynamic Red Zone evaluation result */
export interface DynamicRedZoneStageResult {
  total_evaluated: number;
  triggered_count: number;
  triggered_village_ids: string[];
  candidate_ids: string[];
}

/** Matching assignment summary for a village */
export interface MatchingAssignmentSummary {
  village_id: string;
  village_name: string;
  assigned_site_id?: string | null;
  assigned_site_name?: string | null;
  is_assigned: boolean;
  demanded_households: number;
  allocated_households: number;
  unassigned_code?: string | null;
  rank_score?: number | null;
  distance_km?: number | null;
}

/** Evacuation routing path summary for a village */
export interface RoutingPathSummary {
  village_id: string;
  site_id: string;
  is_feasible: boolean;
  distance_km?: number | null;
  estimated_time_minutes?: number | null;
  blocked_avoided_count: number;
  route_status: string;
}

/** Stage pipeline result from M4-06 */
export interface StagePipelineResult {
  risk_results: VillageRiskStageResult[];
  red_zone_result: DynamicRedZoneStageResult;
  priority_results: PriorityStageResult[];
  matching_result?: {
    total_villages: number;
    assigned_count: number;
    unassigned_count: number;
    assignments: MatchingAssignmentSummary[];
  };
  routing_result?: {
    routes_evaluated: number;
    feasible_routes_count: number;
    unroutable_count: number;
    routes: RoutingPathSummary[];
  };
}

/** Root scenario simulation output from POST /api/v1/scenarios/run */
export interface ScenarioSimulationOutput {
  scenario_name: string;
  scenario_type: string;
  region_profile_id: string;
  run_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  baseline_pipeline: StagePipelineResult;
  scenario_pipeline: StagePipelineResult;
}

/**
 * Unified Habitation / Village Analysis Model presented to the officer UI.
 * Assembled from authoritative backend envelopes without invented numbers.
 */
export interface HabitationDetail {
  id: string;
  name: string;
  census_code?: string | null;
  region_profile_id?: string | null;
  district?: string | null;
  block?: string | null;
  coordinates?: [number, number] | null; // [lon, lat]
  elevation_m?: number | null;
  slope_deg?: number | null;

  // Population & Demographics
  demographics: {
    total_population: number | null;
    households: number | null;
    elderly_count?: number | null;
    children_count?: number | null;
    disabled_count?: number | null;
  };

  // Vulnerability assessment
  vulnerability: {
    social_vulnerability_score: number | null;
    infrastructure_vulnerability_score: number | null;
    vulnerability_band?: string | null;
  };

  // Multi-Hazard Risk assessment
  risk: {
    risk_score: number | null;
    risk_band: RiskBand | null;
    raw_band_string?: string | null;
    factors: RiskFactorBreakdown;
    is_red_zone_triggered: boolean;
  };

  // Relocation priority & matching
  relocation: {
    priority_score: number | null;
    priority_band: RelocationPriorityBand | null;
    raw_priority_band_string?: string | null;
    is_assigned: boolean;
    assigned_site_id?: string | null;
    assigned_site_name?: string | null;
    demanded_households?: number | null;
    allocated_households?: number | null;
    unassigned_code?: string | null;
  };

  // Evacuation routing
  evacuation?: {
    route_feasible: boolean;
    distance_km?: number | null;
    estimated_time_minutes?: number | null;
    blocked_corridors_count?: number;
    route_status?: string | null;
  };
}

/** Standard weights configuration for risk breakdown visualization (M3-06) */
export const M3_06_RISK_FACTOR_WEIGHTS = [
  { key: "hazard_severity", label: "Hazard Severity", weight: 0.30, symbol: "H", description: "Geological & compound hazard severity" },
  { key: "flood_exposure", label: "Flood Exposure", weight: 0.20, symbol: "F", description: "Proximity to flash flood & water level thresholds" },
  { key: "rainfall_intensity", label: "Rainfall Intensity", weight: 0.15, symbol: "R", description: "Antecedent 24h & 72h precipitation" },
  { key: "slope_landslide_susceptibility", label: "Slope / Landslide", weight: 0.15, symbol: "S", description: "Terrain inclination & historical slope failures" },
  { key: "infrastructure_vulnerability", label: "Infrastructure Isolation", weight: 0.10, symbol: "D", description: "Single-access roads & critical lifeline vulnerability" },
  { key: "social_vulnerability", label: "Social Vulnerability", weight: 0.10, symbol: "V", description: "Socio-economic & demographic dependency ratios" },
] as const;

/** Standard weights configuration for relocation priority formula (M3-12) */
export const M3_12_PRIORITY_WEIGHTS = [
  { factor: "Composite Risk", weight: 0.40, symbol: "R" },
  { factor: "Demographic Exposure", weight: 0.25, symbol: "E" },
  { factor: "Social Vulnerability", weight: 0.20, symbol: "V" },
  { factor: "Hazard Severity", weight: 0.10, symbol: "H" },
  { factor: "Isolation / Accessibility", weight: 0.05, symbol: "A" },
] as const;

/**
 * Safely parse and normalize backend-provided risk band string into strongly typed RiskBand.
 * Returns null if the backend string is null/undefined or not a recognized band.
 */
export function parseRiskBand(raw: string | null | undefined): RiskBand | null {
  if (!raw) return null;
  const normalized = raw.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (
    normalized === "safe" ||
    normalized === "moderate" ||
    normalized === "high" ||
    normalized === "very_high" ||
    normalized === "critical"
  ) {
    return normalized as RiskBand;
  }
  return null;
}

/**
 * Safely parse and normalize backend-provided relocation priority band string into strongly typed RelocationPriorityBand.
 * Returns null if the backend string is null/undefined or not a recognized band.
 */
export function parseRelocationPriorityBand(raw: string | null | undefined): RelocationPriorityBand | null {
  if (!raw) return null;
  const normalized = raw.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (
    normalized === "immediate" ||
    normalized === "short_term" ||
    normalized === "medium_term" ||
    normalized === "monitor"
  ) {
    return normalized as RelocationPriorityBand;
  }
  return null;
}

