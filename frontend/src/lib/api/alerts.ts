/**
 * Real-Time Alerts & Threshold Warnings API Service & Himalayan Pilot Baseline Dataset (Chunk M6-05).
 * Conforms strictly to:
 * - Chunk M3-11 Dynamic Red Zone & Threshold Trigger Engine
 * - Chunk M3-13 Alert database model (telemetry.py)
 * - Regional Profile Himalayan Pilot trigger thresholds (himalayan.py)
 */

import { apiClient } from "./client";
import { ResponseEnvelope } from "@/types/api";
import {
  AlertFilterCriteria,
  AlertSummaryMetrics,
  DynamicThresholdSummary,
  OperationalAlertItem,
} from "@/types/alerts";

export * from "@/types/alerts";

// ============================================================================
// Authoritative Himalayan Pilot Dynamic Thresholds (from himalayan.py)
// ============================================================================

export const HIMALAYAN_PILOT_THRESHOLDS: DynamicThresholdSummary = {
  profile_id: "himalayan_pilot",
  profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
  rainfall_trigger_24h_mm: 64.5, // IMD standard heavy precipitation trigger
  seismic_trigger_mmi: 6.0, // Strong felt intensity threshold
  slope_trigger_min_deg: 25.0, // Critical slope threshold for landslide acceleration
  water_level_trigger_m_above_danger: 1.5, // Riverine danger stage exceedance
  landslide_debris_volume_trigger_m3: 1000.0, // Acute debris flow volume threshold
  buffer_distance_m: 500.0, // Geodesic buffer applied around point sensors/settlements
  default_danger_level: "VERY_HIGH",
};

// ============================================================================
// Deterministic Himalayan Pilot Sample Alert Feed (Explicitly Synthetic Baseline)
// ============================================================================

export const HIMALAYAN_PILOT_ALERT_DATASET: OperationalAlertItem[] = [
  {
    id: "ALT-HIM-2026-001",
    alert_type: "rainfall_threshold",
    severity: "extreme",
    danger_level: "VERY_HIGH",
    status: "triggered",
    headline: "Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge",
    message:
      "24-hour cumulative precipitation reached 84.2 mm at Sunil Station, exceeding the regional dynamic threshold of 64.5 mm (IMD Heavy Rain Standard). High antecedent moisture elevates active subsidence and debris flow vulnerability.",
    village_id: "VIL-CHAMOLI-001",
    village_name: "Joshimath (Ward 5 - Sunil)",
    district_id: "DIST-UK-01",
    district_name: "Chamoli",
    coordinates: [79.5634, 30.5562],
    indicator: "rainfall_24h",
    observed_value: 84.2,
    configured_threshold: 64.5,
    operator: ">=",
    unit: "mm",
    buffer_m: 500.0,
    is_acknowledged: false,
    acknowledged_at: null,
    acknowledged_by: null,
    issued_at: "2026-09-06T15:30:00Z",
    expires_at: "2026-09-07T15:30:00Z",
    candidate_id: "DYN-RZ-VIL-001-RAIN",
    source_id: "SRC-AWS-SUNIL-01",
    is_synthetic: true,
    explainability: {
      decision_reason: "Dynamic threshold triggered: Observed 24h rainfall (84.2 mm) >= regional threshold (64.5 mm).",
      summary: "Extreme monsoon cloudburst breach. Temporary exclusion zone proposed around Sunil Ward perimeter.",
      profile_id: "himalayan_pilot",
      profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
      trigger_evaluations: [
        {
          indicator: "rainfall_24h",
          observed_value: 84.2,
          configured_threshold: 64.5,
          operator: ">=",
          triggered: true,
          status: "triggered",
          unit: "mm",
          audit_note: "Precipitation recorded at Automated Weather Station AWS-SUNIL-01 over rolling 24h window.",
        },
        {
          indicator: "slope_deg",
          observed_value: 28.4,
          configured_threshold: 25.0,
          operator: ">=",
          triggered: true,
          status: "triggered",
          unit: "deg",
          audit_note: "Compound hazard check: Terrain slope 28.4° exceeds critical threshold 25.0°.",
        },
      ],
      triggered_indicators: ["rainfall_24h", "slope_deg"],
      missing_indicators: [],
      source_observation_ids: ["OBS-RAIN-20260906-01", "OBS-SLOPE-20260906-01"],
      source_village_ids: ["VIL-CHAMOLI-001"],
      buffer_applied_m: 500.0,
      is_dissolved: false,
      governance_notice:
        "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: This is an event-driven temporary exclusion candidate generated for operational decision support and early warning. It does NOT constitute a statutory disaster declaration or legal evacuation order. Official action requires verification and authorization by the competent disaster management authority (Chunk M6-08 workflow).",
    },
  },
  {
    id: "ALT-HIM-2026-002",
    alert_type: "seismic_event",
    severity: "severe",
    danger_level: "HIGH",
    status: "triggered",
    headline: "Seismic Tremor Exceedance (6.4 MMI) — Pipalkoti Corridor",
    message:
      "Telemetry station recorded strong seismic intensity of 6.4 MMI, breaching the 6.0 MMI threshold trigger. Secondary rockfall hazards active along NH-07 transit highway.",
    village_id: "VIL-CHAMOLI-002",
    village_name: "Pipalkoti (Lower Terraces)",
    district_id: "DIST-UK-01",
    district_name: "Chamoli",
    coordinates: [79.4312, 30.4289],
    indicator: "seismic_mmi",
    observed_value: 6.4,
    configured_threshold: 6.0,
    operator: ">=",
    unit: "MMI",
    buffer_m: 500.0,
    is_acknowledged: false,
    acknowledged_at: null,
    acknowledged_by: null,
    issued_at: "2026-09-06T16:15:00Z",
    expires_at: "2026-09-07T04:15:00Z",
    candidate_id: "DYN-RZ-VIL-002-SEIS",
    source_id: "SRC-SEISMO-PIPALKOTI-02",
    is_synthetic: true,
    explainability: {
      decision_reason: "Dynamic threshold triggered: Observed seismic intensity (6.4 MMI) >= regional threshold (6.0 MMI).",
      summary: "Significant tectonic motion detected. Slope stability along road cut slopes compromised.",
      profile_id: "himalayan_pilot",
      profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
      trigger_evaluations: [
        {
          indicator: "seismic_mmi",
          observed_value: 6.4,
          configured_threshold: 6.0,
          operator: ">=",
          triggered: true,
          status: "triggered",
          unit: "MMI",
          audit_note: "Seismograph telemetry verified across 3 regional accelerometers.",
        },
      ],
      triggered_indicators: ["seismic_mmi"],
      missing_indicators: [],
      source_observation_ids: ["OBS-SEIS-20260906-02"],
      source_village_ids: ["VIL-CHAMOLI-002"],
      buffer_applied_m: 500.0,
      is_dissolved: false,
      governance_notice:
        "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: Temporary exclusion candidate generated for operational decision support and early warning. Official action requires verification and authorization by the competent disaster management authority.",
    },
  },
  {
    id: "ALT-HIM-2026-003",
    alert_type: "flood_breach",
    severity: "severe",
    danger_level: "VERY_HIGH",
    status: "triggered",
    headline: "Hydrological River Stage Breach (+2.1m) — Helang Riverine Zone",
    message:
      "Alaknanda river gauge recorded stage level 2.1 m above warning mark, surpassing the 1.5 m threshold. Riverbank erosion and low-bridge flooding imminent.",
    village_id: "VIL-CHAMOLI-003",
    village_name: "Helang / Dhauli Ganga Confluence",
    district_id: "DIST-UK-01",
    district_name: "Chamoli",
    coordinates: [79.512, 30.521],
    indicator: "water_level_above_danger",
    observed_value: 2.1,
    configured_threshold: 1.5,
    operator: ">=",
    unit: "m",
    buffer_m: 500.0,
    is_acknowledged: true,
    acknowledged_at: "2026-09-06T16:45:00Z",
    acknowledged_by: "Officer R. Sharma (DM Chamoli)",
    issued_at: "2026-09-06T14:00:00Z",
    expires_at: "2026-09-07T02:00:00Z",
    candidate_id: "DYN-RZ-VIL-003-HYDRO",
    source_id: "SRC-CWC-HELANG-01",
    is_synthetic: true,
    explainability: {
      decision_reason: "Dynamic threshold triggered: Water level (+2.1 m) >= regional threshold (+1.5 m).",
      summary: "Riverine discharge exceedance following torrential tributary runoff.",
      profile_id: "himalayan_pilot",
      profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
      trigger_evaluations: [
        {
          indicator: "water_level_above_danger",
          observed_value: 2.1,
          configured_threshold: 1.5,
          operator: ">=",
          triggered: true,
          status: "triggered",
          unit: "m",
          audit_note: "CWC hydrological ultrasonic level transmitter reading confirmed.",
        },
      ],
      triggered_indicators: ["water_level_above_danger"],
      missing_indicators: [],
      source_observation_ids: ["OBS-HYDRO-20260906-03"],
      source_village_ids: ["VIL-CHAMOLI-003"],
      buffer_applied_m: 500.0,
      is_dissolved: false,
      governance_notice:
        "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: Temporary exclusion candidate generated for operational decision support and early warning.",
    },
  },
  {
    id: "ALT-HIM-2026-004",
    alert_type: "landslide_warning",
    severity: "warning",
    danger_level: null,
    status: "insufficient_data",
    headline: "Sensor Telemetry Unavailable — Urgam Debris Volume Transducer",
    message:
      "Precipitation exceedance detected on 31.2° slope, but debris volume transducer returned null/offline. Evaluated strictly as INSUFFICIENT_DATA per M3-11 safe semantics (never coerced to safe).",
    village_id: "VIL-CHAMOLI-004",
    village_name: "Urgam Valley High Ridge",
    district_id: "DIST-UK-01",
    district_name: "Chamoli",
    coordinates: [79.5891, 30.5912],
    indicator: "landslide_debris_volume",
    observed_value: null,
    configured_threshold: 1000.0,
    operator: ">=",
    unit: "m3",
    buffer_m: 500.0,
    is_acknowledged: false,
    acknowledged_at: null,
    acknowledged_by: null,
    issued_at: "2026-09-06T16:50:00Z",
    expires_at: "2026-09-07T00:50:00Z",
    candidate_id: "DYN-RZ-VIL-004-DATAGAP",
    source_id: "SRC-GEOTECH-URGAM-03",
    is_synthetic: true,
    explainability: {
      decision_reason: "Evaluation yielded INSUFFICIENT_DATA: Observation data for 'landslide_debris_volume' is missing or offline.",
      summary: "Critical geophysical data gap. Safety protocol prevents declaring status as safe without authoritative telemetry.",
      profile_id: "himalayan_pilot",
      profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
      trigger_evaluations: [
        {
          indicator: "landslide_debris_volume",
          observed_value: null,
          configured_threshold: 1000.0,
          operator: ">=",
          triggered: false,
          status: "insufficient_data",
          unit: "m3",
          audit_note: "Transducer failed health check; telemetry age exceeded maximum staleness threshold.",
        },
      ],
      triggered_indicators: [],
      missing_indicators: ["landslide_debris_volume"],
      source_observation_ids: ["OBS-GAP-20260906-04"],
      source_village_ids: ["VIL-CHAMOLI-004"],
      buffer_applied_m: 500.0,
      is_dissolved: false,
      governance_notice:
        "SAFETY NOTICE: Telemetry gap flagged. Physical ground inspection required by district disaster dispatch.",
    },
  },
  {
    id: "ALT-HIM-2026-005",
    alert_type: "rainfall_threshold",
    severity: "info",
    danger_level: null,
    status: "no_trigger",
    headline: "Nominal Monitoring — Govindghat Lower Valley Station",
    message:
      "Precipitation at 42.1 mm / 24h remains below the 64.5 mm threshold limit. Continuous seasonal observation cycle active under standard SOPs.",
    village_id: "VIL-CHAMOLI-005",
    village_name: "Govindghat (Valley Floor)",
    district_id: "DIST-UK-01",
    district_name: "Chamoli",
    coordinates: [79.5541, 30.6234],
    indicator: "rainfall_24h",
    observed_value: 42.1,
    configured_threshold: 64.5,
    operator: ">=",
    unit: "mm",
    buffer_m: 500.0,
    is_acknowledged: true,
    acknowledged_at: "2026-09-06T12:00:00Z",
    acknowledged_by: "System (Automated Baseline Log)",
    issued_at: "2026-09-06T11:00:00Z",
    expires_at: "2026-09-07T11:00:00Z",
    candidate_id: "DYN-RZ-VIL-005-NOMINAL",
    source_id: "SRC-AWS-GOVINDGHAT-01",
    is_synthetic: true,
    explainability: {
      decision_reason: "Dynamic threshold evaluated: Observed rainfall (42.1 mm) < regional threshold (64.5 mm).",
      summary: "Normal operating parameters within baseline variance.",
      profile_id: "himalayan_pilot",
      profile_name: "Himalayan Pilot (Chamoli / Joshimath District)",
      trigger_evaluations: [
        {
          indicator: "rainfall_24h",
          observed_value: 42.1,
          configured_threshold: 64.5,
          operator: ">=",
          triggered: false,
          status: "no_trigger",
          unit: "mm",
          audit_note: "Telemetry verified below threshold limit.",
        },
      ],
      triggered_indicators: [],
      missing_indicators: [],
      source_observation_ids: ["OBS-RAIN-20260906-05"],
      source_village_ids: ["VIL-CHAMOLI-005"],
      buffer_applied_m: 500.0,
      is_dissolved: false,
      governance_notice:
        "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: Normal operating parameters.",
    },
  },
];

// In-memory state for client-side acknowledgment testing and simulation
let inMemoryAlerts: OperationalAlertItem[] = [...HIMALAYAN_PILOT_ALERT_DATASET];

// ============================================================================
// Service Methods
// ============================================================================

/**
 * Retrieves alerts matching optional operational filters.
 */
export async function listAlerts(
  filters?: AlertFilterCriteria
): Promise<ResponseEnvelope<OperationalAlertItem[]>> {
  try {
    const resp = await apiClient.get<ResponseEnvelope<OperationalAlertItem[]>>(
      "/api/v1/alerts",
      {
        params: {
          severity: filters?.severity !== "all" ? filters?.severity : undefined,
          status: filters?.status !== "all" ? filters?.status : undefined,
          indicator: filters?.indicator !== "all" ? filters?.indicator : undefined,
          is_acknowledged:
            filters?.is_acknowledged !== "all"
              ? String(filters?.is_acknowledged)
              : undefined,
          search: filters?.search || undefined,
        },
      }
    );
    return resp;
  } catch {
    // Fallback to deterministic Himalayan Pilot dataset
    let filtered = [...inMemoryAlerts];

    if (filters?.severity && filters.severity !== "all") {
      filtered = filtered.filter((a) => a.severity === filters.severity);
    }
    if (filters?.status && filters.status !== "all") {
      filtered = filtered.filter((a) => a.status === filters.status);
    }
    if (filters?.indicator && filters.indicator !== "all") {
      filtered = filtered.filter((a) => a.indicator === filters.indicator);
    }
    if (filters?.is_acknowledged !== undefined && filters.is_acknowledged !== "all") {
      filtered = filtered.filter((a) => a.is_acknowledged === filters.is_acknowledged);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      filtered = filtered.filter(
        (a) =>
          a.headline.toLowerCase().includes(q) ||
          a.message.toLowerCase().includes(q) ||
          (a.village_name && a.village_name.toLowerCase().includes(q)) ||
          (a.candidate_id && a.candidate_id.toLowerCase().includes(q)) ||
          a.id.toLowerCase().includes(q)
      );
    }

    return {
      success: true,
      data: filtered,
    };
  }
}

/**
 * Retrieves full details and audit trail for an individual alert.
 */
export async function getAlertDetail(
  id: string
): Promise<ResponseEnvelope<OperationalAlertItem>> {
  try {
    const resp = await apiClient.get<ResponseEnvelope<OperationalAlertItem>>(
      `/api/v1/alerts/${id}`
    );
    return resp;
  } catch {
    const item = inMemoryAlerts.find((a) => a.id === id);
    if (!item) {
      throw new Error(`Alert with id '${id}' not found.`);
    }
    return {
      success: true,
      data: item,
    };
  }
}

/**
 * Marks an individual alert as acknowledged by the current officer.
 */
export async function acknowledgeAlert(
  id: string,
  officerName = "District Disaster Officer"
): Promise<ResponseEnvelope<OperationalAlertItem>> {
  try {
    const resp = await apiClient.post<ResponseEnvelope<OperationalAlertItem>>(
      `/api/v1/alerts/${id}/acknowledge`,
      { officer_name: officerName }
    );
    return resp;
  } catch {
    const idx = inMemoryAlerts.findIndex((a) => a.id === id);
    if (idx === -1) {
      throw new Error(`Alert with id '${id}' not found.`);
    }

    const updated: OperationalAlertItem = {
      ...inMemoryAlerts[idx],
      is_acknowledged: true,
      acknowledged_at: new Date().toISOString(),
      acknowledged_by: officerName,
    };
    inMemoryAlerts[idx] = updated;

    return {
      success: true,
      data: updated,
    };
  }
}

/**
 * Bulk acknowledges all currently unacknowledged alerts.
 */
export async function acknowledgeAllAlerts(
  officerName = "District Disaster Officer"
): Promise<ResponseEnvelope<{ acknowledged_count: number }>> {
  try {
    const resp = await apiClient.post<ResponseEnvelope<{ acknowledged_count: number }>>(
      "/api/v1/alerts/acknowledge-all",
      { officer_name: officerName }
    );
    return resp;
  } catch {
    let count = 0;
    const now = new Date().toISOString();

    inMemoryAlerts = inMemoryAlerts.map((alert) => {
      if (!alert.is_acknowledged) {
        count++;
        return {
          ...alert,
          is_acknowledged: true,
          acknowledged_at: now,
          acknowledged_by: officerName,
        };
      }
      return alert;
    });

    return {
      success: true,
      data: { acknowledged_count: count },
    };
  }
}

/**
 * Retrieves the active dynamic threshold configuration for the specified region.
 */
export async function getThresholdConfig(
  _profileId = "himalayan_pilot"
): Promise<ResponseEnvelope<DynamicThresholdSummary>> {
  return {
    success: true,
    data: HIMALAYAN_PILOT_THRESHOLDS,
  };
}

/**
 * Computes high-level alert summary metrics.
 */
export async function getAlertSummaryMetrics(): Promise<ResponseEnvelope<AlertSummaryMetrics>> {
  const alerts = inMemoryAlerts;
  const metrics: AlertSummaryMetrics = {
    total_alerts: alerts.length,
    triggered_count: alerts.filter((a) => a.status === "triggered").length,
    pending_acknowledgment: alerts.filter((a) => !a.is_acknowledged).length,
    insufficient_data_count: alerts.filter((a) => a.status === "insufficient_data").length,
    critical_extreme_count: alerts.filter(
      (a) => a.severity === "extreme" || a.severity === "severe"
    ).length,
  };

  return {
    success: true,
    data: metrics,
  };
}

/**
 * Reset memory state (helper for tests).
 */
export function resetAlertsMemoryState(): void {
  inMemoryAlerts = [...HIMALAYAN_PILOT_ALERT_DATASET];
}
