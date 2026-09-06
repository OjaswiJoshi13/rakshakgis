"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { RelocationBadge, Badge } from "@/components/ui/Badge";
import { HabitationDetail } from "@/types/villages";
import { getRelocationPriorityBand } from "@/design-system/tokens";

export interface RelocationPriorityCardProps {
  habitation: HabitationDetail;
}

export const RelocationPriorityCard: React.FC<RelocationPriorityCardProps> = ({
  habitation,
}) => {
  const { relocation, evacuation } = habitation;
  const score = relocation.priority_score;
  const resolvedBand =
    relocation.priority_band ??
    (score !== null ? getRelocationPriorityBand(score) : "monitor");

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base font-medium text-slate-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            Relocation Priority & Evacuation
          </CardTitle>
          <div className="flex items-center gap-2">
            <RelocationBadge band={resolvedBand} score={score ?? undefined} />
            <span className="text-xs font-mono text-slate-400">M3-12 / M4-04</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Priority Score Summary */}
        <div className="flex items-center justify-between p-3 bg-slate-950/80 border border-slate-800 rounded mb-4">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Relocation Urgency Score
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100 tabular-nums">
              {score !== null ? `${score.toFixed(1)} / 100` : "—"}
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Matching Status
            </div>
            {relocation.is_assigned ? (
              <Badge variant="success" size="sm">
                SITE ASSIGNED
              </Badge>
            ) : (
              <Badge variant="warning" size="sm">
                {relocation.unassigned_code || "PENDING ALLOCATION"}
              </Badge>
            )}
          </div>
        </div>

        {/* Relocation Destination Details */}
        <div className="space-y-3 mb-4">
          <div className="text-xs font-mono text-slate-300 font-medium">
            Candidate Site Assignment
          </div>

          {relocation.is_assigned ? (
            <div className="p-3 rounded bg-slate-950/50 border border-emerald-900/40 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Target Site:</span>
                <span className="font-mono font-semibold text-emerald-300">
                  {relocation.assigned_site_name || "Assigned Site"} ({relocation.assigned_site_id})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Allocated Demand:</span>
                <span className="font-mono text-slate-200">
                  {relocation.allocated_households ?? "—"} households
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded bg-slate-950/50 border border-slate-800 text-xs text-slate-400">
              No relocation site assigned yet. Settlement remains in priority evaluation queue.
            </div>
          )}
        </div>

        {/* Evacuation Route Corridor Details */}
        <div className="space-y-2 border-t border-slate-800/80 pt-3">
          <div className="text-xs font-mono text-slate-300 font-medium">
            Evacuation & Access Routing (M4-05)
          </div>

          {evacuation ? (
            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between py-1 px-2 rounded bg-slate-950/40">
                <span className="text-slate-400">Corridor Status:</span>
                <span
                  className={
                    evacuation.route_feasible ? "text-emerald-400 font-semibold" : "text-red-400 font-semibold"
                  }
                >
                  {evacuation.route_feasible ? "FEASIBLE CORRIDOR" : "SEVERED / UNROUTABLE"}
                </span>
              </div>

              {evacuation.distance_km !== undefined && evacuation.distance_km !== null && (
                <div className="flex justify-between py-1 px-2 rounded bg-slate-950/40">
                  <span className="text-slate-400">Corridor Distance:</span>
                  <span className="text-slate-200">{evacuation.distance_km.toFixed(1)} km</span>
                </div>
              )}

              {evacuation.estimated_time_minutes !== undefined && evacuation.estimated_time_minutes !== null && (
                <div className="flex justify-between py-1 px-2 rounded bg-slate-950/40">
                  <span className="text-slate-400">Estimated Transit Time:</span>
                  <span className="text-slate-200">{evacuation.estimated_time_minutes.toFixed(0)} mins</span>
                </div>
              )}

              {evacuation.blocked_corridors_count !== undefined && evacuation.blocked_corridors_count > 0 && (
                <div className="flex justify-between py-1 px-2 rounded bg-amber-950/30 text-amber-300">
                  <span>Blocked Corridors Avoided:</span>
                  <span>{evacuation.blocked_corridors_count}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="p-2.5 rounded bg-slate-950/40 text-xs text-slate-500">
              Direct route calculation pending active matching assignment.
            </div>
          )}
        </div>

        {/* Formula Citation */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-500 font-mono">
          Priority = 0.40R + 0.25E + 0.20V + 0.10H + 0.05A (M3-12)
        </div>
      </CardContent>
    </Card>
  );
};
