"use client";

import React from "react";
import { Button } from "@/components/ui/Button";
import { AuditActionCategory } from "@/types/audit";
import { Search, RotateCcw, Filter } from "lucide-react";

interface AuditFilterBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCategory: AuditActionCategory;
  onCategoryChange: (category: AuditActionCategory) => void;
  selectedStatus: string;
  onStatusChange: (status: string) => void;
  selectedTimeRange: "all" | "24h" | "7d" | "30d";
  onTimeRangeChange: (timeRange: "all" | "24h" | "7d" | "30d") => void;
  onReset: () => void;
  totalResults: number;
}

export const AuditFilterBar: React.FC<AuditFilterBarProps> = ({
  searchQuery,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
  selectedStatus,
  onStatusChange,
  selectedTimeRange,
  onTimeRangeChange,
  onReset,
  totalResults,
}) => {
  const hasActiveFilters =
    Boolean(searchQuery.trim()) ||
    selectedCategory !== "all" ||
    selectedStatus !== "all" ||
    selectedTimeRange !== "all";

  return (
    <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            id="audit-search"
            aria-label="Search audit records"
            placeholder="Search by actor, ID, target entity, rationale, or engine..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-md border border-slate-800 bg-slate-950/80 pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            data-testid="audit-search-input"
          />
        </div>

        {/* Dropdown Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <select
              aria-label="Filter by event category"
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value as AuditActionCategory)}
              className="rounded-md border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none font-mono"
              data-testid="audit-category-select"
            >
              <option value="all">All Categories</option>
              <option value="officer_decision">Officer Decisions (Rule 12)</option>
              <option value="relocation_assignment">Relocation Allocations</option>
              <option value="scenario_run">Scenario Runs</option>
              <option value="alert_trigger">Alerts & Warnings</option>
              <option value="telemetry_probe">Telemetry Diagnostics</option>
              <option value="report_export">Report Exports</option>
            </select>
          </div>

          {/* Decision Status Filter */}
          <select
            aria-label="Filter by decision status"
            value={selectedStatus}
            onChange={(e) => onStatusChange(e.target.value)}
            className="rounded-md border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none font-mono"
            data-testid="audit-status-select"
          >
            <option value="all">All Statuses</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="revision_requested">Revision Requested</option>
            <option value="committed">Committed</option>
            <option value="executed">Executed</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="exported">Exported</option>
          </select>

          {/* Time Range Filter */}
          <select
            aria-label="Filter by time range"
            value={selectedTimeRange}
            onChange={(e) => onTimeRangeChange(e.target.value as "all" | "24h" | "7d" | "30d")}
            className="rounded-md border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none font-mono"
            data-testid="audit-time-select"
          >
            <option value="all">All Time</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          {/* Reset Filters Button */}
          {hasActiveFilters && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={onReset}
              className="text-xs gap-1 h-8"
              data-testid="audit-reset-filters-btn"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset</span>
            </Button>
          )}
        </div>
      </div>

      {/* Result Counter & Active Filter Indicators */}
      <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-1 border-t border-slate-800/60">
        <span>
          Showing <strong className="text-slate-200">{totalResults}</strong> audit trail events
        </span>
        <span className="text-[11px] text-slate-500">
          Strictly Read-Only • Tamper-Evident Immutable Log
        </span>
      </div>
    </div>
  );
};
