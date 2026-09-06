/**
 * Candidate Relocation Sites API Service (Chunk M6-03)
 * Dispatches typed HTTP operations against backend Chunk M4-01, M4-02, and M4-03 endpoints.
 */

import { apiClient } from "./client";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
import {
  CandidateSiteDetailRead,
  CandidateSiteRead,
  SiteCapacityResult,
  SiteSuitabilityResult,
} from "@/types/sites";

/**
 * Retrieves paginated candidate relocation sites via GET /api/v1/sites.
 */
export async function listCandidateSites(params?: {
  page?: number;
  page_size?: number;
  district_id?: number;
  status?: string;
  search?: string;
}): Promise<PaginatedResponse<CandidateSiteRead>> {
  return apiClient.get<PaginatedResponse<CandidateSiteRead>>("/api/v1/sites", {
    params,
  });
}

/**
 * Retrieves detailed candidate site record including capacities and infrastructure assets via GET /api/v1/sites/{id}.
 */
export async function getCandidateSiteDetail(
  id: number
): Promise<ResponseEnvelope<CandidateSiteDetailRead>> {
  return apiClient.get<ResponseEnvelope<CandidateSiteDetailRead>>(
    `/api/v1/sites/${id}`
  );
}

/**
 * Retrieves M4-02 multi-criteria suitability evaluation for a candidate site via GET /api/v1/sites/{id}/suitability.
 */
export async function getCandidateSiteSuitability(
  id: number,
  regionProfileId: string = "himalayan_pilot"
): Promise<ResponseEnvelope<SiteSuitabilityResult>> {
  return apiClient.get<ResponseEnvelope<SiteSuitabilityResult>>(
    `/api/v1/sites/${id}/suitability`,
    {
      params: { region_profile_id: regionProfileId },
    }
  );
}

/**
 * Retrieves M4-03 carrying capacity and infrastructure sizing evaluation via GET /api/v1/sites/{id}/capacity.
 */
export async function getCandidateSiteCapacity(
  id: number,
  incomingHouseholds: number = 0,
  regionProfileId: string = "himalayan_pilot"
): Promise<ResponseEnvelope<SiteCapacityResult>> {
  return apiClient.get<ResponseEnvelope<SiteCapacityResult>>(
    `/api/v1/sites/${id}/capacity`,
    {
      params: {
        incoming_households: incomingHouseholds,
        region_profile_id: regionProfileId,
      },
    }
  );
}

/**
 * Authoritative Himalayan Pilot (Chamoli) sample sites dataset for testing and fallback.
 */
export const HIMALAYAN_PILOT_SAMPLE_SITES: CandidateSiteRead[] = [
  {
    id: 101,
    name: "Joshimath Safe Terrace",
    district_id: 1,
    location: { type: "Point", coordinates: [79.563, 30.556] },
    area_sq_m: 120000,
    terrain_slope_deg: 8.5,
    elevation_m: 1890,
    status: "approved",
    created_at: "2026-09-04T10:00:00Z",
    updated_at: "2026-09-06T12:00:00Z",
  },
  {
    id: 102,
    name: "Pipalkoti Plateau",
    district_id: 1,
    location: { type: "Point", coordinates: [79.432, 30.428] },
    area_sq_m: 95000,
    terrain_slope_deg: 11.2,
    elevation_m: 1350,
    status: "approved",
    created_at: "2026-09-04T10:00:00Z",
    updated_at: "2026-09-06T12:00:00Z",
  },
  {
    id: 103,
    name: "Urgam North Ridge",
    district_id: 1,
    location: { type: "Point", coordinates: [79.489, 30.592] },
    area_sq_m: 78000,
    terrain_slope_deg: 18.4,
    elevation_m: 2120,
    status: "rejected",
    created_at: "2026-09-04T10:00:00Z",
    updated_at: "2026-09-06T12:00:00Z",
  },
];

export const HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS: Record<
  number,
  CandidateSiteDetailRead
> = {
  101: {
    ...HIMALAYAN_PILOT_SAMPLE_SITES[0],
    capacities: [
      {
        id: 201,
        site_id: 101,
        max_households: 85,
        max_population: 360,
        allocated_households: 77,
        allocated_population: 320,
        available_households: 8,
        available_population: 40,
        water_supply_lpd: 35000,
        sanitation_units: 25,
        updated_at: "2026-09-06T12:00:00Z",
      },
    ],
    infrastructures: [
      {
        id: 301,
        site_id: 101,
        name: "Joshimath Gravity Water Supply",
        infra_type: "water_supply",
        status: "functional",
        location: { type: "Point", coordinates: [79.564, 30.557] },
        capacity_description: "35,000 LPD filtered natural spring intake",
        created_at: "2026-09-04T10:00:00Z",
      },
      {
        id: 302,
        site_id: 101,
        name: "Helipad & Emergency Evacuation Staging Point",
        infra_type: "emergency_shelter",
        status: "functional",
        location: { type: "Point", coordinates: [79.562, 30.555] },
        capacity_description: "Mi-17 heavy helicopter pad with 200-person weather shelter",
        created_at: "2026-09-04T10:00:00Z",
      },
      {
        id: 303,
        site_id: 101,
        name: "Joshimath Terrace Access Road",
        infra_type: "road_access",
        status: "functional",
        location: { type: "Point", coordinates: [79.561, 30.554] },
        capacity_description: "Double-lane paved blacktop corridor (5.5m width)",
        created_at: "2026-09-04T10:00:00Z",
      },
      {
        id: 304,
        site_id: 101,
        name: "Primary Health Sub-Center",
        infra_type: "health_clinic",
        status: "functional",
        location: { type: "Point", coordinates: [79.565, 30.558] },
        capacity_description: "4-bed emergency triage and stabilization facility",
        created_at: "2026-09-04T10:00:00Z",
      },
    ],
  },
  102: {
    ...HIMALAYAN_PILOT_SAMPLE_SITES[1],
    capacities: [
      {
        id: 202,
        site_id: 102,
        max_households: 60,
        max_population: 250,
        allocated_households: 28,
        allocated_population: 110,
        available_households: 32,
        available_population: 140,
        water_supply_lpd: 22000,
        sanitation_units: 18,
        updated_at: "2026-09-06T12:00:00Z",
      },
    ],
    infrastructures: [
      {
        id: 305,
        site_id: 102,
        name: "Pipalkoti Lift Water System",
        infra_type: "water_supply",
        status: "functional",
        location: { type: "Point", coordinates: [79.433, 30.429] },
        capacity_description: "22,000 LPD municipal pump intake",
        created_at: "2026-09-04T10:00:00Z",
      },
      {
        id: 306,
        site_id: 102,
        name: "Pipalkoti NH-07 Connector",
        infra_type: "road_access",
        status: "functional",
        location: { type: "Point", coordinates: [79.431, 30.427] },
        capacity_description: "Single-lane paved spur (3.75m width)",
        created_at: "2026-09-04T10:00:00Z",
      },
    ],
  },
  103: {
    ...HIMALAYAN_PILOT_SAMPLE_SITES[2],
    capacities: [
      {
        id: 203,
        site_id: 103,
        max_households: 50,
        max_population: 200,
        allocated_households: 0,
        allocated_population: 0,
        available_households: 50,
        available_population: 200,
        water_supply_lpd: 12000,
        sanitation_units: 10,
        updated_at: "2026-09-06T12:00:00Z",
      },
    ],
    infrastructures: [
      {
        id: 307,
        site_id: 103,
        name: "Urgam Dirt Track",
        infra_type: "road_access",
        status: "damaged",
        location: { type: "Point", coordinates: [79.49, 30.593] },
        capacity_description: "Unpaved track impassable during torrential rain",
        created_at: "2026-09-04T10:00:00Z",
      },
    ],
  },
};

export const HIMALAYAN_PILOT_SAMPLE_SUITABILITY: Record<
  number,
  SiteSuitabilityResult
> = {
  101: {
    site_id: 101,
    site_name: "Joshimath Safe Terrace",
    is_eligible: true,
    decision: "suitable",
    overall_score: 88.2,
    criteria_scores: {
      hazard_safety: {
        criterion: "hazard_safety",
        criterion_name: "Hazard Safety",
        raw_score: 92.0,
        weight: 0.3,
        weighted_contribution: 27.6,
        description: "Terrain slope 8.5° safely under 15° limit; hazard buffer 850m > 500m.",
      },
      capacity: {
        criterion: "capacity",
        criterion_name: "Capacity & Resource Limits",
        raw_score: 85.0,
        weight: 0.2,
        weighted_contribution: 17.0,
        description: "85 household capacity with 120,000 sq m habitable area.",
      },
      road_access: {
        criterion: "road_access",
        criterion_name: "Road & Transport Access",
        raw_score: 88.0,
        weight: 0.1,
        weighted_contribution: 8.8,
        description: "5.5m double-lane paved road corridor within 1.2km of highway.",
      },
      water_availability: {
        criterion: "water_availability",
        criterion_name: "Water Availability",
        raw_score: 97.2,
        weight: 0.1,
        weighted_contribution: 9.7,
        description: "97.2 LPD/capita exceeds statutory requirement of 70 LPD/capita.",
      },
      healthcare_access: {
        criterion: "healthcare_access",
        criterion_name: "Healthcare Access",
        raw_score: 80.0,
        weight: 0.1,
        weighted_contribution: 8.0,
        description: "Primary Health Sub-Center located directly on site.",
      },
      school_access: {
        criterion: "school_access",
        criterion_name: "School Access",
        raw_score: 75.0,
        weight: 0.05,
        weighted_contribution: 3.8,
        description: "Government Senior Secondary School within 2.1km.",
      },
      emergency_services: {
        criterion: "emergency_services",
        criterion_name: "Emergency Services",
        raw_score: 90.0,
        weight: 0.05,
        weighted_contribution: 4.5,
        description: "Helipad and civil defense post available on site.",
      },
      livelihood_access: {
        criterion: "livelihood_access",
        criterion_name: "Livelihood Access",
        raw_score: 80.0,
        weight: 0.05,
        weighted_contribution: 4.0,
        description: "Terraced agricultural land and pilgrimage tourism employment nearby.",
      },
      expansion_potential: {
        criterion: "expansion_potential",
        criterion_name: "Expansion Potential",
        raw_score: 95.0,
        weight: 0.05,
        weighted_contribution: 4.8,
        description: "Ample contiguous crown land available for Phase 2 expansion.",
      },
    },
    hard_constraints: [
      {
        constraint_type: "hazard_slope",
        name: "Terrain Slope <= 15°",
        passed: true,
        actual_value: 8.5,
        threshold_value: 15.0,
        reason: "Slope 8.5° is within safe limit.",
      },
      {
        constraint_type: "hazard_buffer",
        name: "Hazard Buffer >= 500m",
        passed: true,
        actual_value: 850,
        threshold_value: 500,
        reason: "Buffer distance 850m satisfies minimum safety buffer.",
      },
      {
        constraint_type: "usable_capacity",
        name: "Usable Capacity >= 20 HH",
        passed: true,
        actual_value: 85,
        threshold_value: 20,
        reason: "Capacity 85 HH exceeds minimum settlement threshold.",
      },
    ],
    failed_constraints: [],
    summary_reasons: [
      "All hard safety constraints passed.",
      "High composite suitability score (88.2/100).",
      "On-site water and emergency shelter assets verified operational.",
    ],
    evaluated_at: "2026-09-06T12:00:00Z",
    config_version: "1.0.0",
  },
  102: {
    site_id: 102,
    site_name: "Pipalkoti Plateau",
    is_eligible: true,
    decision: "suitable",
    overall_score: 81.5,
    criteria_scores: {
      hazard_safety: {
        criterion: "hazard_safety",
        criterion_name: "Hazard Safety",
        raw_score: 84.0,
        weight: 0.3,
        weighted_contribution: 25.2,
        description: "Terrain slope 11.2°; buffer distance 620m.",
      },
      capacity: {
        criterion: "capacity",
        criterion_name: "Capacity & Resource Limits",
        raw_score: 75.0,
        weight: 0.2,
        weighted_contribution: 15.0,
        description: "60 household capacity with 95,000 sq m area.",
      },
      road_access: {
        criterion: "road_access",
        criterion_name: "Road & Transport Access",
        raw_score: 85.0,
        weight: 0.1,
        weighted_contribution: 8.5,
        description: "Direct connection to NH-07 within 400m.",
      },
      water_availability: {
        criterion: "water_availability",
        criterion_name: "Water Availability",
        raw_score: 88.0,
        weight: 0.1,
        weighted_contribution: 8.8,
        description: "88 LPD/capita from municipal intake.",
      },
      healthcare_access: {
        criterion: "healthcare_access",
        criterion_name: "Healthcare Access",
        raw_score: 70.0,
        weight: 0.1,
        weighted_contribution: 7.0,
        description: "Pipalkoti Community Health Centre 2.5km away.",
      },
      school_access: {
        criterion: "school_access",
        criterion_name: "School Access",
        raw_score: 80.0,
        weight: 0.05,
        weighted_contribution: 4.0,
        description: "Primary school within 1.0km.",
      },
      emergency_services: {
        criterion: "emergency_services",
        criterion_name: "Emergency Services",
        raw_score: 70.0,
        weight: 0.05,
        weighted_contribution: 3.5,
        description: "Police post within 1.5km.",
      },
      livelihood_access: {
        criterion: "livelihood_access",
        criterion_name: "Livelihood Access",
        raw_score: 85.0,
        weight: 0.05,
        weighted_contribution: 4.3,
        description: "Commercial highway access and artisan shops.",
      },
      expansion_potential: {
        criterion: "expansion_potential",
        criterion_name: "Expansion Potential",
        raw_score: 70.0,
        weight: 0.05,
        weighted_contribution: 3.5,
        description: "Moderate expansion potential bounded by forest reserve.",
      },
    },
    hard_constraints: [
      {
        constraint_type: "hazard_slope",
        name: "Terrain Slope <= 15°",
        passed: true,
        actual_value: 11.2,
        threshold_value: 15.0,
        reason: "Slope 11.2° is within safe limit.",
      },
      {
        constraint_type: "hazard_buffer",
        name: "Hazard Buffer >= 500m",
        passed: true,
        actual_value: 620,
        threshold_value: 500,
        reason: "Buffer distance 620m satisfies minimum safety buffer.",
      },
      {
        constraint_type: "usable_capacity",
        name: "Usable Capacity >= 20 HH",
        passed: true,
        actual_value: 60,
        threshold_value: 20,
        reason: "Capacity 60 HH exceeds minimum settlement threshold.",
      },
    ],
    failed_constraints: [],
    summary_reasons: [
      "All hard safety constraints passed.",
      "Good overall suitability score (81.5/100).",
    ],
    evaluated_at: "2026-09-06T12:00:00Z",
    config_version: "1.0.0",
  },
  103: {
    site_id: 103,
    site_name: "Urgam North Ridge",
    is_eligible: false,
    decision: "unsuitable",
    overall_score: 41.0,
    criteria_scores: {
      hazard_safety: {
        criterion: "hazard_safety",
        criterion_name: "Hazard Safety",
        raw_score: 25.0,
        weight: 0.3,
        weighted_contribution: 7.5,
        description: "Excessive slope (18.4°) and active landslide scar within 320m.",
      },
      capacity: {
        criterion: "capacity",
        criterion_name: "Capacity & Resource Limits",
        raw_score: 50.0,
        weight: 0.2,
        weighted_contribution: 10.0,
        description: "50 household capacity.",
      },
      road_access: {
        criterion: "road_access",
        criterion_name: "Road & Transport Access",
        raw_score: 30.0,
        weight: 0.1,
        weighted_contribution: 3.0,
        description: "Unpaved damaged dirt track prone to blockages.",
      },
      water_availability: {
        criterion: "water_availability",
        criterion_name: "Water Availability",
        raw_score: 60.0,
        weight: 0.1,
        weighted_contribution: 6.0,
        description: "Seasonal brook water supply.",
      },
      healthcare_access: {
        criterion: "healthcare_access",
        criterion_name: "Healthcare Access",
        raw_score: 35.0,
        weight: 0.1,
        weighted_contribution: 3.5,
        description: "Nearest medical clinic over 12km away.",
      },
      school_access: {
        criterion: "school_access",
        criterion_name: "School Access",
        raw_score: 40.0,
        weight: 0.05,
        weighted_contribution: 2.0,
        description: "School 8km away.",
      },
      emergency_services: {
        criterion: "emergency_services",
        criterion_name: "Emergency Services",
        raw_score: 30.0,
        weight: 0.05,
        weighted_contribution: 1.5,
        description: "No dedicated emergency infrastructure.",
      },
      livelihood_access: {
        criterion: "livelihood_access",
        criterion_name: "Livelihood Access",
        raw_score: 45.0,
        weight: 0.05,
        weighted_contribution: 2.3,
        description: "Limited subsistence terrace farming.",
      },
      expansion_potential: {
        criterion: "expansion_potential",
        criterion_name: "Expansion Potential",
        raw_score: 35.0,
        weight: 0.05,
        weighted_contribution: 1.8,
        description: "Severely restricted by surrounding cliff terrain.",
      },
    },
    hard_constraints: [
      {
        constraint_type: "hazard_slope",
        name: "Terrain Slope <= 15°",
        passed: false,
        actual_value: 18.4,
        threshold_value: 15.0,
        reason: "Failed: Slope 18.4° exceeds maximum safe limit of 15.0°.",
      },
      {
        constraint_type: "hazard_buffer",
        name: "Hazard Buffer >= 500m",
        passed: false,
        actual_value: 320,
        threshold_value: 500,
        reason: "Failed: Hazard buffer 320m is below mandatory 500m buffer.",
      },
      {
        constraint_type: "usable_capacity",
        name: "Usable Capacity >= 20 HH",
        passed: true,
        actual_value: 50,
        threshold_value: 20,
        reason: "Capacity 50 HH meets minimum threshold.",
      },
    ],
    failed_constraints: ["hazard_slope", "hazard_buffer"],
    summary_reasons: [
      "Hard safety constraints failed: hazard_slope and hazard_buffer.",
      "Overall suitability score (41.0/100) below acceptable threshold.",
      "Classified as UNSUITABLE for permanent relocation.",
    ],
    evaluated_at: "2026-09-06T12:00:00Z",
    config_version: "1.0.0",
  },
};

export const HIMALAYAN_PILOT_SAMPLE_CAPACITY: Record<
  number,
  SiteCapacityResult
> = {
  101: {
    site_id: 101,
    site_name: "Joshimath Safe Terrace",
    effective_capacity_households: 85,
    current_occupancy_households: 77,
    available_capacity_households: 8,
    incoming_households: 0,
    capacity_margin_households: 8,
    remaining_capacity_households: 8,
    feasible: true,
    limiting_factors: ["housing"],
    unknown_dimensions: [],
    infrastructure_results: {
      housing: {
        dimension: "housing",
        dimension_name: "Habitable Land & Housing",
        current_capacity: 85,
        required_capacity: 77,
        deficit: 0,
        is_adequate: true,
        unit: "HH",
      },
      water: {
        dimension: "water",
        dimension_name: "Water Supply (70 LPD/capita)",
        current_capacity: 119,
        required_capacity: 77,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
      sanitation: {
        dimension: "sanitation",
        dimension_name: "Sanitation Facilities",
        current_capacity: 100,
        required_capacity: 77,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
      healthcare: {
        dimension: "healthcare",
        dimension_name: "Healthcare Capacity",
        current_capacity: 150,
        required_capacity: 77,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
      shelter: {
        dimension: "shelter",
        dimension_name: "Emergency Shelter",
        current_capacity: 95,
        required_capacity: 77,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
    },
    deficits: {},
    assumptions: {
      water_lpd_per_capita: 70.0,
      sanitation_persons_per_unit: 20,
      shelter_area_sq_m_per_person: 3.5,
    },
    reasons: [
      "Authoritative weakest-link formula min(housing, water, sanitation, healthcare, shelter) evaluated.",
      "Bottleneck limiting factor is Habitable Land & Housing (85 HH capacity).",
      "Available margin: 8 households remaining.",
    ],
  },
  102: {
    site_id: 102,
    site_name: "Pipalkoti Plateau",
    effective_capacity_households: 60,
    current_occupancy_households: 28,
    available_capacity_households: 32,
    incoming_households: 0,
    capacity_margin_households: 32,
    remaining_capacity_households: 32,
    feasible: true,
    limiting_factors: ["housing"],
    unknown_dimensions: [],
    infrastructure_results: {
      housing: {
        dimension: "housing",
        dimension_name: "Habitable Land & Housing",
        current_capacity: 60,
        required_capacity: 28,
        deficit: 0,
        is_adequate: true,
        unit: "HH",
      },
      water: {
        dimension: "water",
        dimension_name: "Water Supply (70 LPD/capita)",
        current_capacity: 75,
        required_capacity: 28,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
      sanitation: {
        dimension: "sanitation",
        dimension_name: "Sanitation Facilities",
        current_capacity: 72,
        required_capacity: 28,
        deficit: 0,
        is_adequate: true,
        unit: "HH equivalent",
      },
    },
    deficits: {},
    assumptions: {
      water_lpd_per_capita: 70.0,
    },
    reasons: [
      "Bottleneck limiting factor is Habitable Land & Housing (60 HH capacity).",
      "Available margin: 32 households remaining.",
    ],
  },
  103: {
    site_id: 103,
    site_name: "Urgam North Ridge",
    effective_capacity_households: 0,
    current_occupancy_households: 0,
    available_capacity_households: 0,
    incoming_households: 0,
    capacity_margin_households: 0,
    remaining_capacity_households: 0,
    feasible: false,
    limiting_factors: ["hazard_safety"],
    unknown_dimensions: [],
    infrastructure_results: {
      housing: {
        dimension: "housing",
        dimension_name: "Habitable Land & Housing",
        current_capacity: 0,
        required_capacity: 0,
        deficit: 0,
        is_adequate: false,
        unit: "HH",
      },
    },
    deficits: {},
    assumptions: {},
    reasons: [
      "Site is designated INELIGIBLE due to hard slope failure; zero capacity recognized.",
    ],
  },
};
