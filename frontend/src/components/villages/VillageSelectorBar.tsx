"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { HabitationDetail } from "@/types/villages";
import { useOperational } from "@/context/OperationalContext";

export interface VillageSelectorBarProps {
  villages: HabitationDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const VillageSelectorBar: React.FC<VillageSelectorBarProps> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  searchQuery,
  onSearchChange,
  isRefreshing = false,
  onRefresh,
  isLoading = false,
}) => {
  const { dataMode, activeRegion } = useOperational();

  const filteredVillages = villages.filter(
    (v) =>
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div
      className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6 shadow-sm"
      role="region"
      aria-label="Habitation Selector"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Search & Filter */}
        <div className="flex-1 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <span
              className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500"
              aria-hidden="true"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </span>
            <input
              type="text"
              id="village-search-input"
              aria-label="Filter habitations by name or ID"
              placeholder="Search settlements by name or ID..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>

          {/* Quick Dropdown / Selector */}
          <div className="flex items-center gap-2">
            <label htmlFor="habitation-dropdown" className="text-xs text-slate-400 font-mono shrink-0">
              Select:
            </label>
            <select
              id="habitation-dropdown"
              aria-label="Select habitation"
              value={selectedVillageId || ""}
              onChange={(e) => onSelectVillage(e.target.value)}
              disabled={isLoading || villages.length === 0}
              className="bg-slate-950 border border-slate-700 rounded text-sm text-slate-200 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              {villages.length === 0 ? (
                <option value="">No habitations available</option>
              ) : (
                filteredVillages.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.id})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {/* Right: Operational Status & Controls */}
        <div className="flex items-center gap-3 self-end md:self-center flex-wrap">
          {/* Operational Data Mode Badge */}
          <Badge
            variant={dataMode === "live" ? "success" : dataMode === "simulation" ? "warning" : "info"}
            size="sm"
            aria-label={`Operational Mode: ${String(dataMode).toUpperCase()}`}
          >
            {String(dataMode).toUpperCase()} MODE
          </Badge>

          {/* Active Region Indicator */}
          <span className="text-xs font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
            Region: {activeRegion}
          </span>

          {/* Habitations Count */}
          <span className="text-xs font-mono text-slate-300" aria-live="polite">
            {villages.length} Baseline {villages.length === 1 ? "Settlement" : "Settlements"}
          </span>

          {/* Refresh Action */}
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isRefreshing || isLoading}
              aria-label="Refresh habitation risk and vulnerability assessment data"
              className="text-xs h-8"
            >
              {isRefreshing ? (
                <>
                  <svg
                    className="w-3.5 h-3.5 mr-1.5 animate-spin text-slate-400"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Refreshing...
                </>
              ) : (
                <>
                  <svg
                    className="w-3.5 h-3.5 mr-1.5 text-slate-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Refresh Data
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
