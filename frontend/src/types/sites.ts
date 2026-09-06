/**
 * Typed contracts and domain models for Relocation Sites & Infrastructure (Chunk M6-03).
 * Strictly mirrors backend schemas from app/schemas/sites.py,
 * app/core/relocation/suitability/contracts.py, and
 * app/core/relocation/capacity/contracts.py.
 */

export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: [number, number][][];
}

export interface SiteCapacityRead {
  id: number;
  site_id: number;
  max_households: number;
  max_population: number;
  allocated_households: number;
  allocated_population: number;
  available_households: number;
  available_population: number;
  water_supply_lpd?: number | null;
  sanitation_units?: number | null;
  updated_at: string;
}

export interface InfrastructureRead {
  id: number;
  site_id?: number | null;
  name: string;
  infra_type: string;
  status: string;
  location: GeoJSONPoint;
  capacity_description?: string | null;
  created_at: string;
}

export interface CandidateSiteRead {
  id: number;
  name: string;
  district_id: number;
  location: GeoJSONPoint;
  boundary?: GeoJSONPolygon | null;
  area_sq_m?: number | null;
  terrain_slope_deg?: number | null;
  elevation_m?: number | null;
  status: "proposed" | "approved" | "rejected" | "active" | string;
  created_at: string;
  updated_at: string;
}

export interface CandidateSiteDetailRead extends CandidateSiteRead {
  capacities: SiteCapacityRead[];
  infrastructures: InfrastructureRead[];
}

export type SuitabilityDecision = "suitable" | "constrained" | "unsuitable" | "ineligible";

export interface HardConstraintEvaluation {
  constraint_type: string;
  name: string;
  passed: boolean;
  actual_value?: number | string | null;
  threshold_value?: number | string | null;
  reason?: string | null;
}

export interface CriterionScoreResult {
  criterion: string;
  criterion_name: string;
  raw_score: number;
  weight: number;
  weighted_contribution: number;
  description: string;
  audit_notes?: string | null;
}

export interface SiteSuitabilityResult {
  site_id?: number | string | null;
  site_name: string;
  is_eligible: boolean;
  decision: SuitabilityDecision;
  overall_score: number;
  criteria_scores: Record<string, CriterionScoreResult>;
  hard_constraints: HardConstraintEvaluation[];
  failed_constraints: string[];
  summary_reasons: string[];
  evaluated_at: string;
  config_version: string;
}

export interface DimensionSizingResult {
  dimension: string;
  dimension_name: string;
  current_capacity?: number | null;
  required_capacity: number;
  deficit: number;
  is_adequate: boolean;
  unit: string;
}

export interface SiteCapacityResult {
  site_id?: number | string | null;
  site_name: string;
  effective_capacity_households?: number | null;
  current_occupancy_households: number;
  available_capacity_households?: number | null;
  incoming_households: number;
  capacity_margin_households?: number | null;
  remaining_capacity_households?: number | null;
  feasible: boolean;
  limiting_factors: string[];
  unknown_dimensions: string[];
  infrastructure_results: Record<string, DimensionSizingResult>;
  deficits: Record<string, number>;
  assumptions: Record<string, unknown>;
  reasons: ListReasons;
}

export type ListReasons = string[];

export type SiteDetailTab = "infrastructure" | "suitability" | "capacity";
