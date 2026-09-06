/**
 * Strongly typed domain models for Real-Time Alerts & Threshold Warnings (Chunk M6-05).
 * Conforms strictly to:
 * - Chunk M3-11 Dynamic Red Zone & Threshold Trigger Engine (dynamic_contracts.py)
 * - Chunk M3-13 Alert database model (telemetry.py)
 * - Authoritative Regional Profile trigger thresholds (himalayan.py, coastal.py, riverine.py)
 */

export type DangerLevel =
  | "LOW"
  | "MODERATE"
  | "HIGH"
  | "VERY_HIGH"
  | "CRITICAL"
  | "UNINHABITABLE";

// ============================================================================
// Status, Indicator & Operator Enums (strictly mirroring M3-11)
// ============================================================================

export type DynamicTriggerStatus = "no_trigger" | "triggered" | "insufficient_data";

export type DynamicHazardIndicator =
  | "rainfall_24h"
  | "seismic_mmi"
  | "slope_deg"
  | "water_level_above_danger"
  | "landslide_debris_volume"
  | "landslide_activity"
  | "custom";

export type ComparisonOperator = ">" | ">=" | "<" | "<=" | "==";

export type AlertSeverity = "info" | "warning" | "severe" | "extreme";

export type AlertType =
  | "rainfall_threshold"
  | "landslide_warning"
  | "evacuation_notice"
  | "seismic_event"
  | "flood_breach"
  | "dynamic_red_zone";

// ============================================================================
// Explainability & Audit Trail Contracts (M3-11)
// ============================================================================

export interface SingleTriggerEvaluation {
  indicator: string;
  observed_value?: number | null;
  configured_threshold?: number | null;
  operator: ComparisonOperator | string;
  triggered: boolean;
  status: DynamicTriggerStatus;
  unit?: string | null;
  audit_note: string;
}

export interface DynamicRedZoneExplainability {
  decision_reason: string;
  summary: string;
  profile_id: string;
  profile_name?: string;
  trigger_evaluations: SingleTriggerEvaluation[];
  triggered_indicators: string[];
  missing_indicators: string[];
  source_observation_ids: string[];
  source_village_ids: string[];
  buffer_applied_m?: number | null;
  is_dissolved?: boolean;
  dissolved_count?: number;
  governance_notice: string;
}

// ============================================================================
// Operational Alert Model (Unified M3-11 Dynamic Candidate & M3-13 Alert)
// ============================================================================

export interface OperationalAlertItem {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  danger_level?: DangerLevel | null;
  status: DynamicTriggerStatus;
  headline: string;
  message: string;
  village_id?: string | null;
  village_name?: string | null;
  district_id?: string | null;
  district_name?: string | null;
  coordinates?: [number, number] | null; // [longitude, latitude] WGS84
  indicator: DynamicHazardIndicator | string;
  observed_value?: number | null;
  configured_threshold?: number | null;
  operator: ComparisonOperator | string;
  unit?: string | null;
  buffer_m?: number | null;
  is_acknowledged: boolean;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  issued_at: string;
  expires_at?: string | null;
  candidate_id?: string | null;
  source_id?: string | null;
  is_synthetic: boolean;
  explainability?: DynamicRedZoneExplainability | null;
}

// ============================================================================
// Threshold Configuration Contract (M3-11 Profile Resolution)
// ============================================================================

export interface DynamicThresholdSummary {
  profile_id: string;
  profile_name: string;
  rainfall_trigger_24h_mm: number;
  seismic_trigger_mmi?: number | null;
  slope_trigger_min_deg: number;
  water_level_trigger_m_above_danger?: number | null;
  landslide_debris_volume_trigger_m3?: number | null;
  buffer_distance_m: number;
  default_danger_level: DangerLevel;
}

// ============================================================================
// Operational Filters & Overview Metrics
// ============================================================================

export interface AlertFilterCriteria {
  severity?: AlertSeverity | "all";
  status?: DynamicTriggerStatus | "all";
  indicator?: DynamicHazardIndicator | "all";
  is_acknowledged?: boolean | "all";
  search?: string;
}

export interface AlertSummaryMetrics {
  total_alerts: number;
  triggered_count: number;
  pending_acknowledgment: number;
  insufficient_data_count: number;
  critical_extreme_count: number;
}
