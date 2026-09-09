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
          <CardTitle className="text-base font-semibold text-text-primary flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            <span className="text-xs font-mono text-text-muted">Relocation Engine</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Priority Score Summary */}
        <div className="flex items-center justify-between p-3 bg-surface-elevated border border-border-subtle rounded-md mb-4">
          <div>
            <div className="text-xs font-medium text-text-muted">
              Relocation Urgency Score
            </div>
            <div className="text-2xl font-bold font-mono text-text-primary tabular-nums">
              {score !== null ? `${score.toFixed(1)} / 100` : "Not available in source"}
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs font-medium text-text-muted">
              Matching Status
            </div>
            {relocation.is_assigned ? (
              <Badge variant="success" size="sm">
                Site Assigned
              </Badge>
            ) : (
              <Badge variant="warning" size="sm">
                {relocation.unassigned_code || "Pending Allocation"}
              </Badge>
            )}
          </div>
        </div>

        {/* Relocation Destination Details */}
        <div className="space-y-3 mb-4">
          <div className="text-xs font-medium text-text-secondary">
            Proposed Candidate Site Assignment
          </div>

          {relocation.is_assigned ? (
            <div className="p-3 rounded-md bg-surface-elevated border border-emerald-500/30 dark:border-emerald-900/40 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Target Proposed Site:</span>
                <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                  {relocation.assigned_site_name || "Assigned Site"} ({relocation.assigned_site_id})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Allocated Demand:</span>
                <span className="font-mono text-text-primary">
                  {relocation.allocated_households ?? "Not available in source"} households
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-md bg-surface-elevated border border-border-subtle text-xs text-text-muted">
              No proposed candidate site assigned yet. Settlement remains in priority evaluation queue.
            </div>
          )}
        </div>

        {/* Evacuation Route Corridor Details */}
        <div className="space-y-2 border-t border-border-subtle pt-3">
          <div className="text-xs font-medium text-text-secondary">
            Evacuation & Access Routing
          </div>

          {evacuation ? (
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
                <span className="text-text-muted">Corridor Status:</span>
                <span
                  className={
                    evacuation.route_feasible ? "text-emerald-700 dark:text-emerald-400 font-semibold" : "text-red-700 dark:text-red-400 font-semibold"
                  }
                >
                  {evacuation.route_feasible ? "FEASIBLE CORRIDOR" : "SEVERED / UNROUTABLE"}
                </span>
              </div>

              {evacuation.distance_km !== undefined && evacuation.distance_km !== null && (
                <div className="flex justify-between py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
                  <span className="text-text-muted">Corridor Distance:</span>
                  <span className="text-text-primary font-mono tabular-nums">{evacuation.distance_km.toFixed(1)} km</span>
                </div>
              )}

              {evacuation.estimated_time_minutes !== undefined && evacuation.estimated_time_minutes !== null && (
                <div className="flex justify-between py-1.5 px-2.5 rounded bg-surface-elevated border border-border-subtle">
                  <span className="text-text-muted">Estimated Transit Time:</span>
                  <span className="text-text-primary font-mono tabular-nums">{evacuation.estimated_time_minutes.toFixed(0)} mins</span>
                </div>
              )}

              {evacuation.blocked_corridors_count !== undefined && evacuation.blocked_corridors_count > 0 && (
                <div className="flex justify-between py-1.5 px-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300">
                  <span>Blocked Corridors Avoided:</span>
                  <span className="font-mono font-semibold">{evacuation.blocked_corridors_count}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="p-2.5 rounded bg-surface-elevated text-xs text-text-muted border border-border-subtle">
              Direct route calculation pending active matching assignment.
            </div>
          )}
        </div>

        {/* Formula Citation */}
        <div className="mt-4 pt-3 border-t border-border-subtle text-xs text-text-muted font-mono">
          Priority Formula: 0.40R + 0.25E + 0.20V + 0.10H + 0.05A
        </div>
      </CardContent>
    </Card>
  );
};
