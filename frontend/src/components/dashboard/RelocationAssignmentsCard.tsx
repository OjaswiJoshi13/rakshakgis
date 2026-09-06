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
            <span className="text-xs font-mono font-medium text-slate-400 bg-slate-900 border border-slate-800 px-2 py-1 rounded">
              {totalCount} Total Assignments
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="py-8 text-center text-slate-400 font-mono text-sm animate-pulse">
            Loading settlement relocation assignments...
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-900/60 bg-red-950/30 p-4 text-sm text-red-300">
            <div className="font-semibold mb-1">Failed to Load Relocation Assignments</div>
            <p className="text-xs text-red-400">
              {errorMessage || "Unable to retrieve assignments from backend."}
            </p>
          </div>
        ) : !assignments || assignments.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-sm font-mono space-y-1">
            <p>No active settlement relocation assignments found.</p>
            <p className="text-xs text-slate-600">
              Assignments are generated via deterministic matching in Relocation Planner (M6-02).
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-[11px] font-mono text-slate-400 uppercase tracking-wider border-b border-slate-800">
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
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                {assignments.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-3 py-2 font-mono text-slate-400">#{item.id}</td>
                    <td className="px-3 py-2 font-medium text-slate-200">
                      {item.village_name || `Village #${item.village_id}`}
                    </td>
                    <td className="px-3 py-2 text-slate-300">
                      {item.candidate_site_name || `Site #${item.candidate_site_id}`}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-200">
                      {item.assigned_households}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-300">
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
                    <td className="px-3 py-2 font-mono text-[11px] text-slate-400">
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
