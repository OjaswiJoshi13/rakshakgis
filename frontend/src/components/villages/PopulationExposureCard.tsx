"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { HabitationDetail } from "@/types/villages";

export interface PopulationExposureCardProps {
  habitation: HabitationDetail;
}

export const PopulationExposureCard: React.FC<PopulationExposureCardProps> = ({
  habitation,
}) => {
  const { demographics } = habitation;

  const formatNum = (val: number | null | undefined): string => {
    if (val === null || val === undefined) return "—";
    return val.toLocaleString();
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-text-primary flex items-center gap-2">
            <svg className="w-4 h-4 text-sky-600 dark:text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            Demographics & Exposure
          </CardTitle>
          <span className="text-xs font-mono text-text-muted">M3-09 Profile</span>
        </div>
      </CardHeader>

      <CardContent>
        {/* Core Population Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-surface-elevated border border-border-subtle rounded-md p-3">
            <div className="text-xs font-medium text-text-muted mb-1">
              Total Population
            </div>
            <div className="text-xl font-bold font-mono text-text-primary tabular-nums">
              {formatNum(demographics.total_population)}
            </div>
            <div className="text-xs text-text-muted mt-0.5">
              {demographics.total_population !== null ? "Authoritative census" : "Census record unavailable"}
            </div>
          </div>

          <div className="bg-surface-elevated border border-border-subtle rounded-md p-3">
            <div className="text-xs font-medium text-text-muted mb-1">
              Total Households
            </div>
            <div className="text-xl font-bold font-mono text-text-primary tabular-nums">
              {formatNum(demographics.households)}
            </div>
            <div className="text-xs text-text-muted mt-0.5">Settlement units</div>
          </div>
        </div>

        {/* Vulnerable Sub-groups Breakdown */}
        <div className="space-y-2 border-t border-border-subtle pt-3">
          <div className="text-xs font-medium text-text-secondary mb-2">
            Vulnerable Demographics Breakdown
          </div>

          <div className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
            <span className="text-text-muted">Elderly Population (&ge; 60y)</span>
            <span className="font-mono font-semibold text-text-primary tabular-nums">
              {formatNum(demographics.elderly_count)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
            <span className="text-text-muted">Children (&le; 10y)</span>
            <span className="font-mono font-semibold text-text-primary tabular-nums">
              {formatNum(demographics.children_count)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
            <span className="text-text-muted">Persons with Disabilities</span>
            <span className="font-mono text-text-muted italic">
              {demographics.disabled_count !== undefined && demographics.disabled_count !== null
                ? formatNum(demographics.disabled_count)
                : "Unavailable from backend"}
            </span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-border-subtle text-xs text-text-muted">
          Values mapped from authoritative settlement demographic registers.
        </div>
      </CardContent>
    </Card>
  );
};
