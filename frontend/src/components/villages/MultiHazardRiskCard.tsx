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

  // Determine primary risk driver based on highest (weight * factor_value)
  let primaryDriver: { label: string; contribution: number; symbol: string } | null = null;
  let maxContribution = -1;

  M3_06_RISK_FACTOR_WEIGHTS.forEach((item) => {
    const val = risk.factors[item.key] ?? 0;
    const contribution = val * item.weight;
    if (contribution > maxContribution) {
      maxContribution = contribution;
      primaryDriver = { label: item.label, contribution, symbol: item.symbol };
    }
  });

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base font-medium text-slate-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            <RiskBadge band={resolvedBand} score={score ?? undefined} />
            <span className="text-xs font-mono text-slate-400">M3-06 Engine</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Score & Primary Driver banner */}
        <div className="flex items-center justify-between p-3 bg-slate-950/80 border border-slate-800 rounded mb-4">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Composite Risk Score
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100 tabular-nums">
              {score !== null ? `${score.toFixed(1)} / 100` : "—"}
            </div>
          </div>

          {primaryDriver && maxContribution > 0 && (
            <div className="text-right">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Primary Risk Driver
              </div>
              <div className="text-sm font-semibold font-mono text-amber-400">
                {(primaryDriver as { label: string; contribution: number; symbol: string }).label} [{(primaryDriver as { label: string; contribution: number; symbol: string }).symbol}]
              </div>
              <div className="text-xs font-mono text-slate-500">
                +{(primaryDriver as { label: string; contribution: number; symbol: string }).contribution.toFixed(1)} pts to composite
              </div>
            </div>
          )}
        </div>

        {/* 6-Factor Decomposition */}
        <div className="space-y-3">
          <div className="text-xs font-mono text-slate-300 font-medium">
            Explainable 6-Factor Decomposition
          </div>

          {M3_06_RISK_FACTOR_WEIGHTS.map((f) => {
            const factorVal = risk.factors[f.key];
            const hasVal = factorVal !== undefined && factorVal !== null;
            const pts = hasVal ? (factorVal * f.weight).toFixed(1) : "—";

            return (
              <div key={f.key} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-mono text-slate-300">
                    {f.label} ({f.symbol}){" "}
                    <span className="text-slate-500 font-normal">({(f.weight * 100).toFixed(0)}%)</span>
                  </span>
                  <span className="font-mono text-slate-200 tabular-nums">
                    {hasVal ? `${factorVal.toFixed(1)} [→ +${pts} pts]` : "Unavailable"}
                  </span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                  <div
                    className="bg-red-500/80 h-full rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(0, factorVal ?? 0))}%` }}
                    role="progressbar"
                    aria-valuenow={factorVal ?? 0}
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
        <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-500 font-mono">
          Model: Risk = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V (M3-06)
        </div>
      </CardContent>
    </Card>
  );
};
