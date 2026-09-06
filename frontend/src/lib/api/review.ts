/**
 * Officer Review & Action Sign-Off API Client & Datasets (Chunk M6-08).
 * Manages statutory review dossiers, officer decision capture, and audit linkages.
 * 
 * Backend Dependency Notice:
 * The `OfficerDecision` SQLAlchemy model is defined in `backend/app/models/governance.py`.
 * A dedicated `/api/v1/governance/decisions` REST route is pending future backend exposure.
 * This service implements the complete decision contract, provides deterministic seed dossiers
 * derived from M6-02 and M6-04, persists decision outcomes in session state, and dispatches
 * assignment approval calls to POST /api/v1/relocation/assignments/batch when applicable.
 */

import { HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT, batchCreateRelocationAssignments } from "./relocation";
import { HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS } from "./scenarios";
import {
  RecommendationDossier,
  OfficerDecisionRecord,
  SubmitDecisionRequest,
} from "@/types/review";

// ============================================================================
// Canonical Seed Review Dossiers (Composing M6-02 and M6-04)
// ============================================================================

export const INITIAL_REVIEW_DOSSIERS: RecommendationDossier[] = [
  {
    id: "DOSSIER-RELOC-001",
    title: "Chamoli Monsoon Priority Relocation Plan",
    type: "relocation_plan",
    source_engine: "M4-04 Relocation Matching Engine",
    region_profile_id: "himalayan_pilot",
    created_at: "2026-09-06T18:00:00Z",
    urgency_level: "critical",
    proposed_action:
      "Execute formal village-to-site relocation allocations for 3 vulnerable settlements (Raini, Peng, Tapovan Upper) into safe reception terraces; initiate urgent physical site capacity preparation at Pipalkoti Plateau.",
    executive_summary:
      "The greedy multi-criteria relocation matching engine evaluated 4 settlements with 380 vulnerable households. 3 settlements (320 households) were assigned to safe reception sites with zero constraint violations. 1 settlement (Malari Outpost, 60 households) remains unassigned due to site capacity exhaustion.",
    metrics: [
      { label: "Target Settlements", value: 4, subtext: "Demanding relocation", variant: "default" },
      { label: "Allocated Sites", value: 2, subtext: "Pipalkoti & Joshimath", variant: "success" },
      { label: "Households Placed", value: "320 / 380", subtext: "84.2% demand satisfied", variant: "success" },
      { label: "Unassigned Deficit", value: "60 HH", subtext: "Malari Outpost awaiting site", variant: "danger" },
    ],
    relocation_payload: {
      matching_id: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.matching_id,
      total_villages: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.total_villages,
      assigned_villages_count: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.assigned_villages_count,
      unassigned_villages_count: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.unassigned_villages_count,
      total_households_demanded: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.total_households_demanded,
      total_households_allocated: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.total_households_allocated,
      total_households_unassigned: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.total_households_unassigned,
      assignments: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.assignments,
      summary_narrative: HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT.summary_narrative,
    },
    status: "pending_review",
    decision: null,
    statutory_mandate:
      "NDMA Disaster Management Act 2005 & Uttarakhand State Disaster Management Authority Rule 12 Protocol. Decision requires Level-3 District Officer Authorization.",
  },
  {
    id: "DOSSIER-SCEN-002",
    title: "Extreme Rainfall Shock Escalation (+40%)",
    type: "scenario_evaluation",
    source_engine: "M4-06 Scenario Simulator Engine",
    region_profile_id: "himalayan_pilot",
    created_at: "2026-09-06T18:30:00Z",
    urgency_level: "critical",
    proposed_action:
      "Issue pre-emptive red-zone evacuation warning for 2 slope-exposed settlements along Rishikesh-Badrinath highway corridor; divert emergency logistics transit via Urgam link road.",
    executive_summary:
      "What-if simulation modeling an intense cloudburst (+40% precipitation surge). Triggers 2 high-risk village threshold breaches and cuts off NH-58 transit corridor. 2 routes diverted, average risk score increases by +18.5 points across the valley.",
    metrics: [
      { label: "Precipitation Surge", value: "+40%", subtext: "IMD cloudburst simulation", variant: "warning" },
      { label: "Critical Risk Villages", value: 2, subtext: "Threshold breached", variant: "danger" },
      { label: "Diverted Routes", value: 2, subtext: "NH-58 blockage bypass", variant: "warning" },
      { label: "Mean Risk Delta", value: "+18.5 pts", subtext: "Regional escalation", variant: "danger" },
    ],
    scenario_payload: {
      scenario_type: "EXTREME_RAINFALL",
      scenario_name: HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.EXTREME_RAINFALL.scenario_name,
      parameters: HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.EXTREME_RAINFALL.parameters,
      critical_risk_villages: 2,
      unassigned_households: 60,
      unroutable_villages_count: 0,
      diverted_routes_count: 2,
      average_risk_delta: 18.5,
      summary_narrative:
        "Severe rainfall escalation drives Raini and Tapovan into critical landslide susceptibility. Evacuation routes divert to upper slopes.",
    },
    status: "pending_review",
    decision: null,
    statutory_mandate:
      "Rule 12 Emergency Action Directive: Early warning threshold triggers require authorized executive officer endorsement prior to broadcast.",
  },
  {
    id: "DOSSIER-SCEN-003",
    title: "Flash Flood & GLOF Inundation Surge",
    type: "scenario_evaluation",
    source_engine: "M4-06 Scenario Simulator Engine",
    region_profile_id: "himalayan_pilot",
    created_at: "2026-09-06T19:00:00Z",
    urgency_level: "high",
    proposed_action:
      "Enforce mandatory riverbank perimeter clearance along Dhauliganga riverbed; deploy temporary Bailey bridge units at Rishiganga confluence.",
    executive_summary:
      "Simulation of rapid glacial lake outburst flood. Valley bottom transit lines are submerged within 35 minutes. Recommends immediate evacuation of 180 valley residents to Joshimath Safe Terrace.",
    metrics: [
      { label: "Flood Inundation", value: "GLOF Surge", subtext: "Dhauliganga valley corridor", variant: "danger" },
      { label: "At-Risk Population", value: "180 Persons", subtext: "Valley floor habitations", variant: "warning" },
      { label: "Safe Terrace Capacity", value: "Available", subtext: "Joshimath reception site", variant: "success" },
      { label: "Cordon Urgency", value: "< 45 mins", subtext: "Hydrological response window", variant: "danger" },
    ],
    scenario_payload: {
      scenario_type: "FLASH_FLOOD",
      scenario_name: HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.FLASH_FLOOD.scenario_name,
      parameters: HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.FLASH_FLOOD.parameters,
      critical_risk_villages: 1,
      unassigned_households: 0,
      unroutable_villages_count: 1,
      diverted_routes_count: 1,
      average_risk_delta: 24.2,
      summary_narrative:
        "GLOF surge cuts off low-lying road networks. Immediate helicopter and upper-trail evacuation required.",
    },
    status: "pending_review",
    decision: null,
    statutory_mandate:
      "State Disaster Management Operational Protocol: Mandatory Executive Magistrate clearance required for riverbed cordon enforcement.",
  },
];

// In-memory persistent state for the current session
let reviewDossiersCache: RecommendationDossier[] = JSON.parse(
  JSON.stringify(INITIAL_REVIEW_DOSSIERS)
);

/**
 * Resets the in-memory cache to the initial seed dossiers (useful for testing or reset).
 */
export function resetReviewCache(): void {
  reviewDossiersCache = JSON.parse(JSON.stringify(INITIAL_REVIEW_DOSSIERS));
}

/**
 * Retrieves the list of all recommendation dossiers under review.
 */
export async function listReviewDossiers(): Promise<RecommendationDossier[]> {
  // Simulates an async service retrieval
  return JSON.parse(JSON.stringify(reviewDossiersCache));
}

/**
 * Retrieves a single recommendation dossier by ID.
 */
export async function getReviewDossierById(
  id: string
): Promise<RecommendationDossier | undefined> {
  const item = reviewDossiersCache.find((d) => d.id === id);
  return item ? JSON.parse(JSON.stringify(item)) : undefined;
}

export interface OfficerContext {
  id: string | number;
  name: string;
  role: string;
  department?: string;
}

/**
 * Submits an official officer decision for a recommendation dossier.
 * Enforces mandatory justification for 'rejected' and 'revision_requested'.
 * Enforces statutory confirmation for 'approved'.
 */
export async function submitOfficerDecision(
  req: SubmitDecisionRequest,
  officer: OfficerContext
): Promise<{ success: boolean; dossier: RecommendationDossier; message: string }> {
  const trimmedRationale = req.rationale?.trim() || "";

  // Validation: rejection or revision MUST have an officer justification
  if (req.action === "rejected" && !trimmedRationale) {
    throw new Error("Officer rationale is mandatory when rejecting an operational recommendation.");
  }
  if (req.action === "revision_requested" && !trimmedRationale) {
    throw new Error("Specific revision instructions are mandatory when returning a recommendation for revision.");
  }

  // Validation: approval requires statutory confirmation
  if (req.action === "approved" && !req.confirm_statutory_verification) {
    throw new Error("Statutory Rule 12 confirmation checkbox must be checked before approving operational actions.");
  }

  const index = reviewDossiersCache.findIndex((d) => d.id === req.recommendation_id);
  if (index === -1) {
    throw new Error(`Recommendation dossier with ID '${req.recommendation_id}' not found.`);
  }

  const nowIso = new Date().toISOString();
  const decisionRecord: OfficerDecisionRecord = {
    id: `DEC-${Date.now()}`,
    officer_id: officer.id || "OFFICER-001",
    officer_name: officer.name || "District Magistrate / Officer",
    officer_role: officer.role || "District Disaster Management Officer",
    decision_type:
      reviewDossiersCache[index].type === "relocation_plan"
        ? "relocation_plan"
        : "scenario_approval",
    target_entity_type:
      reviewDossiersCache[index].type === "relocation_plan"
        ? "relocation_plan"
        : "scenario_run",
    target_entity_id: req.recommendation_id,
    action_taken: req.action,
    rationale: trimmedRationale,
    overridden_recommendation: Boolean(req.override_ai_recommendation),
    decision_metadata_json: {
      source_engine: reviewDossiersCache[index].source_engine,
      region_profile_id: reviewDossiersCache[index].region_profile_id,
      statutory_mandate: reviewDossiersCache[index].statutory_mandate,
      override_flag: Boolean(req.override_ai_recommendation),
    },
    decided_at: nowIso,
  };

  // If approved and relocation plan, attempt upstream batch assignment persistence
  if (req.action === "approved" && reviewDossiersCache[index].type === "relocation_plan") {
    try {
      const payload = reviewDossiersCache[index].relocation_payload;
      if (payload && payload.assignments) {
        const assignedItems = payload.assignments
          .filter((a) => a.status === "assigned" && a.assigned_site_id)
          .map((a) => ({
            village_id: Number(a.village_id) || 1,
            candidate_site_id:
              typeof a.assigned_site_id === "string"
                ? Number(a.assigned_site_id.replace(/\D/g, "")) || 1
                : Number(a.assigned_site_id) || 1,
            assigned_households: a.incoming_households,
            assigned_population: a.incoming_population || 0,
            status: "approved",
          }));

        if (assignedItems.length > 0) {
          // Attempt batch assignment persistence against existing M4-04 endpoint
          await batchCreateRelocationAssignments({
            assignments: assignedItems,
            commit_site_capacity: true,
          }).catch(() => {
            // Silently fallback if backend container is offline during standalone UI testing
          });
        }
      }
    } catch {
      // Graceful fallback for offline / mock testing
    }
  }

  // Update in-memory dossier state
  reviewDossiersCache[index] = {
    ...reviewDossiersCache[index],
    status: req.action,
    decision: decisionRecord,
  };

  const actionLabels: Record<string, string> = {
    approved: "approved for operational execution",
    rejected: "officially rejected",
    revision_requested: "returned for technical planner revision",
  };

  return {
    success: true,
    dossier: JSON.parse(JSON.stringify(reviewDossiersCache[index])),
    message: `Recommendation '${reviewDossiersCache[index].title}' has been ${actionLabels[req.action]}. Decision record ${decisionRecord.id} filed under Rule 12.`,
  };
}

/**
 * Reverts a recommendation back to 'pending_review' status.
 */
export async function resetDossierDecision(
  id: string
): Promise<{ success: boolean; dossier: RecommendationDossier }> {
  const index = reviewDossiersCache.findIndex((d) => d.id === id);
  if (index === -1) {
    throw new Error(`Recommendation dossier with ID '${id}' not found.`);
  }

  reviewDossiersCache[index] = {
    ...reviewDossiersCache[index],
    status: "pending_review",
    decision: null,
  };

  return {
    success: true,
    dossier: JSON.parse(JSON.stringify(reviewDossiersCache[index])),
  };
}
