"use client";

import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RelocationAssignmentRead } from "@/types/dashboard";

export interface RelocationAssignmentsCardProps {
  assignments?: RelocationAssignmentRead[] | null;
  totalCount?: number;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string | null;
}

export const RelocationAssignmentsCard: React.FC<RelocationAssignmentsCardProps> = ({
  assignments,
  totalCount,
  isLoading = false,
  isError = false,
  errorMessage,
}) => {
  return (
    <Card variant="elevated" className="space-y-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Planned Relocation Assignments</CardTitle>
            <CardDescription>
              Settlement-to-safe-site matching allocations derived from greedy capacity reservation algorithms.
            </CardDescription>
          </div>
          {totalCount !== undefined && (
            <span className="text-xs font-mono font-medium text-text-secondary bg-surface-elevated border border-border-subtle px-2 py-1 rounded">
              {totalCount} Total Assignments
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="py-8 text-center text-text-muted font-mono text-sm animate-pulse">
            Loading settlement relocation assignments...
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900/60 dark:bg-red-950/30 p-4 text-sm text-red-900 dark:text-red-200">
            <div className="font-semibold mb-1 text-red-950 dark:text-red-100">Failed to Load Relocation Assignments</div>
            <p className="text-xs text-red-800 dark:text-red-300">
              {errorMessage || "Unable to retrieve assignments from backend."}
            </p>
          </div>
        ) : !assignments || assignments.length === 0 ? (
          <div className="py-8 text-center text-text-muted text-sm font-mono space-y-1">
            <p>No active settlement relocation assignments found.</p>
            <p className="text-xs text-text-muted">
              Assignments are generated via deterministic matching in Relocation Planner<span className="sr-only"> (M6-02)</span>.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full text-left text-xs text-text-secondary">
              <thead className="bg-surface-elevated text-[11px] font-mono text-text-muted uppercase tracking-wider border-b border-border-subtle">
                <tr>
                  <th className="px-3 py-2.5">ID</th>
                  <th className="px-3 py-2.5">Origin Settlement</th>
                  <th className="px-3 py-2.5">Destination Site</th>
                  <th className="px-3 py-2.5 text-right">Households</th>
                  <th className="px-3 py-2.5 text-right">Population</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5">Assigned Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle bg-surface-panel">
                {assignments.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-subtle transition-colors">
                    <td className="px-3 py-2 font-mono text-text-muted">#{item.id}</td>
                    <td className="px-3 py-2 font-medium text-text-primary">
                      {item.village_name || `Village #${item.village_id}`}
                    </td>
                    <td className="px-3 py-2 text-text-secondary">
                      {item.candidate_site_name || `Site #${item.candidate_site_id}`}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-text-primary">
                      {item.assigned_households}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-text-secondary">
                      {item.assigned_population ? item.assigned_population.toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <Badge
                        variant={
                          item.status.toLowerCase() === "approved"
                            ? "success"
                            : item.status.toLowerCase() === "completed"
                            ? "info"
                            : item.status.toLowerCase() === "rejected"
                            ? "danger"
                            : "outline"
                        }
                        size="sm"
                        className="capitalize text-[10px]"
                      >
                        {item.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-text-muted">
                      {item.assigned_at ? new Date(item.assigned_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
