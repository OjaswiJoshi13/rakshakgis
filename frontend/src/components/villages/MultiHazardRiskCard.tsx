"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { RiskBadge } from "@/components/ui/Badge";
import { HabitationDetail, M3_06_RISK_FACTOR_WEIGHTS } from "@/types/villages";
import { getRiskBandFromScore } from "@/design-system/tokens";

export interface MultiHazardRiskCardProps {
  habitation: HabitationDetail;
}

export const MultiHazardRiskCard: React.FC<MultiHazardRiskCardProps> = ({
  habitation,
}) => {
  const { risk } = habitation;
  const score = risk.risk_score;
  const resolvedBand = risk.risk_band ?? (score !== null ? getRiskBandFromScore(score) : "safe");

  // Factor provenance mapping conforming strictly to authoritative sources
  const FACTOR_PROVENANCE: Record<string, { label: string; badgeVariant: "default" | "info" | "outline" | "success" | "warning" }> = {
    hazard_severity: { label: "DERIVED INPUT (Seismic Catalog & Hazard History)", badgeVariant: "outline" },
    flood_exposure: { label: "DERIVED INPUT (Hydrological River Proximity)", badgeVariant: "outline" },
    rainfall_intensity: { label: "DERIVED INPUT (Precipitation Surface Analysis)", badgeVariant: "outline" },
    slope_landslide_susceptibility: { label: "DERIVED / REAL (Survey of India Terrain Slope)", badgeVariant: "info" },
    infrastructure_vulnerability: { label: "DERIVED INPUT (Road Network Connectivity)", badgeVariant: "outline" },
    social_vulnerability: { label: "REAL INPUT (Census 2011 Demographics)", badgeVariant: "success" },
  };

  const availableFactorsCount = M3_06_RISK_FACTOR_WEIGHTS.filter(
    (f) => risk.factors[f.key] !== undefined && risk.factors[f.key] !== null
  ).length;
  const isExplainable = availableFactorsCount > 0;

  // Determine primary risk driver based on highest (weight * factor_value)
  let primaryDriver: { label: string; contribution: number; symbol: string } | null = null;
  let maxContribution = -1;

  if (isExplainable) {
    M3_06_RISK_FACTOR_WEIGHTS.forEach((item) => {
      const val = risk.factors[item.key] ?? 0;
      const contribution = val * item.weight;
      if (contribution > maxContribution) {
        maxContribution = contribution;
        primaryDriver = { label: item.label, contribution, symbol: item.symbol };
      }
    });
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base font-semibold text-text-primary flex items-center gap-2">
            <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            Multi-Hazard Risk Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <RiskBadge band={isExplainable ? resolvedBand : "safe"} score={isExplainable ? (score ?? undefined) : undefined} />
            <span className="text-xs font-mono text-text-muted">M3-06 Engine</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Score & Primary Driver banner */}
        <div className="flex items-center justify-between p-3 bg-surface-elevated border border-border-subtle rounded-md mb-4">
          <div>
            <div className="text-xs font-medium text-text-muted">
              Composite Risk Score
            </div>
            <div className="text-2xl font-bold font-mono text-text-primary tabular-nums">
              {isExplainable && score !== null
                ? `${score.toFixed(1)} / 100`
                : "Unavailable (Pending Assessment)"}
            </div>
            {!isExplainable && (
              <div className="text-[11px] text-amber-700 dark:text-amber-400 font-mono mt-1">
                Risk factor values unavailable in source; numerical score not presented.
              </div>
            )}
          </div>

          {isExplainable && primaryDriver && maxContribution > 0 && (
            <div className="text-right">
              <div className="text-xs font-medium text-text-muted">
                Primary Risk Driver
              </div>
              <div className="text-sm font-semibold font-mono text-amber-600 dark:text-amber-400">
                {(primaryDriver as { label: string; contribution: number; symbol: string }).label} [{(primaryDriver as { label: string; contribution: number; symbol: string }).symbol}]
              </div>
              <div className="text-xs text-text-muted">
                +{(primaryDriver as { label: string; contribution: number; symbol: string }).contribution.toFixed(1)} pts to composite
              </div>
            </div>
          )}
        </div>

        {/* 6-Factor Decomposition */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-text-secondary">
              Explainable 6-Factor Decomposition
            </span>
            <span className="text-[11px] font-mono text-text-muted">
              {isExplainable ? `${availableFactorsCount}/6 factors populated` : "All factors unavailable"}
            </span>
          </div>

          {M3_06_RISK_FACTOR_WEIGHTS.map((f) => {
            const factorVal = risk.factors[f.key];
            const hasVal = factorVal !== undefined && factorVal !== null;
            const pts = hasVal ? (factorVal * f.weight).toFixed(1) : "—";
            const prov = FACTOR_PROVENANCE[f.key];

            return (
              <div key={f.key} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-text-secondary font-medium">
                      {f.label} ({f.symbol}){" "}
                      <span className="text-text-muted font-normal">({(f.weight * 100).toFixed(0)}%)</span>
                    </span>
                    {prov && (
                      <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-surface-base border border-border-subtle text-text-muted">
                        {hasVal ? prov.label : "UNAVAILABLE"}
                      </span>
                    )}
                  </div>
                  <span className="font-mono text-text-primary tabular-nums text-xs shrink-0">
                    {hasVal ? `${factorVal.toFixed(1)} [→ +${pts} pts]` : "Unavailable"}
                  </span>
                </div>
                <div className="w-full bg-surface-elevated rounded-full h-1.5 overflow-hidden border border-border-subtle">
                  <div
                    className="bg-red-600 dark:bg-red-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${hasVal ? Math.min(100, Math.max(0, factorVal)) : 0}%` }}
                    role="progressbar"
                    aria-valuenow={hasVal ? factorVal : 0}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`${f.label} Score`}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Formula Citation */}
        <div className="mt-4 pt-3 border-t border-border-subtle text-xs text-text-muted font-mono">
          Model: Risk = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V (M3-06)
        </div>
      </CardContent>
    </Card>
  );
};
