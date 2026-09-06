"use client";

import React from "react";
import { AlertFilterCriteria } from "@/types/alerts";
import { Search, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";

export interface AlertFilterBarProps {
  filters: AlertFilterCriteria;
  onFilterChange: (newFilters: AlertFilterCriteria) => void;
  totalFiltered: number;
  totalAll: number;
}

export const AlertFilterBar: React.FC<AlertFilterBarProps> = ({
  filters,
  onFilterChange,
  totalFiltered,
  totalAll,
}) => {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, search: e.target.value });
  };

  const handleSeverityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      severity: e.target.value as AlertFilterCriteria["severity"],
    });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      status: e.target.value as AlertFilterCriteria["status"],
    });
  };

  const handleIndicatorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      indicator: e.target.value as AlertFilterCriteria["indicator"],
    });
  };

  const handleAckChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onFilterChange({
      ...filters,
      is_acknowledged:
        val === "all" ? "all" : val === "true" ? true : false,
    });
  };

  const handleReset = () => {
    onFilterChange({
      severity: "all",
      status: "all",
      indicator: "all",
      is_acknowledged: "all",
      search: "",
    });
  };

  const isFiltered =
    (filters.severity && filters.severity !== "all") ||
    (filters.status && filters.status !== "all") ||
    (filters.indicator && filters.indicator !== "all") ||
    (filters.is_acknowledged !== undefined && filters.is_acknowledged !== "all") ||
    Boolean(filters.search);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 sm:p-4 space-y-3">
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search Box */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
          <input
            type="text"
            value={filters.search || ""}
            onChange={handleSearchChange}
            placeholder="Search by settlement, district, headline, or zone ID..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
          />
        </div>

        {/* Filter Count & Reset */}
        <div className="flex items-center gap-2 self-end md:self-center">
          <span className="text-xs font-mono text-slate-400">
            Showing <strong className="text-slate-200">{totalFiltered}</strong> of{" "}
            {totalAll} alerts
          </span>
          {isFiltered && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="text-xs text-sky-400 hover:text-sky-300 h-7 px-2"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              <span>Reset</span>
            </Button>
          )}
        </div>
      </div>

      {/* Filter Selectors */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1 border-t border-slate-800/80">
        {/* Severity */}
        <div>
          <label
            htmlFor="alert-severity-select"
            className="block text-[10px] font-mono uppercase text-slate-400 mb-1"
          >
            Severity
          </label>
          <select
            id="alert-severity-select"
            value={filters.severity || "all"}
            onChange={handleSeverityChange}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="all">All Severities</option>
            <option value="extreme">Extreme / Critical</option>
            <option value="severe">Severe / High</option>
            <option value="warning">Warning / Moderate</option>
            <option value="info">Info / Normal</option>
          </select>
        </div>

        {/* Status */}
        <div>
          <label
            htmlFor="alert-status-select"
            className="block text-[10px] font-mono uppercase text-slate-400 mb-1"
          >
            M3-11 Status
          </label>
          <select
            id="alert-status-select"
            value={filters.status || "all"}
            onChange={handleStatusChange}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="all">All Statuses</option>
            <option value="triggered">Triggered (Candidate)</option>
            <option value="insufficient_data">Insufficient Data (Gap)</option>
            <option value="no_trigger">No Trigger (Below)</option>
          </select>
        </div>

        {/* Hazard Indicator */}
        <div>
          <label
            htmlFor="alert-indicator-select"
            className="block text-[10px] font-mono uppercase text-slate-400 mb-1"
          >
            Indicator
          </label>
          <select
            id="alert-indicator-select"
            value={filters.indicator || "all"}
            onChange={handleIndicatorChange}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="all">All Indicators</option>
            <option value="rainfall_24h">24h Rainfall (mm)</option>
            <option value="seismic_mmi">Seismic Tremor (MMI)</option>
            <option value="water_level_above_danger">Water Level (m)</option>
            <option value="landslide_debris_volume">Debris Volume (m³)</option>
          </select>
        </div>

        {/* Acknowledgment */}
        <div>
          <label
            htmlFor="alert-action-select"
            className="block text-[10px] font-mono uppercase text-slate-400 mb-1"
          >
            Officer Action
          </label>
          <select
            id="alert-action-select"
            value={
              filters.is_acknowledged === undefined || filters.is_acknowledged === "all"
                ? "all"
                : String(filters.is_acknowledged)
            }
            onChange={handleAckChange}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="all">All States</option>
            <option value="false">Pending Acknowledgment</option>
            <option value="true">Acknowledged</option>
          </select>
        </div>
      </div>
    </div>
  );
};
