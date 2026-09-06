/**
 * Strongly typed domain models for Data Sources & Freshness Monitoring (Chunk M6-06).
 * Conforms strictly to:
 * - Chunk M3-13 Data Source Freshness & Telemetry Backend (contracts.py, telemetry.py)
 * - Chunk M3-03 Provider Interfaces & Mock Adapters (contracts.py)
 */

// ============================================================================
// Enums & Literal Unions (strictly mirroring M3-13 & M3-03)
// ============================================================================

export type FreshnessStatus =
  | "fresh"
  | "stale"
  | "unavailable"
  | "clock_skew"
  | "unknown";

export type ProviderHealth =
  | "healthy"
  | "degraded"
  | "unavailable"
  | "unknown";

export type ProviderMode =
  | "live"
  | "mock"
  | "file"
  | "hybrid";

export type SourceCategory =
  | "rainfall"
  | "flood"
  | "landslide"
  | "hazard_observation"
  | "population_exposure"
  | "other";

// ============================================================================
// Evaluation & Telemetry Models
// ============================================================================

export interface FreshnessEvaluationRead {
  status: FreshnessStatus;
  age_seconds: number | null;
  threshold_seconds: number;
  is_usable: boolean;
  reason: string;
  evaluated_at: string;
}

export interface DataIngestionRunRead {
  id: number;
  data_source_id: number;
  status: "success" | "failed" | "running" | "partial" | string;
  records_ingested: number;
  records_failed: number;
  started_at: string;
  completed_at: string | null;
  log_details: string | null;
}

export interface DataSourceTelemetryRead {
  source_id: number;
  name: string;
  source_type: string;
  provider: string;
  provider_id: string | null;
  category: SourceCategory | string | null;
  provider_mode: ProviderMode | string;
  provider_health: ProviderHealth | string;
  freshness: FreshnessEvaluationRead;
  last_successful_update: string | null;
  last_attempted_update: string | null;
  latest_run_status: string | null;
  is_synthetic: boolean;
  is_active: boolean;
  endpoint_url: string | null;
  polling_interval_seconds: number | null;
  region_id: string | null;
  records_ingested_total: number;
  records_failed_total: number;
}

export interface DataSourceDetailRead extends DataSourceTelemetryRead {
  recent_runs: DataIngestionRunRead[];
  metadata_json: Record<string, any> | null;
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

export interface CategoryFreshnessThresholdItem {
  category: SourceCategory;
  name: string;
  threshold_seconds: number;
  description: string;
}

export interface DataSourceFilterCriteria {
  search?: string;
  category?: string;
  health?: string;
  freshness?: string;
  mode?: string;
}
