/**
 * Typed contracts and domain models for Relocation Matching & Assignment (Chunk M6-02).
 * Strictly mirrors backend contracts from app/core/relocation/matching/contracts.py
 * and app/schemas/relocation.py (Chunk M4-04).
 */

export type AssignmentStatus = "assigned" | "unassigned";

export type RejectionReasonCode =
  | "unsafe_site"
  | "low_suitability"
  | "insufficient_capacity"
  | "unknown_capacity"
  | "site_unavailable"
  | "no_feasible_site";

export type MatchingAlgorithmType = "greedy_priority";

export interface VillageDemandInput {
  village_id: number | string;
  village_name: string;
  priority_score: number;
  priority_band?: string | null;
  incoming_households: number;
  incoming_population?: number | null;
  location?: [number, number] | null; // [longitude, latitude]
  metadata?: Record<string, unknown>;
}

export interface MatchingSiteCandidate {
  site_id: number | string;
  site_name: string;
  location?: [number, number] | null;
  status: string;
  initial_available_capacity?: number | null;
}

export interface CandidateEvaluationAudit {
  site_id: number | string;
  site_name: string;
  is_feasible: boolean;
  rejection_code?: RejectionReasonCode | null;
  rejection_reasons: string[];
  suitability_score?: number | null;
  suitability_decision?: string | null;
  available_capacity_before?: number | null;
  capacity_margin?: number | null;
  distance_km?: number | null;
  rank_score?: number | null;
}

export interface VillageAssignmentResult {
  village_id: number | string;
  village_name: string;
  priority_score: number;
  priority_band?: string | null;
  incoming_households: number;
  incoming_population?: number | null;
  status: AssignmentStatus;
  assigned_site_id?: number | string | null;
  assigned_site_name?: string | null;
  suitability_score?: number | null;
  distance_km?: number | null;
  available_capacity_before?: number | null;
  available_capacity_after?: number | null;
  selection_reason?: string | null;
  unassigned_reason?: string | null;
  unassigned_code?: RejectionReasonCode | null;
  evaluated_candidates: CandidateEvaluationAudit[];
}

export interface RelocationMatchingResult {
  matching_id: string;
  algorithm: MatchingAlgorithmType;
  total_villages: number;
  assigned_villages_count: number;
  unassigned_villages_count: number;
  total_households_demanded: number;
  total_households_allocated: number;
  total_households_unassigned: number;
  assignments: VillageAssignmentResult[];
  site_remaining_capacities: Record<string, number>;
  summary_narrative: string;
  execution_timestamp: string;
  region_profile_id: string;
  governance_notice: string;
}

export interface RelocationMatchingRequest {
  villages?: VillageDemandInput[] | null;
  sites?: MatchingSiteCandidate[] | null;
  use_database_villages?: boolean;
  use_database_sites?: boolean;
  region_profile_id?: string;
  district_id?: number | null;
}

export interface RelocationAssignmentCreate {
  village_id: number;
  candidate_site_id: number;
  assigned_households: number;
  assigned_population?: number | null;
  status?: string;
}

export interface RelocationAssignmentBatchCreate {
  assignments: RelocationAssignmentCreate[];
  commit_site_capacity?: boolean;
}

export interface RelocationAssignmentRead {
  id?: number;
  village_id: number;
  village_name?: string | null;
  candidate_site_id: number;
  candidate_site_name?: string | null;
  assigned_households: number;
  assigned_population: number;
  status: string;
  approved_by_officer_id?: number | null;
  assigned_at?: string | null;
  updated_at?: string | null;
}

export type RelocationWorkflowView = "matching" | "ledger";

export type AssignmentFilter = "all" | "assigned" | "unassigned";
