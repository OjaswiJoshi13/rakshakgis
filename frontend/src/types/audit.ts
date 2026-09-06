/**
 * Typed contracts and domain models for Audit Log & Traceability UI (Chunk M6-09).
 * Strictly mirrors backend governance models from app/models/governance.py (AuditLog, OfficerDecision)
 * and incorporates upstream operational events across M6-02 to M6-08.
 */

export type AuditActionCategory =
  | "all"
  | "officer_decision"
  | "relocation_assignment"
  | "scenario_run"
  | "alert_trigger"
  | "telemetry_probe"
  | "report_export";

export type AuditActionType =
  | "officer_approval"
  | "officer_rejection"
  | "officer_revision_request"
  | "dossier_reopened"
  | "relocation_assignment_commit"
  | "scenario_simulation_run"
  | "alert_threshold_ack"
  | "telemetry_probe_executed"
  | "report_dossier_exported";

export type AuditResourceType =
  | "relocation_plan"
  | "scenario_run"
  | "relocation_assignment"
  | "alert_threshold"
  | "telemetry_source"
  | "statutory_report"
  | "officer_decision";

export type AuditDecisionStatus =
  | "approved"
  | "rejected"
  | "revision_requested"
  | "committed"
  | "executed"
  | "acknowledged"
  | "exported"
  | "reopened";

export interface AuditActor {
  id: number | string;
  name: string;
  username?: string;
  email?: string;
  role: string;
  department?: string;
}

export interface AuditTraceabilityInfo {
  source_engine: string;
  region_profile_id: string;
  statutory_mandate: string;
  cryptographic_hash: string;
  payload_before?: Record<string, unknown> | null;
  payload_after?: Record<string, unknown> | null;
  overridden_recommendation?: boolean;
  notes?: string | null;
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  actor: AuditActor;
  action: AuditActionType;
  action_label: string;
  category: AuditActionCategory;
  decision_status: AuditDecisionStatus;
  resource_type: AuditResourceType;
  resource_id: string;
  target_entity_name: string;
  reason?: string | null;
  ip_address?: string | null;
  traceability: AuditTraceabilityInfo;
}

export interface AuditFilterParams {
  query?: string;
  category?: AuditActionCategory;
  decisionStatus?: string;
  timeRange?: "all" | "24h" | "7d" | "30d";
}

export interface AuditSummaryKPIs {
  totalEvents: number;
  officerSignOffs: number;
  automatedActions: number;
  integrityPercentage: number;
}

export interface HashIntegrityResult {
  verifiedCount: number;
  totalCount: number;
  isValid: boolean;
  algorithm: string;
  verifiedAt: string;
}
