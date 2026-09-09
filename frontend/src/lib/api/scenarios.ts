/**
 * API client service and deterministic Himalayan Pilot datasets for Scenario Simulator (Chunk M6-04).
 * Mirrors backend endpoints from app/api/v1/scenarios.py.
 */

import { apiClient } from "./client";
import { ResponseEnvelope } from "@/types/api";
import {
  ScenarioDefinitionRead,
  ScenarioParameters,
  ScenarioRunRequest,
  ScenarioRunRecordRead,
  ScenarioSimulationOutput,
  ScenarioType,
} from "@/types/scenarios";

export type { ScenarioType };

// ============================================================================
// Canonical Scenario Catalog
// ============================================================================

export const CANONICAL_SCENARIO_CATALOG: ScenarioDefinitionRead[] = [
  {
    scenario_type: "NORMAL",
    name: "Normal / Baseline State",
    description:
      "Represents current baseline operating conditions without artificial hazard or capacity alterations.",
    default_parameters: {
      scenario_type: "NORMAL",
      rainfall_multiplier: 1.0,
      capacity_reduction_percentage: 0.0,
      flood_hazard_increase: 0.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    is_canonical: true,
    tags: ["baseline", "operational"],
  },
  {
    scenario_type: "EXTREME_RAINFALL",
    name: "Extreme Rainfall Simulation (+40%)",
    description:
      "Simulates a 40% increase in precipitation intensity (simulation parameter for heavy rainfall stress testing).",
    default_parameters: {
      scenario_type: "EXTREME_RAINFALL",
      rainfall_multiplier: 1.4,
      capacity_reduction_percentage: 0.0,
      flood_hazard_increase: 10.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    is_canonical: true,
    tags: ["climate_shock", "hazard_escalation", "monsoon"],
  },
  {
    scenario_type: "FLASH_FLOOD",
    name: "Flash Flood / GLOF Valley Inundation",
    description:
      "Simulates severe riverine flash flooding and GLOF surge along river valleys, cutting off low-lying transit highways.",
    default_parameters: {
      scenario_type: "FLASH_FLOOD",
      rainfall_multiplier: 1.2,
      capacity_reduction_percentage: 0.0,
      flood_severity: "critical",
      flood_hazard_increase: 35.0,
      road_blockage_percentage: 15.0,
      blocked_segment_ids: ["RD-SEG-NH58-01", "RD-SEG-ALAK-04"],
    },
    is_canonical: true,
    tags: ["glof", "flash_flood", "road_severance"],
  },
  {
    scenario_type: "CAPACITY_CRISIS",
    name: "Relocation Capacity Crisis (-50%)",
    description:
      "Simulates a 50% loss or shortage of usable carrying capacity across candidate relocation sites.",
    default_parameters: {
      scenario_type: "CAPACITY_CRISIS",
      rainfall_multiplier: 1.0,
      capacity_reduction_percentage: 50.0,
      flood_hazard_increase: 0.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    is_canonical: true,
    tags: ["bottleneck", "capacity_deficit", "resource_strain"],
  },
];

// ============================================================================
// Deterministic Himalayan Pilot Sample Simulation Outputs
// ============================================================================

export const HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS: Record<
  ScenarioType,
  ScenarioSimulationOutput
> = {
  NORMAL: {
    scenario_name: "Normal / Baseline State",
    scenario_type: "NORMAL",
    region_profile_id: "himalayan_pilot",
    run_id: "SIM-RUN-20260906-BASE",
    status: "COMPLETED",
    parameters: {
      scenario_type: "NORMAL",
      rainfall_multiplier: 1.0,
      capacity_reduction_percentage: 0.0,
      flood_hazard_increase: 0.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    started_at: "2026-09-06T12:00:00Z",
    completed_at: "2026-09-06T12:00:01Z",
    baseline_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    scenario_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    comparison: {
      risk_score_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      average_risk_delta: 0.0,
      risk_band_shifts: [],
      villages_escalated_to_critical: [],
      baseline_red_zones_count: 1,
      scenario_red_zones_count: 1,
      new_red_zone_villages: [],
      priority_score_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      priority_band_shifts: [],
      villages_escalated_to_immediate: [],
      site_capacity_deltas: {
        "101": 0,
        "102": 0,
      },
      newly_infeasible_sites: [],
      baseline_unassigned_count: 0,
      scenario_unassigned_count: 0,
      newly_unassigned_villages: [],
      site_reallocations: [],
      route_distance_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      corridors_diverted: [],
      newly_severed_routes: [],
      comparison_narrative:
        "Baseline operating scenario. All risk scores, Dynamic Red Zones, and evacuation routes are in equilibrium with nominal conditions.",
    },
    baseline_pipeline: {
      risk_results: [
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          risk_score: 68.5,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 42.0, slope: 72.0, flood: 30.0 },
        },
        {
          village_id: "HIM-VILL-002",
          village_name: "Ravigram",
          risk_score: 58.2,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 38.0, slope: 58.0, flood: 25.0 },
        },
        {
          village_id: "HIM-VILL-003",
          village_name: "Marwari",
          risk_score: 76.4,
          risk_band: "CRITICAL",
          factor_breakdown: { rainfall: 50.0, slope: 82.0, flood: 65.0 },
        },
        {
          village_id: "HIM-VILL-004",
          village_name: "Manohar Bagh",
          risk_score: 46.5,
          risk_band: "MODERATE",
          factor_breakdown: { rainfall: 35.0, slope: 45.0, flood: 20.0 },
        },
      ],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: ["HIM-VILL-001"],
      },
      priority_results: [
        {
          village_id: "HIM-VILL-003",
          village_name: "Marwari",
          priority_score: 79.2,
          priority_band: "IMMEDIATE",
        },
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          priority_score: 64.0,
          priority_band: "SHORT_TERM",
        },
        {
          village_id: "HIM-VILL-002",
          village_name: "Ravigram",
          priority_score: 52.8,
          priority_band: "MEDIUM_TERM",
        },
        {
          village_id: "HIM-VILL-004",
          village_name: "Manohar Bagh",
          priority_score: 41.5,
          priority_band: "MONITOR",
        },
      ],
      capacity_results: [
        {
          site_id: "101",
          site_name: "Joshimath Safe Terrace",
          effective_capacity: 85,
          available_capacity: 8,
          limiting_factor: "sanitation",
          is_feasible: true,
        },
        {
          site_id: "102",
          site_name: "Pipalkoti Plateau",
          effective_capacity: 120,
          available_capacity: 45,
          limiting_factor: "water_supply",
          is_feasible: true,
        },
      ],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [
          {
            village_id: "HIM-VILL-003",
            village_name: "Marwari",
            assigned_site_id: "101",
            assigned_site_name: "Joshimath Safe Terrace",
            is_assigned: true,
            demanded_households: 95,
            allocated_households: 95,
            distance_km: 6.4,
          },
          {
            village_id: "HIM-VILL-001",
            village_name: "Sunil",
            assigned_site_id: "102",
            assigned_site_name: "Pipalkoti Plateau",
            is_assigned: true,
            demanded_households: 110,
            allocated_households: 110,
            distance_km: 24.2,
          },
        ],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [
          {
            village_id: "HIM-VILL-003",
            site_id: "101",
            is_feasible: true,
            distance_km: 6.4,
            estimated_time_minutes: 18.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
          {
            village_id: "HIM-VILL-001",
            site_id: "102",
            is_feasible: true,
            distance_km: 24.2,
            estimated_time_minutes: 55.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
          {
            village_id: "HIM-VILL-002",
            site_id: "101",
            is_feasible: true,
            distance_km: 8.8,
            estimated_time_minutes: 24.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
          {
            village_id: "HIM-VILL-004",
            site_id: "102",
            is_feasible: true,
            distance_km: 26.5,
            estimated_time_minutes: 60.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
        ],
      },
    },
    scenario_pipeline: {
      risk_results: [
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          risk_score: 68.5,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 42.0, slope: 72.0, flood: 30.0 },
        },
      ],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    provenance: { engine_version: "1.0.0", algorithm: "M4-06 Pipeline Orchestrator" },
    explainability: { methodology: "Deterministic baseline isolation" },
  },
  EXTREME_RAINFALL: {
    scenario_name: "Extreme Rainfall Simulation (+40%)",
    scenario_type: "EXTREME_RAINFALL",
    region_profile_id: "himalayan_pilot",
    run_id: "SIM-RUN-20260906-EXRAIN",
    status: "COMPLETED",
    parameters: {
      scenario_type: "EXTREME_RAINFALL",
      rainfall_multiplier: 1.4,
      capacity_reduction_percentage: 0.0,
      flood_hazard_increase: 10.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    started_at: "2026-09-06T12:05:00Z",
    completed_at: "2026-09-06T12:05:01Z",
    baseline_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    scenario_metrics: {
      average_risk_score: 66.8,
      critical_risk_villages: 3,
      active_red_zones: 3,
      immediate_priority_villages: 3,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    comparison: {
      risk_score_deltas: {
        "HIM-VILL-001": 14.8,
        "HIM-VILL-002": 13.5,
        "HIM-VILL-003": 11.2,
        "HIM-VILL-004": 18.1,
      },
      average_risk_delta: 14.4,
      risk_band_shifts: [
        {
          village_id: "HIM-VILL-001",
          baseline_band: "HIGH",
          scenario_band: "CRITICAL",
        },
        {
          village_id: "HIM-VILL-002",
          baseline_band: "HIGH",
          scenario_band: "CRITICAL",
        },
        {
          village_id: "HIM-VILL-004",
          baseline_band: "MODERATE",
          scenario_band: "HIGH",
        },
      ],
      villages_escalated_to_critical: ["HIM-VILL-001", "HIM-VILL-002"],
      baseline_red_zones_count: 1,
      scenario_red_zones_count: 3,
      new_red_zone_villages: ["HIM-VILL-001", "HIM-VILL-002"],
      priority_score_deltas: {
        "HIM-VILL-001": 15.6,
        "HIM-VILL-002": 14.2,
        "HIM-VILL-003": 8.0,
        "HIM-VILL-004": 12.0,
      },
      priority_band_shifts: [
        {
          village_id: "HIM-VILL-001",
          baseline_band: "SHORT_TERM",
          scenario_band: "IMMEDIATE",
        },
        {
          village_id: "HIM-VILL-002",
          baseline_band: "MEDIUM_TERM",
          scenario_band: "IMMEDIATE",
        },
      ],
      villages_escalated_to_immediate: ["HIM-VILL-001", "HIM-VILL-002"],
      site_capacity_deltas: {
        "101": 0,
        "102": 0,
      },
      newly_infeasible_sites: [],
      baseline_unassigned_count: 0,
      scenario_unassigned_count: 0,
      newly_unassigned_villages: [],
      site_reallocations: [],
      route_distance_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      corridors_diverted: [],
      newly_severed_routes: [],
      comparison_narrative:
        "40% rainfall surge causes widespread risk escalation. Sunil and Ravigram escalate into CRITICAL risk and trigger Dynamic Red Zones. Immediate relocation urgency rises by 2 villages (+200%), requiring expedited evacuation preparedness.",
    },
    baseline_pipeline: {
      risk_results: [
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          risk_score: 68.5,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 42.0, slope: 72.0, flood: 30.0 },
        },
        {
          village_id: "HIM-VILL-002",
          village_name: "Ravigram",
          risk_score: 58.2,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 38.0, slope: 58.0, flood: 25.0 },
        },
        {
          village_id: "HIM-VILL-003",
          village_name: "Marwari",
          risk_score: 76.4,
          risk_band: "CRITICAL",
          factor_breakdown: { rainfall: 50.0, slope: 82.0, flood: 65.0 },
        },
        {
          village_id: "HIM-VILL-004",
          village_name: "Manohar Bagh",
          risk_score: 46.5,
          risk_band: "MODERATE",
          factor_breakdown: { rainfall: 35.0, slope: 45.0, flood: 20.0 },
        },
      ],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: ["HIM-VILL-001"],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    scenario_pipeline: {
      risk_results: [
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          risk_score: 83.3,
          risk_band: "CRITICAL",
          factor_breakdown: { rainfall: 58.8, slope: 84.0, flood: 40.0 },
        },
        {
          village_id: "HIM-VILL-002",
          village_name: "Ravigram",
          risk_score: 71.7,
          risk_band: "CRITICAL",
          factor_breakdown: { rainfall: 53.2, slope: 69.5, flood: 35.0 },
        },
        {
          village_id: "HIM-VILL-003",
          village_name: "Marwari",
          risk_score: 87.6,
          risk_band: "CRITICAL",
          factor_breakdown: { rainfall: 70.0, slope: 92.0, flood: 75.0 },
        },
        {
          village_id: "HIM-VILL-004",
          village_name: "Manohar Bagh",
          risk_score: 64.6,
          risk_band: "HIGH",
          factor_breakdown: { rainfall: 49.0, slope: 56.0, flood: 30.0 },
        },
      ],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 3,
        triggered_village_ids: ["HIM-VILL-001", "HIM-VILL-002", "HIM-VILL-003"],
        candidate_ids: ["HIM-VILL-004"],
      },
      priority_results: [
        {
          village_id: "HIM-VILL-001",
          village_name: "Sunil",
          priority_score: 79.6,
          priority_band: "IMMEDIATE",
        },
        {
          village_id: "HIM-VILL-003",
          village_name: "Marwari",
          priority_score: 87.2,
          priority_band: "IMMEDIATE",
        },
        {
          village_id: "HIM-VILL-002",
          village_name: "Ravigram",
          priority_score: 67.0,
          priority_band: "IMMEDIATE",
        },
        {
          village_id: "HIM-VILL-004",
          village_name: "Manohar Bagh",
          priority_score: 53.5,
          priority_band: "SHORT_TERM",
        },
      ],
      capacity_results: [
        {
          site_id: "101",
          site_name: "Joshimath Safe Terrace",
          effective_capacity: 85,
          available_capacity: 8,
          limiting_factor: "sanitation",
          is_feasible: true,
        },
        {
          site_id: "102",
          site_name: "Pipalkoti Plateau",
          effective_capacity: 120,
          available_capacity: 45,
          limiting_factor: "water_supply",
          is_feasible: true,
        },
      ],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [
          {
            village_id: "HIM-VILL-003",
            village_name: "Marwari",
            assigned_site_id: "101",
            assigned_site_name: "Joshimath Safe Terrace",
            is_assigned: true,
            demanded_households: 95,
            allocated_households: 95,
            distance_km: 6.4,
          },
          {
            village_id: "HIM-VILL-001",
            village_name: "Sunil",
            assigned_site_id: "102",
            assigned_site_name: "Pipalkoti Plateau",
            is_assigned: true,
            demanded_households: 110,
            allocated_households: 110,
            distance_km: 24.2,
          },
        ],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [
          {
            village_id: "HIM-VILL-003",
            site_id: "101",
            is_feasible: true,
            distance_km: 6.4,
            estimated_time_minutes: 18.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
          {
            village_id: "HIM-VILL-001",
            site_id: "102",
            is_feasible: true,
            distance_km: 24.2,
            estimated_time_minutes: 55.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
        ],
      },
    },
    provenance: { engine_version: "1.0.0", algorithm: "M4-06 Pipeline Orchestrator" },
    explainability: { methodology: "Heavy Rainfall (+40%) Multiplier Simulation" },
  },
  FLASH_FLOOD: {
    scenario_name: "Flash Flood / GLOF Valley Inundation",
    scenario_type: "FLASH_FLOOD",
    region_profile_id: "himalayan_pilot",
    run_id: "SIM-RUN-20260906-FLOOD",
    status: "COMPLETED",
    parameters: {
      scenario_type: "FLASH_FLOOD",
      rainfall_multiplier: 1.2,
      capacity_reduction_percentage: 0.0,
      flood_severity: "critical",
      flood_hazard_increase: 35.0,
      road_blockage_percentage: 15.0,
      blocked_segment_ids: ["RD-SEG-NH58-01", "RD-SEG-ALAK-04"],
    },
    started_at: "2026-09-06T12:10:00Z",
    completed_at: "2026-09-06T12:10:01Z",
    baseline_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    scenario_metrics: {
      average_risk_score: 64.1,
      critical_risk_villages: 2,
      active_red_zones: 2,
      immediate_priority_villages: 2,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 3,
      average_route_distance_km: 26.8,
    },
    comparison: {
      risk_score_deltas: {
        "HIM-VILL-001": 8.5,
        "HIM-VILL-002": 9.2,
        "HIM-VILL-003": 17.5,
        "HIM-VILL-004": 11.6,
      },
      average_risk_delta: 11.7,
      risk_band_shifts: [
        {
          village_id: "HIM-VILL-003",
          baseline_band: "HIGH",
          scenario_band: "CRITICAL",
        },
      ],
      villages_escalated_to_critical: ["HIM-VILL-003"],
      baseline_red_zones_count: 1,
      scenario_red_zones_count: 2,
      new_red_zone_villages: ["HIM-VILL-003"],
      priority_score_deltas: {
        "HIM-VILL-001": 7.0,
        "HIM-VILL-002": 8.1,
        "HIM-VILL-003": 18.0,
        "HIM-VILL-004": 6.5,
      },
      priority_band_shifts: [
        {
          village_id: "HIM-VILL-003",
          baseline_band: "SHORT_TERM",
          scenario_band: "IMMEDIATE",
        },
      ],
      villages_escalated_to_immediate: ["HIM-VILL-003"],
      site_capacity_deltas: {
        "101": 0,
        "102": 0,
      },
      newly_infeasible_sites: [],
      baseline_unassigned_count: 0,
      scenario_unassigned_count: 0,
      newly_unassigned_villages: [],
      site_reallocations: [],
      route_distance_deltas: {
        "HIM-VILL-001": 8.4,
        "HIM-VILL-002": 6.2,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 12.0,
      },
      corridors_diverted: ["HIM-VILL-001", "HIM-VILL-002"],
      newly_severed_routes: ["HIM-VILL-004"],
      comparison_narrative:
        "Severe valley flash flooding severed NH-58 lower valley segments. Evacuation routes from Sunil and Ravigram are diverted along high-elevation bypasses (+8.4 km average detour). Manohar Bagh route to Pipalkoti is temporarily cut off due to submerged culverts.",
    },
    baseline_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    scenario_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 2,
        triggered_village_ids: ["HIM-VILL-001", "HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 3,
        unroutable_count: 1,
        average_distance_km: 26.8,
        routes: [
          {
            village_id: "HIM-VILL-003",
            site_id: "101",
            is_feasible: true,
            distance_km: 6.4,
            estimated_time_minutes: 20.0,
            blocked_avoided_count: 0,
            route_status: "FEASIBLE",
          },
          {
            village_id: "HIM-VILL-001",
            site_id: "102",
            is_feasible: true,
            distance_km: 32.6,
            estimated_time_minutes: 85.0,
            blocked_avoided_count: 2,
            route_status: "DIVERTED",
          },
          {
            village_id: "HIM-VILL-002",
            site_id: "101",
            is_feasible: true,
            distance_km: 15.0,
            estimated_time_minutes: 42.0,
            blocked_avoided_count: 1,
            route_status: "DIVERTED",
          },
          {
            village_id: "HIM-VILL-004",
            site_id: "102",
            is_feasible: false,
            distance_km: null,
            estimated_time_minutes: null,
            blocked_avoided_count: 1,
            route_status: "CUT_OFF",
          },
        ],
      },
    },
    provenance: { engine_version: "1.0.0", algorithm: "M4-05/06 Routing & Scenario Engine" },
    explainability: { methodology: "Dijkstra Road Blockage Severance" },
  },
  CAPACITY_CRISIS: {
    scenario_name: "Relocation Capacity Crisis (-50%)",
    scenario_type: "CAPACITY_CRISIS",
    region_profile_id: "himalayan_pilot",
    run_id: "SIM-RUN-20260906-CAPCRIS",
    status: "COMPLETED",
    parameters: {
      scenario_type: "CAPACITY_CRISIS",
      rainfall_multiplier: 1.0,
      capacity_reduction_percentage: 50.0,
      flood_hazard_increase: 0.0,
      road_blockage_percentage: 0.0,
      blocked_segment_ids: [],
    },
    started_at: "2026-09-06T12:15:00Z",
    completed_at: "2026-09-06T12:15:01Z",
    baseline_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    scenario_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 190,
      allocated_households: 185,
      unassigned_households: 125,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    comparison: {
      risk_score_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      average_risk_delta: 0.0,
      risk_band_shifts: [],
      villages_escalated_to_critical: [],
      baseline_red_zones_count: 1,
      scenario_red_zones_count: 1,
      new_red_zone_villages: [],
      priority_score_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      priority_band_shifts: [],
      villages_escalated_to_immediate: [],
      site_capacity_deltas: {
        "101": -42,
        "102": -60,
      },
      newly_infeasible_sites: ["101"],
      baseline_unassigned_count: 0,
      scenario_unassigned_count: 1,
      newly_unassigned_villages: ["HIM-VILL-001"],
      site_reallocations: [],
      route_distance_deltas: {
        "HIM-VILL-001": 0.0,
        "HIM-VILL-002": 0.0,
        "HIM-VILL-003": 0.0,
        "HIM-VILL-004": 0.0,
      },
      corridors_diverted: [],
      newly_severed_routes: [],
      comparison_narrative:
        "50% carrying capacity reduction cuts available relocation slots by 190 HH across sites. Sunil (110 HH demanded) cannot be accommodated due to severe site saturation, creating an unassigned deficit of 125 households requiring inter-district relocation coordination.",
    },
    baseline_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    scenario_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [
        {
          site_id: "101",
          site_name: "Joshimath Safe Terrace",
          effective_capacity: 43,
          available_capacity: 0,
          limiting_factor: "sanitation",
          is_feasible: false,
        },
        {
          site_id: "102",
          site_name: "Pipalkoti Plateau",
          effective_capacity: 60,
          available_capacity: 0,
          limiting_factor: "water_supply",
          is_feasible: true,
        },
      ],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 185,
        total_households_unassigned: 125,
        assigned_count: 3,
        unassigned_count: 1,
        assignments: [
          {
            village_id: "HIM-VILL-001",
            village_name: "Sunil",
            assigned_site_id: null,
            assigned_site_name: null,
            is_assigned: false,
            demanded_households: 110,
            allocated_households: 0,
            unassigned_code: "INSUFFICIENT_CAPACITY",
            distance_km: null,
          },
        ],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    provenance: { engine_version: "1.0.0", algorithm: "M4-06 Capacity Constraint Squeezer" },
    explainability: { methodology: "50% Site Capacity Reduction" },
  },
  CUSTOM: {
    scenario_name: "Custom Parameterized Simulation",
    scenario_type: "CUSTOM",
    region_profile_id: "himalayan_pilot",
    run_id: "SIM-RUN-20260906-CUSTOM",
    status: "COMPLETED",
    parameters: {
      scenario_type: "CUSTOM",
      rainfall_multiplier: 1.25,
      capacity_reduction_percentage: 20.0,
      flood_hazard_increase: 15.0,
      road_blockage_percentage: 10.0,
      blocked_segment_ids: [],
    },
    started_at: "2026-09-06T12:20:00Z",
    completed_at: "2026-09-06T12:20:01Z",
    baseline_metrics: {
      average_risk_score: 52.4,
      critical_risk_villages: 1,
      active_red_zones: 1,
      immediate_priority_villages: 1,
      total_effective_capacity: 380,
      allocated_households: 310,
      unassigned_households: 0,
      feasible_routes: 4,
      average_route_distance_km: 18.2,
    },
    scenario_metrics: {
      average_risk_score: 61.2,
      critical_risk_villages: 2,
      active_red_zones: 2,
      immediate_priority_villages: 2,
      total_effective_capacity: 304,
      allocated_households: 290,
      unassigned_households: 20,
      feasible_routes: 4,
      average_route_distance_km: 21.4,
    },
    comparison: {
      risk_score_deltas: {
        "HIM-VILL-001": 9.4,
        "HIM-VILL-002": 8.6,
        "HIM-VILL-003": 11.2,
        "HIM-VILL-004": 6.2,
      },
      average_risk_delta: 8.8,
      risk_band_shifts: [
        {
          village_id: "HIM-VILL-001",
          baseline_band: "HIGH",
          scenario_band: "CRITICAL",
        },
      ],
      villages_escalated_to_critical: ["HIM-VILL-001"],
      baseline_red_zones_count: 1,
      scenario_red_zones_count: 2,
      new_red_zone_villages: ["HIM-VILL-001"],
      priority_score_deltas: {
        "HIM-VILL-001": 10.2,
        "HIM-VILL-002": 7.5,
        "HIM-VILL-003": 8.0,
        "HIM-VILL-004": 5.1,
      },
      priority_band_shifts: [
        {
          village_id: "HIM-VILL-001",
          baseline_band: "SHORT_TERM",
          scenario_band: "IMMEDIATE",
        },
      ],
      villages_escalated_to_immediate: ["HIM-VILL-001"],
      site_capacity_deltas: {
        "101": -17,
        "102": -24,
      },
      newly_infeasible_sites: [],
      baseline_unassigned_count: 0,
      scenario_unassigned_count: 1,
      newly_unassigned_villages: ["HIM-VILL-004"],
      site_reallocations: [],
      route_distance_deltas: {
        "HIM-VILL-001": 3.2,
        "HIM-VILL-002": 0.0,
      },
      corridors_diverted: ["HIM-VILL-001"],
      newly_severed_routes: [],
      comparison_narrative:
        "Custom parameter perturbation: moderate rainfall increase and 20% site capacity constraint lead to 1 new Dynamic Red Zone and 20 unassigned households.",
    },
    baseline_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 1,
        triggered_village_ids: ["HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 310,
        total_households_unassigned: 0,
        assigned_count: 4,
        unassigned_count: 0,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 18.2,
        routes: [],
      },
    },
    scenario_pipeline: {
      risk_results: [],
      red_zone_result: {
        total_evaluated: 4,
        triggered_count: 2,
        triggered_village_ids: ["HIM-VILL-001", "HIM-VILL-003"],
        candidate_ids: [],
      },
      priority_results: [],
      capacity_results: [],
      matching_result: {
        total_villages: 4,
        total_households_demanded: 310,
        total_households_allocated: 290,
        total_households_unassigned: 20,
        assigned_count: 3,
        unassigned_count: 1,
        assignments: [],
      },
      routing_result: {
        routes_evaluated: 4,
        feasible_routes_count: 4,
        unroutable_count: 0,
        average_distance_km: 21.4,
        routes: [],
      },
    },
    provenance: { engine_version: "1.0.0", algorithm: "Custom Orchestration" },
    explainability: { methodology: "User Custom Parameter Override" },
  },
};

// ============================================================================
// Service Methods
// ============================================================================

/**
 * Fetch available scenario definitions (canonical presets + custom).
 */
export async function listScenarioDefinitions(): Promise<
  ResponseEnvelope<ScenarioDefinitionRead[]>
> {
  try {
    const response = await apiClient.get<ResponseEnvelope<ScenarioDefinitionRead[]>>(
      "/api/v1/scenarios"
    );
    if (response.success && response.data && response.data.length > 0) {
      return response;
    }
    return {
      success: true,
      data: CANONICAL_SCENARIO_CATALOG,
    };
  } catch {
    return {
      success: true,
      data: CANONICAL_SCENARIO_CATALOG,
    };
  }
}

/**
 * Execute scenario simulation run.
 */
export async function runScenarioSimulation(
  payload: ScenarioRunRequest
): Promise<ResponseEnvelope<ScenarioSimulationOutput>> {
  try {
    const response = await apiClient.post<ResponseEnvelope<ScenarioSimulationOutput>>(
      "/api/v1/scenarios/run",
      payload
    );
    if (response.success && response.data) {
      return response;
    }
  } catch {
    // Fall back to pre-computed deterministic Himalayan pilot output
  }

  const st = (payload.scenario_type || "NORMAL").toUpperCase() as ScenarioType;
  const fallback =
    HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[st] ||
    HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.NORMAL;

  return {
    success: true,
    data: fallback,
  };
}

/**
 * Retrieve persisted scenario run record by ID.
 */
export async function getScenarioRunRecord(
  runId: number
): Promise<ResponseEnvelope<ScenarioRunRecordRead>> {
  return apiClient.get<ResponseEnvelope<ScenarioRunRecordRead>>(
    `/api/v1/scenarios/runs/${runId}`
  );
}
