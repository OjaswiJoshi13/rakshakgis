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
          <CardTitle className="text-base font-medium text-slate-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            Demographics & Exposure
          </CardTitle>
          <span className="text-xs font-mono text-slate-400">M3-09 Profile</span>
        </div>
      </CardHeader>

      <CardContent>
        {/* Core Population Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Total Population
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {formatNum(demographics.total_population)}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              {demographics.total_population !== null ? "Authoritative census" : "Census record unavailable"}
            </div>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Total Households
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {formatNum(demographics.households)}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">Settlement units</div>
          </div>
        </div>

        {/* Vulnerable Sub-groups Breakdown */}
        <div className="space-y-2 border-t border-slate-800/80 pt-3">
          <div className="text-xs font-mono font-medium text-slate-300 mb-2">
            Vulnerable Demographics Breakdown
          </div>

          <div className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-950/40">
            <span className="text-slate-400">Elderly Population (&ge; 60y)</span>
            <span className="font-mono font-medium text-slate-200">
              {formatNum(demographics.elderly_count)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-950/40">
            <span className="text-slate-400">Children (&le; 10y)</span>
            <span className="font-mono font-medium text-slate-200">
              {formatNum(demographics.children_count)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-950/40">
            <span className="text-slate-500">Persons with Disabilities</span>
            <span className="font-mono text-slate-500 italic">
              {demographics.disabled_count !== undefined && demographics.disabled_count !== null
                ? formatNum(demographics.disabled_count)
                : "Unavailable from backend"}
            </span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-500">
          Values mapped from authoritative backend settlement demographic registers.
        </div>
      </CardContent>
    </Card>
  );
};
