/**
 * Typed contracts and domain models for Scenario Simulator UI (Chunk M6-04).
 * Strictly mirrors backend schemas from app/schemas/scenarios.py and
 * app/core/scenarios/contracts.py.
 */

export type ScenarioType =
  | "NORMAL"
  | "EXTREME_RAINFALL"
  | "FLASH_FLOOD"
  | "CAPACITY_CRISIS"
  | "CUSTOM";

export type ScenarioRunStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED";

export interface ScenarioParameters {
  scenario_type: ScenarioType;
  rainfall_multiplier: number;
  capacity_reduction_percentage: number;
  flood_severity?: string | null;
  flood_hazard_increase: number;
  road_blockage_percentage: number;
  blocked_segment_ids: string[];
  seismic_intensity_mmi?: number | null;
  custom_overrides?: Record<string, unknown>;
}

export interface ScenarioDefinitionRead {
  scenario_type: string;
  name: string;
  description: string;
  default_parameters: ScenarioParameters;
  is_canonical: boolean;
  tags: string[];
}

export interface ScenarioRunRequest {
  scenario_type: string;
  region_profile_id?: string;
  parameters?: Partial<ScenarioParameters>;
  persist?: boolean;
}

export interface VillageRiskStageResult {
  village_id: string;
  village_name: string;
  risk_score: number;
  risk_band: string;
  factor_breakdown: Record<string, number>;
}

export interface DynamicRedZoneStageResult {
  total_evaluated: number;
  triggered_count: number;
  triggered_village_ids: string[];
  candidate_ids: string[];
}

export interface PriorityStageResult {
  village_id: string;
  village_name: string;
  priority_score: number;
  priority_band: string;
}

export interface CapacityStageResult {
  site_id: string;
  site_name: string;
  effective_capacity: number;
  available_capacity: number;
  limiting_factor: string;
  is_feasible: boolean;
}

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

export interface MatchingStageResult {
  total_villages: number;
  total_households_demanded: number;
  total_households_allocated: number;
  total_households_unassigned: number;
  assigned_count: number;
  unassigned_count: number;
  assignments: MatchingAssignmentSummary[];
}

export interface RoutingPathSummary {
  village_id: string;
  site_id: string;
  is_feasible: boolean;
  distance_km?: number | null;
  estimated_time_minutes?: number | null;
  blocked_avoided_count: number;
  route_status: string; // "FEASIBLE" | "DIVERTED" | "CUT_OFF"
}

export interface RoutingStageResult {
  routes_evaluated: number;
  feasible_routes_count: number;
  unroutable_count: number;
  average_distance_km?: number | null;
  routes: RoutingPathSummary[];
}

export interface StagePipelineResult {
  risk_results: VillageRiskStageResult[];
  red_zone_result: DynamicRedZoneStageResult;
  priority_results: PriorityStageResult[];
  capacity_results: CapacityStageResult[];
  matching_result: MatchingStageResult;
  routing_result: RoutingStageResult;
  summary_metrics?: Record<string, unknown>;
}

export interface RiskBandShift {
  village_id: string;
  baseline_band: string;
  scenario_band: string;
}

export interface PriorityBandShift {
  village_id: string;
  baseline_band: string;
  scenario_band: string;
}

export interface SiteReallocation {
  village_id: string;
  baseline_site_id: string;
  scenario_site_id: string;
}

export interface ScenarioComparison {
  risk_score_deltas: Record<string, number>;
  average_risk_delta: number;
  risk_band_shifts: RiskBandShift[];
  villages_escalated_to_critical: string[];
  baseline_red_zones_count: number;
  scenario_red_zones_count: number;
  new_red_zone_villages: string[];
  priority_score_deltas: Record<string, number>;
  priority_band_shifts: PriorityBandShift[];
  villages_escalated_to_immediate: string[];
  site_capacity_deltas: Record<string, number>;
  newly_infeasible_sites: string[];
  baseline_unassigned_count: number;
  scenario_unassigned_count: number;
  newly_unassigned_villages: string[];
  site_reallocations: SiteReallocation[];
  route_distance_deltas: Record<string, number>;
  corridors_diverted: string[];
  newly_severed_routes: string[];
  comparison_narrative: string;
}

export interface ScenarioSimulationOutput {
  scenario_name: string;
  scenario_type: ScenarioType;
  region_profile_id: string;
  run_id: string;
  status: ScenarioRunStatus;
  parameters: ScenarioParameters;
  started_at: string;
  completed_at: string;
  baseline_metrics: {
    average_risk_score?: number;
    critical_risk_villages?: number;
    active_red_zones?: number;
    immediate_priority_villages?: number;
    total_effective_capacity?: number;
    allocated_households?: number;
    unassigned_households?: number;
    feasible_routes?: number;
    average_route_distance_km?: number;
    [key: string]: unknown;
  };
  scenario_metrics: {
    average_risk_score?: number;
    critical_risk_villages?: number;
    active_red_zones?: number;
    immediate_priority_villages?: number;
    total_effective_capacity?: number;
    allocated_households?: number;
    unassigned_households?: number;
    feasible_routes?: number;
    average_route_distance_km?: number;
    [key: string]: unknown;
  };
  comparison: ScenarioComparison;
  baseline_pipeline: StagePipelineResult;
  scenario_pipeline: StagePipelineResult;
  provenance: Record<string, unknown>;
  explainability: Record<string, unknown>;
}

export interface ScenarioRunRecordRead {
  id: number;
  scenario_id: number;
  executed_by_user_id?: number | null;
  status: string;
  start_time: string;
  end_time?: string | null;
  simulated_affected_villages?: number | null;
  simulated_displaced_population?: number | null;
  results_summary_json?: Record<string, unknown> | null;
  error_message?: string | null;
}

export type ScenarioDomainTab = "risk" | "relocation" | "routing";
