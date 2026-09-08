"use client";

import React, { useState } from "react";
import {
  ScenarioDomainTab,
  ScenarioSimulationOutput,
} from "@/types/scenarios";
import { Badge } from "@/components/ui/Badge";
import {
  Flame,
  Building2,
  Route,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  MapPin,
  Layers,
} from "lucide-react";
import { ScenarioRoutingView } from "./ScenarioRoutingView";

export interface ScenarioDeltaTabsProps {
  simulationOutput: ScenarioSimulationOutput;
}

export const ScenarioDeltaTabs: React.FC<ScenarioDeltaTabsProps> = ({
  simulationOutput,
}) => {
  const [activeTab, setActiveTab] = useState<ScenarioDomainTab>("risk");

  const { baseline_pipeline, scenario_pipeline, comparison } = simulationOutput;
  const criticalEscalated = new Set(comparison.villages_escalated_to_critical || []);
  const immediateEscalated = new Set(comparison.villages_escalated_to_immediate || []);
  const newRedZones = new Set(comparison.new_red_zone_villages || []);
  const newlyUnassigned = new Set(comparison.newly_unassigned_villages || []);

  const baselineRiskMap = new Map(
    (baseline_pipeline?.risk_results || []).map((r) => [r.village_id, r])
  );
  const scenarioRiskList = scenario_pipeline?.risk_results || [];

  return (
    <div className="space-y-4">
      {/* Domain Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-subtle pb-2">
        <div className="inline-flex rounded-lg bg-surface-elevated p-1 border border-border-subtle" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "risk"}
            onClick={() => setActiveTab("risk")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "risk"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            <span>Risk &amp; Red Zones ({comparison.villages_escalated_to_critical.length} Critical Shifts)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "relocation"}
            onClick={() => setActiveTab("relocation")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "relocation"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Relocation &amp; Capacity ({comparison.scenario_unassigned_count} Deficits)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "routing"}
            onClick={() => setActiveTab("routing")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "routing"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Route className="h-3.5 w-3.5" />
            <span>Evacuation Routing ({comparison.newly_severed_routes.length} Severed)</span>
          </button>
        </div>

        <span className="text-[11px] font-mono text-text-muted">
          Evaluated via 7-Stage Domain Pipeline
        </span>
      </div>

      {/* Tab 1: Risk & Red Zones */}
      {activeTab === "risk" && (
        <div className="space-y-4 rounded-lg border border-border-subtle bg-surface-panel p-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-3">
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-text-primary font-semibold flex items-center gap-2">
                <Flame className="h-4 w-4 text-rose-500" />
                <span>Multi-Hazard Risk Escalation &amp; Dynamic Red Zones</span>
              </h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Impact of rainfall and flood perturbations on settlement composite risk grades and dynamic buffer triggers.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="rounded bg-surface-elevated px-2.5 py-1 border border-border-subtle text-text-primary">
                New Red Zones: <strong className="text-rose-600 dark:text-rose-400">+{comparison.new_red_zone_villages.length}</strong>
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-text-primary font-mono">
              <thead className="bg-surface-elevated text-[10px] uppercase text-text-muted border-b border-border-subtle">
                <tr>
                  <th className="py-2.5 px-3">Village Settlement</th>
                  <th className="py-2.5 px-3 text-right">Baseline Score</th>
                  <th className="py-2.5 px-3 text-right">Scenario Score</th>
                  <th className="py-2.5 px-3 text-right">Score Delta</th>
                  <th className="py-2.5 px-3">Risk Band Shift</th>
                  <th className="py-2.5 px-3">Dynamic Red Zone</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {scenarioRiskList.map((scRisk) => {
                  const baseRisk = baselineRiskMap.get(scRisk.village_id);
                  const delta = comparison.risk_score_deltas[scRisk.village_id] ?? (baseRisk ? scRisk.risk_score - baseRisk.risk_score : 0);
                  const isCritical = criticalEscalated.has(scRisk.village_id) || scRisk.risk_band.toUpperCase() === "CRITICAL";
                  const isRedZone = newRedZones.has(scRisk.village_id) || (scenario_pipeline.red_zone_result?.triggered_village_ids || []).includes(scRisk.village_id);

                  return (
                    <tr key={scRisk.village_id} className="hover:bg-surface-subtle transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-text-primary">
                        <div className="flex items-center gap-1.5">
                          <span>{scRisk.village_name}</span>
                          {criticalEscalated.has(scRisk.village_id) && (
                            <Badge variant="danger" size="sm" className="text-[9px] py-0">
                              Escalated
                            </Badge>
                          )}
                        </div>
                        <div className="text-[10px] text-text-muted font-mono">ID: {scRisk.village_id}</div>
                      </td>
                      <td className="py-2.5 px-3 text-right text-text-secondary">
                        {baseRisk ? `${baseRisk.risk_score.toFixed(1)} (${baseRisk.risk_band})` : "—"}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-text-primary">
                        {scRisk.risk_score.toFixed(1)}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={delta > 0 ? "text-rose-600 dark:text-rose-400 font-bold" : "text-text-muted"}>
                          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-1">
                          <span className="text-text-secondary">{baseRisk?.risk_band || "—"}</span>
                          <ArrowRight className="h-3 w-3 text-text-muted inline" />
                          <span className={`font-bold ${isCritical ? "text-rose-600 dark:text-rose-400" : "text-amber-700 dark:text-amber-400"}`}>
                            {scRisk.risk_band}
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        {isRedZone ? (
                          <Badge variant="danger" size="sm" className="text-[10px] font-mono uppercase gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            <span>Triggered</span>
                          </Badge>
                        ) : (
                          <span className="text-text-muted text-[11px]">Normal</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Relocation & Capacity */}
      {activeTab === "relocation" && (
        <div className="space-y-4 rounded-lg border border-border-subtle bg-surface-panel p-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-3">
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-text-primary font-semibold flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                <span>Candidate Sites Capacity &amp; Relocation Matching Impact</span>
              </h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Evaluation of site capacity contractions and resulting unassigned household deficits.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="rounded bg-surface-elevated px-2.5 py-1 border border-border-subtle text-text-primary">
                Unassigned Deficit: <strong className="text-rose-600 dark:text-rose-400">{(simulationOutput.scenario_metrics.unassigned_households as number || 0)} HH</strong>
              </span>
            </div>
          </div>

          {/* Sized Capacity Table */}
          <div>
            <h4 className="text-[11px] font-mono uppercase tracking-wide text-text-muted mb-2">
              Candidate Sites Sized Capacity
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(scenario_pipeline?.capacity_results || []).map((cap) => {
                const delta = comparison.site_capacity_deltas[cap.site_id] ?? 0;
                return (
                  <div key={cap.site_id} className="rounded-lg bg-surface-elevated p-3 border border-border-subtle">
                    <div className="flex items-start justify-between gap-1 mb-1.5">
                      <span className="font-semibold text-xs text-text-primary">
                        {cap.site_name}
                      </span>
                      <Badge variant={cap.is_feasible ? "success" : "danger"} size="sm" className="text-[10px]">
                        {cap.is_feasible ? "Feasible" : "Infeasible"}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                      <div>
                        <span className="text-text-muted block text-[10px]">Effective</span>
                        <span className="text-text-primary font-bold">{cap.effective_capacity} HH</span>
                      </div>
                      <div>
                        <span className="text-text-muted block text-[10px]">Available</span>
                        <span className="text-text-primary font-bold">{cap.available_capacity} HH</span>
                      </div>
                      <div>
                        <span className="text-text-muted block text-[10px]">Delta</span>
                        <span className={delta < 0 ? "text-rose-600 dark:text-rose-400 font-bold" : "text-text-muted"}>
                          {delta < 0 ? `${delta} HH` : `0 HH`}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 text-[10px] font-mono text-text-muted">
                      Limiting Factor: <span className="text-amber-700 dark:text-amber-400 uppercase font-medium">{cap.limiting_factor}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Assignments Table */}
          <div className="pt-2">
            <h4 className="text-[11px] font-mono uppercase tracking-wide text-text-muted mb-2">
              Settlement Allocation Status Under Scenario
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-text-primary font-mono">
                <thead className="bg-surface-elevated text-[10px] uppercase text-text-muted border-b border-border-subtle">
                  <tr>
                    <th className="py-2.5 px-3">Village Settlement</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Assigned Site</th>
                    <th className="py-2.5 px-3 text-right">Demanded</th>
                    <th className="py-2.5 px-3 text-right">Allocated</th>
                    <th className="py-2.5 px-3">Reason / Code</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {(scenario_pipeline?.matching_result?.assignments || []).map((asgn) => {
                    const isUnassigned = !asgn.is_assigned || newlyUnassigned.has(asgn.village_id);
                    return (
                      <tr key={asgn.village_id} className="hover:bg-surface-subtle transition-colors">
                        <td className="py-2.5 px-3 font-semibold text-text-primary">
                          {asgn.village_name}
                        </td>
                        <td className="py-2.5 px-3">
                          {isUnassigned ? (
                            <Badge variant="danger" size="sm" className="text-[10px] uppercase">
                              Unassigned
                            </Badge>
                          ) : (
                            <Badge variant="success" size="sm" className="text-[10px] uppercase">
                              Assigned
                            </Badge>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-text-secondary">
                          {asgn.assigned_site_name || "—"}
                        </td>
                        <td className="py-2.5 px-3 text-right text-text-secondary">
                          {asgn.demanded_households} HH
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-text-primary">
                          {asgn.allocated_households} HH
                        </td>
                        <td className="py-2.5 px-3 text-[11px] text-rose-600 dark:text-rose-400">
                          {asgn.unassigned_code || "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Evacuation Routing */}
      {activeTab === "routing" && (
        <ScenarioRoutingView simulationOutput={simulationOutput} />
      )}
    </div>
  );
};
