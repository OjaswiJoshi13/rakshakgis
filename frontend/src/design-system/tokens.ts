/**
 * RakshakGIS Design System Tokens & Semantic Constants
 *
 * Strict alignment with backend domain models:
 * - Chunk M3-01: RiskScoreBands (SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL)
 * - Chunk M3-01: RelocationPriorityCutoffs (IMMEDIATE, SHORT_TERM, MEDIUM_TERM, MONITOR)
 * - Authoritative Multi-Hazard Weights: 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V
 */

export type RiskBand = "safe" | "moderate" | "high" | "very_high" | "critical";

export type RelocationPriorityBand =
  | "immediate"
  | "short_term"
  | "medium_term"
  | "monitor";

export type OperationalStatus = "normal" | "info" | "warning" | "critical";

export type DataMode = "demo" | "live" | "simulation";

export interface RiskBandConfig {
  label: string;
  min: number;
  max: number;
  badgeClass: string;
  dotColor: string;
  textColor: string;
  borderColor: string;
  description: string;
}

export const RISK_BANDS: Record<RiskBand, RiskBandConfig> = {
  safe: {
    label: "Safe",
    min: 0,
    max: 25,
    badgeClass: "bg-emerald-950/80 text-emerald-300 border-emerald-600/50",
    dotColor: "bg-emerald-500",
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500",
    description: "Low vulnerability, minimal hazard impact anticipated.",
  },
  moderate: {
    label: "Moderate",
    min: 25,
    max: 50,
    badgeClass: "bg-amber-950/80 text-amber-300 border-amber-600/50",
    dotColor: "bg-amber-500",
    textColor: "text-amber-400",
    borderColor: "border-amber-500",
    description: "Requires active seasonal telemetry monitoring and watch state.",
  },
  high: {
    label: "High",
    min: 50,
    max: 70,
    badgeClass: "bg-orange-950/80 text-orange-300 border-orange-600/50",
    dotColor: "bg-orange-500",
    textColor: "text-orange-400",
    borderColor: "border-orange-500",
    description: "Substantial slope instability or flood hazard detected.",
  },
  very_high: {
    label: "Very High",
    min: 70,
    max: 85,
    badgeClass: "bg-rose-950/80 text-rose-300 border-rose-600/50",
    dotColor: "bg-rose-500",
    textColor: "text-rose-400",
    borderColor: "border-rose-500",
    description: "Severe hazard threat; candidate for dynamic red zone evaluation.",
  },
  critical: {
    label: "Critical",
    min: 85,
    max: 100,
    badgeClass: "bg-red-950/90 text-red-200 border-red-500/80 shadow-sm shadow-red-950",
    dotColor: "bg-red-500",
    textColor: "text-red-400",
    borderColor: "border-red-600",
    description: "Imminent danger; candidate for immediate red zone demarcation.",
  },
};

export interface RelocationPriorityConfig {
  label: string;
  min: number;
  max: number;
  badgeClass: string;
  textColor: string;
}

export const RELOCATION_PRIORITY_BANDS: Record<
  RelocationPriorityBand,
  RelocationPriorityConfig
> = {
  immediate: {
    label: "Immediate Action",
    min: 80,
    max: 100,
    badgeClass: "bg-red-950 text-red-200 border-red-500/80 font-semibold",
    textColor: "text-red-400",
  },
  short_term: {
    label: "Short Term (1-3 Months)",
    min: 60,
    max: 79.99,
    badgeClass: "bg-orange-950 text-orange-300 border-orange-500/70",
    textColor: "text-orange-400",
  },
  medium_term: {
    label: "Medium Term (3-12 Months)",
    min: 40,
    max: 59.99,
    badgeClass: "bg-amber-950 text-amber-300 border-amber-500/60",
    textColor: "text-amber-400",
  },
  monitor: {
    label: "Routine Monitoring",
    min: 0,
    max: 39.99,
    badgeClass: "bg-blue-950 text-blue-300 border-blue-500/50",
    textColor: "text-blue-400",
  },
};

export const OPERATIONAL_STATUS_CONFIG: Record<
  OperationalStatus,
  { label: string; badgeClass: string; dotClass: string }
> = {
  normal: {
    label: "Normal",
    badgeClass: "bg-emerald-950/60 text-emerald-300 border-emerald-700/50",
    dotClass: "bg-emerald-500",
  },
  info: {
    label: "Info",
    badgeClass: "bg-sky-950/60 text-sky-300 border-sky-700/50",
    dotClass: "bg-sky-500",
  },
  warning: {
    label: "Warning",
    badgeClass: "bg-amber-950/60 text-amber-300 border-amber-700/50",
    dotClass: "bg-amber-500",
  },
  critical: {
    label: "Critical",
    badgeClass: "bg-red-950/80 text-red-300 border-red-600/70",
    dotClass: "bg-red-500 animate-pulse",
  },
};

export const DATA_MODE_CONFIG: Record<
  DataMode,
  { label: string; badgeClass: string }
> = {
  demo: {
    label: "DEMO MODE",
    badgeClass: "bg-cyan-950/80 text-cyan-300 border-cyan-700/60",
  },
  live: {
    label: "LIVE TELEMETRY",
    badgeClass: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
  },
  simulation: {
    label: "SIMULATION RUN",
    badgeClass: "bg-purple-950/80 text-purple-300 border-purple-700/60",
  },
};

/**
 * Maps a numeric risk score (0-100) to its authoritative risk band.
 */
export function getRiskBandFromScore(score: number): RiskBand {
  if (score < 25) return "safe";
  if (score < 50) return "moderate";
  if (score < 70) return "high";
  if (score < 85) return "very_high";
  return "critical";
}

/**
 * Maps a numeric relocation priority score (0-100) to its band.
 */
export function getRelocationPriorityBand(
  score: number
): RelocationPriorityBand {
  if (score >= 80) return "immediate";
  if (score >= 60) return "short_term";
  if (score >= 40) return "medium_term";
  return "monitor";
}
