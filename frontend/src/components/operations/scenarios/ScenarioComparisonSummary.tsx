"use client";

import React from "react";
import { ScenarioSimulationOutput } from "@/types/scenarios";
import { Badge } from "@/components/ui/Badge";
import {
  Shield,
  AlertTriangle,
  Flame,
  Activity,
  ArrowRight,
  TrendingUp,
  Building2,
  Route,
  Compass,
  FileText,
} from "lucide-react";

export interface ScenarioComparisonSummaryProps {
  simulationOutput: ScenarioSimulationOutput;
}

export const ScenarioComparisonSummary: React.FC<ScenarioComparisonSummaryProps> = ({
  simulationOutput,
}) => {
  const { comparison, baseline_metrics, scenario_metrics, scenario_name, parameters } =
    simulationOutput;

  const avgRiskDelta = comparison.average_risk_delta;
  const isRiskEscalated = avgRiskDelta > 0.05;
  const redZoneDelta =
    comparison.scenario_red_zones_count - comparison.baseline_red_zones_count;
  const immediateDelta = comparison.villages_escalated_to_immediate.length;
  const unassignedDelta =
    (scenario_metrics.unassigned_households as number || 0) -
    (baseline_metrics.unassigned_households as number || 0);
  const severedCount = comparison.newly_severed_routes.length;
  const divertedCount = comparison.corridors_diverted.length;

  return (
    <div className="space-y-4">
      {/* Statutory Rule 12 Mandate Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-800/60 bg-amber-950/20 px-3.5 py-2.5 text-xs text-amber-200 font-mono">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-400 shrink-0" />
          <span>
            Protocol: <strong className="text-slate-100">Rule 12 Mandate</strong> — Simulated What-If Analysis
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-amber-300/80">
          <span>Non-mutating analytical sandbox; field verification required</span>
        </div>
      </div>

      {/* Scenario Header Card */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="info" size="sm" className="font-mono text-xs uppercase">
                {simulationOutput.scenario_type}
              </Badge>
              <span className="text-xs font-mono text-slate-500">
                Run ID: {simulationOutput.run_id} • Region: {simulationOutput.region_profile_id}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
              <Activity className="h-5 w-5 text-sky-400 shrink-0" />
              <span>{scenario_name}</span>
            </h2>
          </div>

          <div className="flex flex-wrap gap-2 text-xs font-mono">
            <span className="rounded bg-slate-950 px-2.5 py-1 border border-slate-800 text-slate-300">
              Rainfall: <strong className="text-amber-400">{parameters.rainfall_multiplier.toFixed(2)}x</strong>
            </span>
            <span className="rounded bg-slate-950 px-2.5 py-1 border border-slate-800 text-slate-300">
              Blockage: <strong className="text-cyan-400">{parameters.road_blockage_percentage.toFixed(0)}%</strong>
            </span>
            <span className="rounded bg-slate-950 px-2.5 py-1 border border-slate-800 text-slate-300">
              Capacity Loss: <strong className="text-rose-400">{parameters.capacity_reduction_percentage.toFixed(0)}%</strong>
            </span>
          </div>
        </div>

        {/* Delta Comparison Metric Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-4">
          {/* Average Risk Delta */}
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-0.5">
              Average Risk Score
            </span>
            <div className="flex items-baseline gap-1.5 font-mono">
              <span className="text-sm text-slate-400">
                {(baseline_metrics.average_risk_score as number || 0).toFixed(1)}
              </span>
              <ArrowRight className="h-3 w-3 text-slate-600 inline" />
              <span className="text-base font-bold text-slate-100">
                {(scenario_metrics.average_risk_score as number || 0).toFixed(1)}
              </span>
            </div>
            <div className="mt-1 text-[11px] font-mono flex items-center gap-1 font-semibold">
              <TrendingUp className={`h-3 w-3 ${isRiskEscalated ? "text-rose-400" : "text-slate-400"}`} />
              <span className={isRiskEscalated ? "text-rose-400" : "text-slate-400"}>
                {avgRiskDelta >= 0 ? `+${avgRiskDelta.toFixed(1)} pts` : `${avgRiskDelta.toFixed(1)} pts`}
              </span>
            </div>
          </div>

          {/* Dynamic Red Zones */}
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-0.5">
              Red Zones Triggered
            </span>
            <div className="flex items-baseline gap-1.5 font-mono">
              <span className="text-sm text-slate-400">
                {comparison.baseline_red_zones_count}
              </span>
              <ArrowRight className="h-3 w-3 text-slate-600 inline" />
              <span className="text-base font-bold text-slate-100">
                {comparison.scenario_red_zones_count}
              </span>
            </div>
            <div className="mt-1 text-[11px] font-mono font-semibold">
              <span className={redZoneDelta > 0 ? "text-rose-400" : "text-slate-400"}>
                {redZoneDelta > 0 ? `+${redZoneDelta} New Red Zones` : "No Change"}
              </span>
            </div>
          </div>

          {/* Immediate Relocation Villages */}
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-0.5">
              Immediate Urgency
            </span>
            <div className="flex items-baseline gap-1.5 font-mono">
              <span className="text-sm text-slate-400">
                {(baseline_metrics.immediate_priority_villages as number || 0)}
              </span>
              <ArrowRight className="h-3 w-3 text-slate-600 inline" />
              <span className="text-base font-bold text-slate-100">
                {(scenario_metrics.immediate_priority_villages as number || 0)}
              </span>
            </div>
            <div className="mt-1 text-[11px] font-mono font-semibold">
              <span className={immediateDelta > 0 ? "text-amber-400" : "text-slate-400"}>
                {immediateDelta > 0 ? `+${immediateDelta} Settlements` : "No Escalation"}
              </span>
            </div>
          </div>

          {/* Unassigned Households Deficit */}
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-0.5">
              Unassigned Deficit
            </span>
            <div className="flex items-baseline gap-1.5 font-mono">
              <span className="text-sm text-slate-400">
                {(baseline_metrics.unassigned_households as number || 0)} HH
              </span>
              <ArrowRight className="h-3 w-3 text-slate-600 inline" />
              <span className="text-base font-bold text-slate-100">
                {(scenario_metrics.unassigned_households as number || 0)} HH
              </span>
            </div>
            <div className="mt-1 text-[11px] font-mono font-semibold">
              <span className={unassignedDelta > 0 ? "text-rose-400" : "text-emerald-400"}>
                {unassignedDelta > 0 ? `+${unassignedDelta} HH Unassigned` : "Zero Deficit"}
              </span>
            </div>
          </div>

          {/* Severed / Diverted Routes */}
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-0.5">
              Route Corridors
            </span>
            <div className="flex items-baseline gap-1.5 font-mono">
              <span className="text-base font-bold text-slate-100">
                {severedCount > 0 ? `${severedCount} Severed` : `${divertedCount} Diverted`}
              </span>
            </div>
            <div className="mt-1 text-[11px] font-mono">
              <span className={severedCount > 0 ? "text-rose-400 font-bold" : divertedCount > 0 ? "text-amber-400 font-semibold" : "text-emerald-400"}>
                {severedCount > 0
                  ? `${severedCount} Cut Off, ${divertedCount} Diverted`
                  : divertedCount > 0
                  ? `${divertedCount} Bypasses Active`
                  : "All Routes Optimal"}
              </span>
            </div>
          </div>
        </div>

        {/* Narrative Box */}
        {comparison.comparison_narrative && (
          <div className="mt-4 rounded-lg bg-slate-950/70 p-3.5 border border-slate-800 text-xs">
            <div className="flex items-center gap-2 mb-1 text-slate-300 font-semibold font-mono text-[11px] uppercase tracking-wider">
              <FileText className="h-3.5 w-3.5 text-sky-400" />
              <span>M4-06 Scenario Impact Synthesis</span>
            </div>
            <p className="text-slate-300 leading-relaxed font-sans">
              {comparison.comparison_narrative}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
