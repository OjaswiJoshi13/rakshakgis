"use client";

import React from "react";
import { SiteSuitabilityResult } from "@/types/sites";
import { Badge } from "@/components/ui/Badge";
import {
  Scale,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Info,
} from "lucide-react";

export interface SiteSuitabilityTabProps {
  suitability: SiteSuitabilityResult | null;
  isLoading?: boolean;
}

export const SiteSuitabilityTab: React.FC<SiteSuitabilityTabProps> = ({
  suitability,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="py-16 text-center text-xs text-slate-400">
        Loading multi-criteria suitability evaluation...
      </div>
    );
  }

  if (!suitability) {
    return (
      <div className="rounded-lg border border-dashed border-slate-800 p-8 text-center text-xs text-slate-400">
        No suitability evaluation data available for this site.
      </div>
    );
  }

  const isSuitable = suitability.decision === "suitable";
  const isConstrained = suitability.decision === "constrained";
  const isUnsuitable = suitability.decision === "unsuitable";
  const isIneligible = suitability.decision === "ineligible";

  const decisionBadgeVariant = isSuitable
    ? "success"
    : isConstrained
    ? "warning"
    : "danger";

  return (
    <div className="space-y-6">
      {/* Top Banner: Decision & Overall Score */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-950 border border-slate-800">
            <Scale className="h-6 w-6 text-sky-400" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                M4-02 Classification
              </span>
              <Badge variant={decisionBadgeVariant} size="sm" className="font-mono uppercase">
                {suitability.decision.toUpperCase()}
              </Badge>
              {suitability.is_eligible ? (
                <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Eligible</span>
                </span>
              ) : (
                <span className="text-[11px] font-mono text-red-400 flex items-center gap-1">
                  <XCircle className="h-3 w-3" />
                  <span>Ineligible</span>
                </span>
              )}
            </div>
            <h3 className="text-base font-bold text-slate-100">
              Multi-Criteria Suitability Assessment
            </h3>
          </div>
        </div>

        {/* Score Display */}
        <div className="flex items-baseline gap-2 rounded-lg bg-slate-950 border border-slate-800 px-4 py-2">
          <span className="text-3xl font-bold font-mono tracking-tight text-slate-100">
            {suitability.overall_score.toFixed(1)}
          </span>
          <span className="text-xs font-mono text-slate-400">/ 100</span>
        </div>
      </div>

      {/* Hard Safety Constraint Gates */}
      <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
            <span>Pre-Scoring Hard Safety Constraint Gates</span>
          </h4>
          <span className="text-[11px] font-mono text-slate-500">
            All gates must pass before weighted scoring
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {suitability.hard_constraints.map((gate, idx) => (
            <div
              key={idx}
              className={`rounded-lg border p-3 flex flex-col justify-between ${
                gate.passed
                  ? "border-slate-800 bg-slate-950/60"
                  : "border-red-900/60 bg-red-950/20"
              }`}
            >
              <div className="flex items-start justify-between gap-1 mb-1.5">
                <span className="font-semibold text-xs text-slate-200">
                  {gate.name}
                </span>
                {gate.passed ? (
                  <Badge variant="success" size="sm" className="font-mono">
                    PASS
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm" className="font-mono">
                    FAIL
                  </Badge>
                )}
              </div>

              <div className="text-[11px] font-mono text-slate-400 space-y-0.5">
                <div>
                  <span className="text-slate-500">Actual: </span>
                  <span className={gate.passed ? "text-slate-200" : "text-red-400 font-bold"}>
                    {gate.actual_value !== null ? String(gate.actual_value) : "—"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Threshold: </span>
                  <span className="text-slate-300">
                    {gate.threshold_value !== null ? String(gate.threshold_value) : "—"}
                  </span>
                </div>
              </div>

              {gate.reason && (
                <p className="text-[11px] text-slate-400 mt-2 border-t border-slate-800/60 pt-1.5 line-clamp-2">
                  {gate.reason}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 9 Weighted Criteria Breakdown */}
      <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Scale className="h-3.5 w-3.5 text-sky-400" />
            <span>Authoritative 9-Criteria Weighted Score Decomposition</span>
          </h4>
          <span className="text-[11px] font-mono text-slate-500">Sum of Weights = 1.00</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/70 font-mono text-slate-400 uppercase tracking-wider">
                <th className="py-2.5 px-3">Criterion</th>
                <th className="py-2.5 px-3">Weight</th>
                <th className="py-2.5 px-3">Raw Score</th>
                <th className="py-2.5 px-3">Weighted Contribution</th>
                <th className="py-2.5 px-3">Assessment Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {Object.entries(suitability.criteria_scores).map(([key, item]) => {
                const weightPct = Math.round(item.weight * 100);

                return (
                  <tr key={key} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-200">
                      {item.criterion_name}
                    </td>

                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {weightPct}%
                    </td>

                    <td className="py-2.5 px-3 font-mono">
                      <span className="text-slate-200 font-medium">
                        {item.raw_score.toFixed(1)}
                      </span>
                      <span className="text-slate-500 text-[11px]"> / 100</span>
                    </td>

                    <td className="py-2.5 px-3 font-mono text-sky-300 font-bold">
                      +{item.weighted_contribution.toFixed(1)} pts
                    </td>

                    <td className="py-2.5 px-3 text-slate-400 text-xs max-w-sm">
                      {item.description}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Audit Reasons */}
      {suitability.summary_reasons.length > 0 && (
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-2">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-sky-400" />
            <span>Officer Audit & Review Summary</span>
          </h4>
          <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
            {suitability.summary_reasons.map((reason, idx) => (
              <li key={idx} className="leading-relaxed">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
