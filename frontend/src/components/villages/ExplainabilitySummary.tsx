"use client";

import React from "react";
import { HabitationDetail } from "@/types/villages";
import { RiskBadge, RelocationBadge } from "@/components/ui/Badge";
import { getRiskBandFromScore, getRelocationPriorityBand } from "@/design-system/tokens";

export interface ExplainabilitySummaryProps {
  habitation: HabitationDetail;
}

export const ExplainabilitySummary: React.FC<ExplainabilitySummaryProps> = ({
  habitation,
}) => {
  const riskScore = habitation.risk.risk_score;
  const riskBand =
    habitation.risk.risk_band ??
    (riskScore !== null ? getRiskBandFromScore(riskScore) : "safe");

  const priorityScore = habitation.relocation.priority_score;
  const priorityBand =
    habitation.relocation.priority_band ??
    (priorityScore !== null ? getRelocationPriorityBand(priorityScore) : "monitor");

  const pop = habitation.demographics.total_population;
  const socialScore = habitation.vulnerability.social_vulnerability_score;

  return (
    <div className="bg-surface-panel border border-border-subtle rounded-lg p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wider flex items-center gap-2">
          <svg className="w-4 h-4 text-sky-600 dark:text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
            />
          </svg>
          Officer Decision Support Pipeline
        </h2>
        <span className="text-xs font-mono text-text-muted">Deterministic Backend Trace</span>
      </div>

      {/* Progressive Flow Pipeline: Village -> Exposure/Vulnerability -> Risk -> Priority */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Stage 1: Village Identity */}
        <div className="p-3 bg-surface-elevated border border-border-subtle rounded-md relative">
          <div className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">
            1. Settlement
          </div>
          <div className="font-semibold text-text-primary text-sm truncate" title={habitation.name}>
            {habitation.name}
          </div>
          <div className="text-xs text-text-muted font-mono mt-1">
            ID: {habitation.id}
          </div>
        </div>

        {/* Stage 2: Exposure & Vulnerability */}
        <div className="p-3 bg-surface-elevated border border-border-subtle rounded-md">
          <div className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">
            2. Exposure & Vulnerability
          </div>
          <div className="text-sm font-semibold text-text-primary">
            {pop !== null ? `${pop.toLocaleString()} people` : "Not available in source"}
          </div>
          <div className="text-xs text-purple-700 dark:text-purple-400 font-mono mt-1">
            Vulnerability: {socialScore !== null ? `${socialScore.toFixed(1)} / 100` : "Not available in source"}
          </div>
        </div>

        {/* Stage 3: Multi-Hazard Risk */}
        <div className="p-3 bg-surface-elevated border border-border-subtle rounded-md">
          <div className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">
            3. Multi-Hazard Risk
          </div>
          <div className="text-sm font-semibold text-text-primary">
            Score: {riskScore !== null ? `${riskScore.toFixed(1)}` : "Not available in source"}
          </div>
          <div className="mt-1">
            <RiskBadge band={riskBand} score={riskScore ?? undefined} />
          </div>
        </div>

        {/* Stage 4: Relocation Priority */}
        <div className="p-3 bg-surface-elevated border border-border-subtle rounded-md">
          <div className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">
            4. Relocation Urgency
          </div>
          <div className="text-sm font-semibold text-text-primary">
            Urgency: {priorityScore !== null ? `${priorityScore.toFixed(1)}` : "Not available in source"}
          </div>
          <div className="mt-1">
            <RelocationBadge band={priorityBand} score={priorityScore ?? undefined} />
          </div>
        </div>
      </div>

      <div className="mt-3 text-xs text-text-muted font-mono flex items-center justify-between flex-wrap gap-2">
        <span>Authority: Backend Engines (M3-06 Risk + M3-09 Vulnerability + M3-12 Priority + M4-04 Matching)</span>
        <span>Zero LLM numerical calculation</span>
      </div>
    </div>
  );
};
