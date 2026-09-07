"use client";

import React from "react";
import { Search, RotateCcw, Filter } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { DataSourceFilterCriteria } from "@/types/telemetry";

export interface SourceFilterBarProps {
  criteria: DataSourceFilterCriteria;
  onCriteriaChange: (updated: DataSourceFilterCriteria) => void;
  onReset: () => void;
  totalFiltered: number;
  totalAvailable: number;
}

export const SourceFilterBar: React.FC<SourceFilterBarProps> = ({
  criteria,
  onCriteriaChange,
  onReset,
  totalFiltered,
  totalAvailable,
}) => {
  const hasActiveFilters =
    (criteria.search && criteria.search.trim().length > 0) ||
    (criteria.category && criteria.category !== "all") ||
    (criteria.health && criteria.health !== "all") ||
    (criteria.freshness && criteria.freshness !== "all") ||
    (criteria.mode && criteria.mode !== "all");

  return (
    <div className="rounded-lg border border-border-subtle bg-surface-panel p-4 space-y-4 shadow-sm">
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <label htmlFor="sources-search-input" className="sr-only">
            Search Data Sources
          </label>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            id="sources-search-input"
            type="text"
            placeholder="Search by source name, type, provider ID, or endpoint URL..."
            value={criteria.search || ""}
            onChange={(e) =>
              onCriteriaChange({ ...criteria, search: e.target.value })
            }
            className="w-full bg-surface-elevated border border-border-subtle rounded-md pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-sky-500 transition-colors"
          />
        </div>

        {/* Reset Action */}
        {hasActiveFilters && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onReset}
            leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
            className="text-xs text-text-muted hover:text-text-primary self-end md:self-auto"
          >
            <span>Reset Filters</span>
          </Button>
        )}
      </div>

      {/* Filter Dropdowns Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-border-subtle">
        {/* 1. Category */}
        <div className="space-y-1">
          <label
            htmlFor="sources-category-filter"
            className="block text-[11px] font-medium text-text-secondary font-mono flex items-center gap-1"
          >
            <Filter className="h-3 w-3 text-text-muted" /> Category
          </label>
          <select
            id="sources-category-filter"
            value={criteria.category || "all"}
            onChange={(e) =>
              onCriteriaChange({ ...criteria, category: e.target.value })
            }
            className="w-full bg-surface-elevated border border-border-subtle rounded-md px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="all">All Categories</option>
            <option value="rainfall">Rainfall (Meteorological)</option>
            <option value="flood">Flood (Hydrological)</option>
            <option value="landslide">Landslide (Geological)</option>
            <option value="hazard_observation">IoT Sensors (In-Situ)</option>
            <option value="population_exposure">Demographics (Census)</option>
          </select>
        </div>

        {/* 2. Provider Health */}
        <div className="space-y-1">
          <label
            htmlFor="sources-health-filter"
            className="block text-[11px] font-medium text-text-secondary font-mono"
          >
            Provider Health
          </label>
          <select
            id="sources-health-filter"
            value={criteria.health || "all"}
            onChange={(e) =>
              onCriteriaChange({ ...criteria, health: e.target.value })
            }
            className="w-full bg-surface-elevated border border-border-subtle rounded-md px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="all">All Health States</option>
            <option value="healthy">Healthy (Operational)</option>
            <option value="degraded">Degraded (Warning)</option>
            <option value="unavailable">Unavailable (Offline)</option>
          </select>
        </div>

        {/* 3. Freshness Status */}
        <div className="space-y-1">
          <label
            htmlFor="sources-freshness-filter"
            className="block text-[11px] font-medium text-text-secondary font-mono"
          >
            Freshness Status
          </label>
          <select
            id="sources-freshness-filter"
            value={criteria.freshness || "all"}
            onChange={(e) =>
              onCriteriaChange({ ...criteria, freshness: e.target.value })
            }
            className="w-full bg-surface-elevated border border-border-subtle rounded-md px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="all">All Freshness States</option>
            <option value="fresh">Fresh (Within Cutoff)</option>
            <option value="stale">Stale (Exceeded Cutoff)</option>
            <option value="clock_skew">Clock Skew (Future Drift)</option>
            <option value="unavailable">Unavailable (No Data)</option>
            <option value="unknown">Unknown (Missing Time)</option>
          </select>
        </div>

        {/* 4. Provider Mode */}
        <div className="space-y-1">
          <label
            htmlFor="sources-mode-filter"
            className="block text-[11px] font-medium text-text-secondary font-mono"
          >
            Adapter Mode
          </label>
          <select
            id="sources-mode-filter"
            value={criteria.mode || "all"}
            onChange={(e) =>
              onCriteriaChange({ ...criteria, mode: e.target.value })
            }
            className="w-full bg-surface-elevated border border-border-subtle rounded-md px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="all">All Modes</option>
            <option value="mock">Mock / Synthetic</option>
            <option value="live">Live Provider</option>
            <option value="file">File System</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>
      </div>

      {/* Result Counter */}
      <div className="flex items-center justify-between text-[11px] font-mono text-text-muted pt-1">
        <span>
          Showing <strong className="text-text-primary">{totalFiltered}</strong> of{" "}
          <strong className="text-text-primary">{totalAvailable}</strong> registered data sources
        </span>
        {hasActiveFilters && (
          <span className="text-sky-600 dark:text-sky-400 font-semibold">Filters active</span>
        )}
      </div>
    </div>
  );
};
