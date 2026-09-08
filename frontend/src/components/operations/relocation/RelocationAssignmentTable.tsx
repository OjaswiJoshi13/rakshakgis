"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  AssignmentFilter,
  VillageAssignmentResult,
} from "@/types/relocation";
import { Badge, RelocationBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  Search,
  CheckCircle2,
  AlertCircle,
  Eye,
  Building2,
  Users,
  MapPin,
  TrendingUp,
} from "lucide-react";

export interface RelocationAssignmentTableProps {
  assignments: VillageAssignmentResult[];
  onInspectAudit: (assignment: VillageAssignmentResult) => void;
}

export const RelocationAssignmentTable: React.FC<RelocationAssignmentTableProps> = ({
  assignments,
  onInspectAudit,
}) => {
  const [filter, setFilter] = useState<AssignmentFilter>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const assignedCount = useMemo(
    () => assignments.filter((a) => a.status === "assigned").length,
    [assignments]
  );
  const unassignedCount = useMemo(
    () => assignments.filter((a) => a.status === "unassigned").length,
    [assignments]
  );

  const filteredAssignments = useMemo(() => {
    return assignments.filter((item) => {
      // 1. Status Filter
      if (filter === "assigned" && item.status !== "assigned") return false;
      if (filter === "unassigned" && item.status !== "unassigned") return false;

      // 2. Search Query Filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesVillage = item.village_name.toLowerCase().includes(q);
        const matchesSite =
          item.assigned_site_name?.toLowerCase().includes(q) || false;
        const matchesReason =
          item.unassigned_reason?.toLowerCase().includes(q) ||
          item.selection_reason?.toLowerCase().includes(q) ||
          false;
        return matchesVillage || matchesSite || matchesReason;
      }

      return true;
    });
  }, [assignments, filter, searchQuery]);

  return (
    <div className="space-y-4 rounded-lg border border-border-base bg-surface-raised p-4 shadow-2xs">
      {/* Table Header: Filters & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Status Filter Tabs */}
        <div className="inline-flex rounded-md bg-surface-base p-1 border border-border-base" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={filter === "all"}
            onClick={() => setFilter("all")}
            className={`px-3 py-1 text-xs font-medium rounded transition-all ${
              filter === "all"
                ? "bg-surface-raised dark:bg-[#21262d] text-text-primary border border-border-base dark:border-[#30363d] shadow-2xs font-semibold"
                : "text-text-secondary hover:text-text-primary border border-transparent"
            }`}
          >
            All Villages ({assignments.length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={filter === "assigned"}
            onClick={() => setFilter("assigned")}
            className={`px-3 py-1 text-xs font-medium rounded transition-all flex items-center gap-1.5 ${
              filter === "assigned"
                ? "bg-[#1a7f37]/10 text-[#1a7f37] dark:text-[#3fb950] font-semibold border border-[#1a7f37]/30 shadow-2xs"
                : "text-text-secondary hover:text-text-primary border border-transparent"
            }`}
          >
            <CheckCircle2 className="h-3 w-3 text-[#1a7f37] dark:text-[#3fb950]" />
            <span>Assigned ({assignedCount})</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={filter === "unassigned"}
            onClick={() => setFilter("unassigned")}
            className={`px-3 py-1 text-xs font-medium rounded transition-all flex items-center gap-1.5 ${
              filter === "unassigned"
                ? "bg-amber-500/10 text-amber-800 dark:text-amber-300 font-semibold border border-amber-600/30 shadow-2xs"
                : "text-text-secondary hover:text-text-primary border border-transparent"
            }`}
          >
            <AlertCircle className="h-3 w-3 text-amber-600 dark:text-amber-400" />
            <span>Unassigned ({unassignedCount})</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative min-w-[240px] max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search village or site..."
            className="w-full rounded-md border border-border-strong bg-surface-elevated pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-focus-ring focus:outline-none"
          />
        </div>
      </div>

      {/* Village Assignments Table / Cards */}
      {filteredAssignments.length === 0 ? (
        <div className="rounded-lg border border-border-subtle p-8 text-center text-xs text-text-muted">
          No village assignments match the current filter or search criteria.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-border-subtle bg-surface-elevated/70 text-text-secondary text-xs font-semibold">
                <th className="py-2.5 px-3">Village / Priority</th>
                <th className="py-2.5 px-3">Relocation Demand</th>
                <th className="py-2.5 px-3">Assignment Status</th>
                <th className="py-2.5 px-3">Destination Site</th>
                <th className="py-2.5 px-3">Proximity</th>
                <th className="py-2.5 px-3">Suitability</th>
                <th className="py-2.5 px-3">Capacity Impact</th>
                <th className="py-2.5 px-3 text-right">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle font-sans">
              {filteredAssignments.map((assignment) => {
                const isAssigned = assignment.status === "assigned";

                return (
                  <tr
                    key={String(assignment.village_id)}
                    className="hover:bg-surface-raised/80 dark:hover:bg-[#161b22]/50 transition-colors group"
                  >
                    {/* Village Name & Priority */}
                    <td className="py-3 px-3">
                      <div className="font-semibold text-text-primary flex items-center gap-2">
                        <span>{assignment.village_name}</span>
                        <span className="text-[11px] font-mono text-text-muted font-normal">
                          #{assignment.village_id}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-1.5">
                        <RelocationBadge score={assignment.priority_score} />
                      </div>
                    </td>

                    {/* Relocation Demand */}
                    <td className="py-3 px-3 font-mono tabular-nums">
                      <div className="text-text-primary font-medium">
                        {assignment.incoming_households} HH
                      </div>
                      <div className="text-text-muted text-[11px]">
                        {assignment.incoming_population
                          ? `${assignment.incoming_population} people`
                          : "—"}
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-3 font-mono">
                      {isAssigned ? (
                        <Badge variant="success" size="sm" className="flex items-center gap-1 w-fit">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Assigned</span>
                        </Badge>
                      ) : (
                        <Badge variant="warning" size="sm" className="flex items-center gap-1 w-fit">
                          <AlertCircle className="h-3 w-3" />
                          <span>Unassigned</span>
                        </Badge>
                      )}
                    </td>

                    {/* Destination Site */}
                    <td className="py-3 px-3">
                      {isAssigned ? (
                        <div>
                          <Link
                            href={`/operations/sites?siteId=${
                              typeof assignment.assigned_site_id === "string"
                                ? assignment.assigned_site_id.replace(/\D/g, "") || assignment.assigned_site_id
                                : assignment.assigned_site_id
                            }`}
                            className="font-medium text-text-primary hover:underline flex items-center gap-1.5 group/link"
                            title="Inspect site infrastructure and suitability details"
                          >
                            <Building2 className="h-3.5 w-3.5 text-text-muted shrink-0" />
                            <span>{assignment.assigned_site_name}</span>
                          </Link>
                          <div className="text-xs text-text-muted flex items-center gap-1.5 mt-0.5">
                            <span>Site ID: {assignment.assigned_site_id}</span>
                            <Badge variant="outline" size="sm" className="text-[10px] text-amber-700 dark:text-amber-300 border-amber-500/30 font-normal">
                              Proposed Haven
                            </Badge>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <span className="text-amber-800 dark:text-amber-300 font-mono text-[11px]">
                            Code: [{assignment.unassigned_code || "INSUFFICIENT_CAPACITY"}]
                          </span>
                          <p className="text-[11px] text-text-secondary line-clamp-1 max-w-xs" title={assignment.unassigned_reason || ""}>
                            {assignment.unassigned_reason || "No feasible candidate site"}
                          </p>
                        </div>
                      )}
                    </td>

                    {/* Distance Proximity */}
                    <td className="py-3 px-3 font-mono tabular-nums text-text-secondary">
                      {assignment.distance_km !== null && assignment.distance_km !== undefined ? (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-text-muted" />
                          <span>{assignment.distance_km.toFixed(1)} km</span>
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>

                    {/* Suitability Score */}
                    <td className="py-3 px-3 font-mono tabular-nums">
                      {assignment.suitability_score !== null && assignment.suitability_score !== undefined ? (
                        <span className="text-[#1a7f37] dark:text-[#3fb950] font-medium">
                          {assignment.suitability_score.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>

                    {/* Capacity Impact */}
                    <td className="py-3 px-3 font-mono tabular-nums">
                      {isAssigned &&
                      assignment.available_capacity_before !== null &&
                      assignment.available_capacity_after !== null ? (
                        <div className="text-text-secondary text-[11px]">
                          <span>{assignment.available_capacity_before}</span>
                          <span className="text-text-muted mx-1">→</span>
                          <span className="text-[#0969da] dark:text-[#2f81f7] font-semibold">
                            {assignment.available_capacity_after} HH
                          </span>
                        </div>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>

                    {/* Action Button: Inspect Audit */}
                    <td className="py-3 px-3 text-right">
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => onInspectAudit(assignment)}
                        leftIcon={<Eye className="h-3 w-3" />}
                        className="text-xs"
                      >
                        <span>Audit</span>
                      </Button>
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
