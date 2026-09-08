"use client";

import React from "react";
import { ScenarioSimulationOutput } from "@/types/scenarios";
import { Badge } from "@/components/ui/Badge";
import {
  Route,
  Compass,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Milestone,
} from "lucide-react";

export interface ScenarioRoutingViewProps {
  simulationOutput: ScenarioSimulationOutput;
}

export const ScenarioRoutingView: React.FC<ScenarioRoutingViewProps> = ({
  simulationOutput,
}) => {
  const routing = simulationOutput.scenario_pipeline?.routing_result;
  const routes = routing?.routes || [];
  const distanceDeltas = simulationOutput.comparison?.route_distance_deltas || {};
  const severedRoutes = new Set(simulationOutput.comparison?.newly_severed_routes || []);
  const divertedCorridors = new Set(simulationOutput.comparison?.corridors_diverted || []);

  const getStatusBadge = (status: string, villageId: string, isFeasible: boolean) => {
    const norm = status.toUpperCase();
    if (!isFeasible || severedRoutes.has(villageId) || norm === "CUT_OFF" || norm === "UNROUTABLE") {
      return (
        <Badge variant="danger" size="sm" className="font-mono text-[10px] uppercase gap-1">
          <XCircle className="h-3 w-3" />
          <span>Cut Off</span>
        </Badge>
      );
    }
    if (divertedCorridors.has(villageId) || norm === "DIVERTED") {
      return (
        <Badge variant="warning" size="sm" className="font-mono text-[10px] uppercase gap-1">
          <AlertTriangle className="h-3 w-3" />
          <span>Diverted</span>
        </Badge>
      );
    }
    return (
      <Badge variant="success" size="sm" className="font-mono text-[10px] uppercase gap-1">
        <CheckCircle2 className="h-3 w-3" />
        <span>Feasible</span>
      </Badge>
    );
  };

  return (
    <div className="space-y-4 rounded-lg border border-border-subtle bg-surface-panel p-4 shadow-xs">
      {/* Header and Quick Summary */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div>
          <h3 className="text-xs font-mono uppercase tracking-wider text-text-primary font-semibold flex items-center gap-2">
            <Route className="h-4 w-4 text-primary-600 dark:text-primary-400" />
            <span className="sr-only">M4-05 Evacuation Routing & Corridor Severance Analysis</span>
            <span aria-hidden="true">Evacuation Routing & Corridor Severance Analysis</span>
          </h3>
          <p className="text-xs text-text-secondary mt-0.5">
            Dijkstra shortest path computation evaluated with road blockage constraints and flood hazard avoidance.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="rounded bg-surface-elevated px-2.5 py-1 border border-border-subtle text-text-primary">
            Total Corridors: <strong className="text-text-primary">{routing?.routes_evaluated ?? 0}</strong>
          </span>
          <span className="rounded bg-surface-elevated px-2.5 py-1 border border-border-subtle text-text-primary">
            Feasible: <strong className="text-emerald-600 dark:text-emerald-400">{routing?.feasible_routes_count ?? 0}</strong>
          </span>
          <span className="rounded bg-surface-elevated px-2.5 py-1 border border-border-subtle text-text-primary">
            Severed: <strong className="text-rose-600 dark:text-rose-400">{routing?.unroutable_count ?? 0}</strong>
          </span>
        </div>
      </div>

      {/* Routes Table */}
      {routes.length === 0 ? (
        <div className="rounded border border-dashed border-border-strong p-8 text-center text-xs text-text-muted font-mono">
          No routing paths available for current scenario.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-text-primary font-mono">
            <thead className="bg-surface-elevated text-[10px] uppercase text-text-muted border-b border-border-subtle">
              <tr>
                <th className="py-2.5 px-3">Origin Village</th>
                <th className="py-2.5 px-3">Destination Site</th>
                <th className="py-2.5 px-3">Route Status</th>
                <th className="py-2.5 px-3 text-right">Distance (km)</th>
                <th className="py-2.5 px-3 text-right">Distance Delta</th>
                <th className="py-2.5 px-3 text-right">Est. Transit Time</th>
                <th className="py-2.5 px-3 text-center">Obstacles Avoided</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {routes.map((rt) => {
                const delta = distanceDeltas[rt.village_id] ?? 0;
                const isSevered = !rt.is_feasible || severedRoutes.has(rt.village_id);

                return (
                  <tr key={`${rt.village_id}-${rt.site_id}`} className="hover:bg-surface-subtle transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-text-primary">
                      {rt.village_id}
                    </td>
                    <td className="py-2.5 px-3 text-text-secondary">
                      {rt.site_id}
                    </td>
                    <td className="py-2.5 px-3">
                      {getStatusBadge(rt.route_status, rt.village_id, rt.is_feasible)}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {isSevered || rt.distance_km === null || rt.distance_km === undefined ? (
                        <span className="text-rose-600 dark:text-rose-400 font-bold">Cut Off</span>
                      ) : (
                        `${rt.distance_km.toFixed(1)} km`
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {isSevered ? (
                        <span className="text-rose-600 dark:text-rose-400">—</span>
                      ) : delta > 0 ? (
                        <span className="text-amber-700 dark:text-amber-400 font-bold">+{delta.toFixed(1)} km</span>
                      ) : (
                        <span className="text-text-muted">0.0 km</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {isSevered || rt.estimated_time_minutes === null || rt.estimated_time_minutes === undefined ? (
                        <span className="text-rose-600 dark:text-rose-400">—</span>
                      ) : (
                        <span className="flex items-center justify-end gap-1">
                          <Clock className="h-3 w-3 text-text-muted" />
                          <span>{Math.round(rt.estimated_time_minutes)} mins</span>
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {rt.blocked_avoided_count > 0 ? (
                        <span className="inline-block rounded bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 text-[10px] text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-800/50">
                          {rt.blocked_avoided_count} Bypass{rt.blocked_avoided_count > 1 ? "es" : ""}
                        </span>
                      ) : (
                        <span className="text-text-muted text-[10px]">None</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
