/**
 * Typed contracts and domain models for Officer Review & Action Sign-Off Workflow (Chunk M6-08).
 * Strictly mirrors backend contracts from app/models/governance.py (OfficerDecision)
 * and upstream recommendation models from Chunk M6-02 and Chunk M6-04.
 */

import { VillageAssignmentResult } from "./relocation";
import { ScenarioType, ScenarioParameters } from "./scenarios";

export type OfficerDecisionAction = "approved" | "rejected" | "revision_requested";

export type ReviewStatus = "pending_review" | "approved" | "rejected" | "revision_requested";

export type RecommendationType = "relocation_plan" | "scenario_evaluation";

/**
 * Mirror of backend OfficerDecision entity in app/models/governance.py
 */
export interface OfficerDecisionRecord {
  id?: number | string;
  officer_id: number | string;
  officer_name: string;
  officer_role: string;
  decision_type:
    | "relocation_plan"
    | "scenario_approval"
    | "evacuation_order"
    | "site_approval"
    | "zone_declaration";
  target_entity_type: "relocation_plan" | "scenario_run" | "village" | "candidate_site";
  target_entity_id: string | number;
  action_taken: OfficerDecisionAction;
  rationale: string;
  overridden_recommendation: boolean;
  decision_metadata_json?: Record<string, unknown> | null;
  decided_at: string;
}

export interface ReviewMetric {
  label: string;
  value: string | number;
  subtext?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

export interface ScenarioRecommendationPayload {
  scenario_type: ScenarioType;
  scenario_name: string;
  parameters: ScenarioParameters;
  critical_risk_villages: number;
  unassigned_households: number;
  unroutable_villages_count: number;
  diverted_routes_count: number;
  average_risk_delta: number;
  summary_narrative: string;
}

export interface RelocationRecommendationPayload {
  matching_id: string;
  total_villages: number;
  assigned_villages_count: number;
  unassigned_villages_count: number;
  total_households_demanded: number;
  total_households_allocated: number;
  total_households_unassigned: number;
  assignments: VillageAssignmentResult[];
  summary_narrative: string;
}

export interface RecommendationDossier {
  id: string;
  title: string;
  type: RecommendationType;
  source_engine: string;
  region_profile_id: string;
  created_at: string;
  urgency_level: "critical" | "high" | "moderate";
  proposed_action: string;
  executive_summary: string;
  metrics: ReviewMetric[];
  relocation_payload?: RelocationRecommendationPayload;
  scenario_payload?: ScenarioRecommendationPayload;
  status: ReviewStatus;
  decision?: OfficerDecisionRecord | null;
  statutory_mandate: string;
}

export interface SubmitDecisionRequest {
  recommendation_id: string;
  action: OfficerDecisionAction;
  rationale: string;
  confirm_statutory_verification: boolean;
  override_ai_recommendation?: boolean;
}
