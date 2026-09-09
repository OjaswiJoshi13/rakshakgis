/**
 * Relocation API Service & Networking (Chunk M6-02)
 * Dispatches typed HTTP operations against backend Chunk M4-04 endpoints.
 */

import { apiClient } from "./client";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
import {
  RelocationAssignmentBatchCreate,
  RelocationAssignmentCreate,
  RelocationAssignmentRead,
  RelocationMatchingRequest,
  RelocationMatchingResult,
} from "@/types/relocation";

/**
 * Executes deterministic relocation matching evaluation via POST /api/v1/relocation/match.
 * Pure evaluation (zero database mutations).
 */
export async function evaluateRelocationMatching(
  request: RelocationMatchingRequest
): Promise<ResponseEnvelope<RelocationMatchingResult>> {
  return apiClient.post<ResponseEnvelope<RelocationMatchingResult>>(
    "/api/v1/relocation/match",
    request
  );
}

/**
 * Retrieves paginated persisted relocation assignments via GET /api/v1/relocation/assignments.
 */
export async function listRelocationAssignments(params?: {
  page?: number;
  page_size?: number;
  village_id?: number;
  candidate_site_id?: number;
  status?: string;
}): Promise<PaginatedResponse<RelocationAssignmentRead>> {
  return apiClient.get<PaginatedResponse<RelocationAssignmentRead>>(
    "/api/v1/relocation/assignments",
    { params }
  );
}

/**
 * Persists a single village-to-site relocation assignment via POST /api/v1/relocation/assignments.
 */
export async function createRelocationAssignment(
  payload: RelocationAssignmentCreate
): Promise<ResponseEnvelope<RelocationAssignmentRead>> {
  return apiClient.post<ResponseEnvelope<RelocationAssignmentRead>>(
    "/api/v1/relocation/assignments",
    payload
  );
}

/**
 * Batch persists relocation assignments via POST /api/v1/relocation/assignments/batch.
 */
export async function batchCreateRelocationAssignments(
  payload: RelocationAssignmentBatchCreate
): Promise<ResponseEnvelope<RelocationAssignmentRead[]>> {
  return apiClient.post<ResponseEnvelope<RelocationAssignmentRead[]>>(
    "/api/v1/relocation/assignments/batch",
    payload
  );
}

/**
 * Authoritative Himalayan Pilot (Chamoli) sample matching evaluation result.
 * Used for offline verification, unit tests, and demonstration fallback.
 * Strictly adheres to M4-04 RelocationMatchingResult schema.
 */
export const HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT: RelocationMatchingResult = {
  matching_id: "match-chamoli-pilot-001",
  algorithm: "greedy_priority",
  total_villages: 4,
  assigned_villages_count: 3,
  unassigned_villages_count: 1,
  total_households_demanded: 155,
  total_households_allocated: 105,
  total_households_unassigned: 50,
  site_remaining_capacities: {
    "site-101": 8,   // Joshimath Safe Terrace (Initial 85 - 42 - 35 = 8)
    "site-102": 32,  // Pipalkoti Plateau (Initial 60 - 28 = 32)
    "site-103": 0,   // Urgam Safe Zone (Unsuitable - 0 allocated)
  },
  summary_narrative:
    "Evaluated 4 prioritized Chamoli villages against 3 candidate relocation sites. 3 villages successfully matched (105 households allocated). 1 village remains unassigned due to site carrying capacity exhaustion across eligible candidates.",
  execution_timestamp: "2026-09-06T12:00:00Z",
  region_profile_id: "himalayan_pilot",
  governance_notice:
    "DECISION SUPPORT ONLY: Relocation matching recommendations are deterministic planning proposals for District Magistrate, District Officer, and Rehabilitation Committee sign-off. They do NOT constitute an automatic legal eviction or mandatory relocation order.",
  assignments: [
    {
      village_id: 1,
      village_name: "Raini",
      priority_score: 94.5,
      priority_band: "immediate",
      incoming_households: 42,
      incoming_population: 178,
      status: "assigned",
      assigned_site_id: "site-101",
      assigned_site_name: "Joshimath Safe Terrace",
      suitability_score: 88.2,
      distance_km: 8.4,
      available_capacity_before: 85,
      available_capacity_after: 43,
      selection_reason:
        "Ranked #1 candidate: highest composite suitability (88.2) within 10km radius with 85 available household capacity.",
      unassigned_reason: null,
      unassigned_code: null,
      evaluated_candidates: [
        {
          site_id: "site-101",
          site_name: "Joshimath Safe Terrace",
          is_feasible: true,
          rejection_code: null,
          rejection_reasons: [],
          suitability_score: 88.2,
          suitability_decision: "suitable",
          available_capacity_before: 85,
          capacity_margin: 43,
          distance_km: 8.4,
          rank_score: 85.1,
        },
        {
          site_id: "site-102",
          site_name: "Pipalkoti Plateau",
          is_feasible: true,
          rejection_code: null,
          rejection_reasons: [],
          suitability_score: 81.5,
          suitability_decision: "suitable",
          available_capacity_before: 60,
          capacity_margin: 18,
          distance_km: 19.8,
          rank_score: 72.4,
        },
        {
          site_id: "site-103",
          site_name: "Urgam North Ridge",
          is_feasible: false,
          rejection_code: "unsafe_site",
          rejection_reasons: [
            "Safety constraint failed: Site is within the active hazard buffer perimeter.",
          ],
          suitability_score: 41.0,
          suitability_decision: "unsuitable",
          available_capacity_before: 50,
          capacity_margin: null,
          distance_km: 12.1,
          rank_score: null,
        },
      ],
    },
    {
      village_id: 2,
      village_name: "Peng",
      priority_score: 86.2,
      priority_band: "immediate",
      incoming_households: 35,
      incoming_population: 142,
      status: "assigned",
      assigned_site_id: "site-101",
      assigned_site_name: "Joshimath Safe Terrace",
      suitability_score: 88.2,
      distance_km: 11.2,
      available_capacity_before: 43,
      available_capacity_after: 8,
      selection_reason:
        "Ranked #1 candidate: highest composite suitability (88.2) with 43 remaining capacity sufficient for 35 households.",
      unassigned_reason: null,
      unassigned_code: null,
      evaluated_candidates: [
        {
          site_id: "site-101",
          site_name: "Joshimath Safe Terrace",
          is_feasible: true,
          rejection_code: null,
          rejection_reasons: [],
          suitability_score: 88.2,
          suitability_decision: "suitable",
          available_capacity_before: 43,
          capacity_margin: 8,
          distance_km: 11.2,
          rank_score: 82.3,
        },
        {
          site_id: "site-102",
          site_name: "Pipalkoti Plateau",
          is_feasible: true,
          rejection_code: null,
          rejection_reasons: [],
          suitability_score: 81.5,
          suitability_decision: "suitable",
          available_capacity_before: 60,
          capacity_margin: 25,
          distance_km: 21.0,
          rank_score: 70.9,
        },
      ],
    },
    {
      village_id: 3,
      village_name: "Tapovan Upper",
      priority_score: 78.4,
      priority_band: "short_term",
      incoming_households: 28,
      incoming_population: 110,
      status: "assigned",
      assigned_site_id: "site-102",
      assigned_site_name: "Pipalkoti Plateau",
      suitability_score: 81.5,
      distance_km: 16.5,
      available_capacity_before: 60,
      available_capacity_after: 32,
      selection_reason:
        "Allocated to Pipalkoti Plateau after Joshimath Safe Terrace had insufficient remaining capacity (8 available < 28 required).",
      unassigned_reason: null,
      unassigned_code: null,
      evaluated_candidates: [
        {
          site_id: "site-101",
          site_name: "Joshimath Safe Terrace",
          is_feasible: false,
          rejection_code: "insufficient_capacity",
          rejection_reasons: [
            "Insufficient capacity: Available 8 households < required 28 households (deficit of 20 households).",
          ],
          suitability_score: 88.2,
          suitability_decision: "suitable",
          available_capacity_before: 8,
          capacity_margin: -20,
          distance_km: 6.8,
          rank_score: null,
        },
        {
          site_id: "site-102",
          site_name: "Pipalkoti Plateau",
          is_feasible: true,
          rejection_code: null,
          rejection_reasons: [],
          suitability_score: 81.5,
          suitability_decision: "suitable",
          available_capacity_before: 60,
          capacity_margin: 32,
          distance_km: 16.5,
          rank_score: 74.5,
        },
      ],
    },
    {
      village_id: 4,
      village_name: "Malari Outpost",
      priority_score: 71.0,
      priority_band: "short_term",
      incoming_households: 50,
      incoming_population: 210,
      status: "unassigned",
      assigned_site_id: null,
      assigned_site_name: null,
      suitability_score: null,
      distance_km: null,
      available_capacity_before: null,
      available_capacity_after: null,
      selection_reason: null,
      unassigned_reason:
        "No candidate site possesses adequate remaining carrying capacity to house 50 households without exceeding safety limits.",
      unassigned_code: "insufficient_capacity",
      evaluated_candidates: [
        {
          site_id: "site-101",
          site_name: "Joshimath Safe Terrace",
          is_feasible: false,
          rejection_code: "insufficient_capacity",
          rejection_reasons: [
            "Insufficient capacity: Available 8 households < required 50 households (deficit of 42 households).",
          ],
          suitability_score: 88.2,
          suitability_decision: "suitable",
          available_capacity_before: 8,
          capacity_margin: -42,
          distance_km: 32.1,
          rank_score: null,
        },
        {
          site_id: "site-102",
          site_name: "Pipalkoti Plateau",
          is_feasible: false,
          rejection_code: "insufficient_capacity",
          rejection_reasons: [
            "Insufficient capacity: Available 32 households < required 50 households (deficit of 18 households).",
          ],
          suitability_score: 81.5,
          suitability_decision: "suitable",
          available_capacity_before: 32,
          capacity_margin: -18,
          distance_km: 44.5,
          rank_score: null,
        },
        {
          site_id: "site-103",
          site_name: "Urgam North Ridge",
          is_feasible: false,
          rejection_code: "unsafe_site",
          rejection_reasons: [
            "Safety constraint failed: Site is within the active hazard buffer perimeter.",
          ],
          suitability_score: 41.0,
          suitability_decision: "unsuitable",
          available_capacity_before: 50,
          capacity_margin: null,
          distance_km: 38.0,
          rank_score: null,
        },
      ],
    },
  ],
};

export const HIMALAYAN_PILOT_SAMPLE_ASSIGNMENTS: RelocationAssignmentRead[] = [
  {
    id: 1001,
    village_id: 1,
    village_name: "Raini",
    candidate_site_id: 101,
    candidate_site_name: "Joshimath Safe Terrace",
    assigned_households: 42,
    assigned_population: 178,
    status: "draft",
    approved_by_officer_id: null,
    assigned_at: "2026-09-06T12:05:00Z",
    updated_at: "2026-09-06T12:05:00Z",
  },
  {
    id: 1002,
    village_id: 2,
    village_name: "Peng",
    candidate_site_id: 101,
    candidate_site_name: "Joshimath Safe Terrace",
    assigned_households: 35,
    assigned_population: 142,
    status: "draft",
    approved_by_officer_id: null,
    assigned_at: "2026-09-06T12:05:00Z",
    updated_at: "2026-09-06T12:05:00Z",
  },
  {
    id: 1003,
    village_id: 3,
    village_name: "Tapovan Upper",
    candidate_site_id: 102,
    candidate_site_name: "Pipalkoti Plateau",
    assigned_households: 28,
    assigned_population: 110,
    status: "draft",
    approved_by_officer_id: null,
    assigned_at: "2026-09-06T12:05:00Z",
    updated_at: "2026-09-06T12:05:00Z",
  },
];
