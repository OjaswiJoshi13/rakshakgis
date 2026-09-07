"use client";

import React from "react";
import { RelocationMatchingResult } from "@/types/relocation";
import { MetricCard } from "@/components/ui/MetricCard";
import { ShieldAlert, Users, CheckCircle2, AlertTriangle, Building2, Info } from "lucide-react";

export interface RelocationSummaryCardsProps {
  result: RelocationMatchingResult;
}

export const RelocationSummaryCards: React.FC<RelocationSummaryCardsProps> = ({ result }) => {
  const allocationRate =
    result.total_households_demanded > 0
      ? Math.round((result.total_households_allocated / result.total_households_demanded) * 100)
      : 0;

  const sitesWithCapacity = Object.entries(result.site_remaining_capacities || {});
  const totalRemainingCapacity = sitesWithCapacity.reduce((sum, [, cap]) => sum + (cap || 0), 0);

  return (
    <div className="space-y-4">
      {/* Statutory Rule 12 Mandate Banner */}
      <div className="flex items-start gap-3 rounded-lg border border-amber-600/30 bg-amber-500/10 p-3.5 text-xs text-amber-900 dark:text-amber-200">
        <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-amber-800 dark:text-amber-300 tracking-wide font-mono">
            Rule 12 Mandate — Statutory Decision Support
          </p>
          <p className="text-amber-900/90 dark:text-amber-200/90 text-xs leading-relaxed">
            {result.governance_notice}
          </p>
        </div>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Demanded Households"
          value={result.total_households_demanded.toLocaleString()}
          unit="HH"
          subtext={`Across ${result.total_villages} prioritized villages`}
          status="info"
          icon={<Users className="h-4 w-4" />}
        />

        <MetricCard
          label="Allocated Households"
          value={result.total_households_allocated.toLocaleString()}
          unit="HH"
          subtext={`${allocationRate}% absorption rate`}
          status={allocationRate === 100 ? "normal" : allocationRate >= 60 ? "warning" : "critical"}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />

        <MetricCard
          label="Unassigned Deficit"
          value={result.total_households_unassigned.toLocaleString()}
          unit="HH"
          subtext={`${result.unassigned_villages_count} unassigned village${result.unassigned_villages_count === 1 ? "" : "s"}`}
          status={result.unassigned_villages_count > 0 ? "warning" : "normal"}
          icon={<AlertTriangle className="h-4 w-4" />}
        />

        <MetricCard
          label="Remaining Capacity"
          value={totalRemainingCapacity.toLocaleString()}
          unit="HH"
          subtext={`Across ${sitesWithCapacity.length} candidate sites`}
          status="normal"
          icon={<Building2 className="h-4 w-4" />}
        />
      </div>

      {/* Narrative Context */}
      {result.summary_narrative && (
        <div className="flex items-center gap-2 rounded-md bg-surface-raised border border-border-subtle px-3.5 py-2 text-xs text-text-secondary">
          <Info className="h-4 w-4 text-[#0969da] dark:text-[#2f81f7] shrink-0" />
          <span className="leading-snug">{result.summary_narrative}</span>
        </div>
      )}
    </div>
  );
};
