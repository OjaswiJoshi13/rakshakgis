"use client";

import React, { useState, useMemo } from "react";
import { CandidateSiteRead } from "@/types/sites";
import { Badge } from "@/components/ui/Badge";
import { Search, Building2, Mountain, MapPin, Compass } from "lucide-react";

export interface SiteSelectorCardProps {
  sites: CandidateSiteRead[];
  selectedSiteId: number | null;
  onSelectSite: (id: number) => void;
  isLoading?: boolean;
}

export const SiteSelectorCard: React.FC<SiteSelectorCardProps> = ({
  sites,
  selectedSiteId,
  onSelectSite,
  isLoading = false,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredSites = useMemo(() => {
    return sites.filter((site) => {
      if (statusFilter !== "all" && site.status.toLowerCase() !== statusFilter.toLowerCase()) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = site.name.toLowerCase().includes(q);
        const matchesId = String(site.id).includes(q);
        return matchesName || matchesId;
      }
      return true;
    });
  }, [sites, statusFilter, searchQuery]);

  return (
    <div className="space-y-3 rounded-lg border border-border-subtle bg-surface-panel p-3.5 shadow-xs">
      {/* Selector Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-mono uppercase tracking-wider text-text-muted flex items-center gap-1.5">
          <Building2 className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
          <span>Candidate Sites ({sites.length})</span>
        </h3>
        <span className="text-[11px] font-mono text-text-muted">
          Registry
          <span className="sr-only">M4-01 Registry</span>
        </span>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search site name or ID..."
          className="w-full rounded-md border border-border-subtle bg-surface-elevated pl-8 pr-2.5 py-1.5 text-xs text-text-primary placeholder-text-muted focus:border-primary-500 focus:outline-hidden font-mono"
        />
      </div>

      {/* Status Filter Chips */}
      <div className="flex items-center gap-1 overflow-x-auto text-[11px] font-mono pb-1">
        {["all", "approved", "proposed", "rejected"].map((st) => (
          <button
            key={st}
            type="button"
            onClick={() => setStatusFilter(st)}
            className={`px-2 py-0.5 rounded capitalize transition-colors ${
              statusFilter === st
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "bg-surface-elevated text-text-secondary hover:text-text-primary border border-border-subtle"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Sites List */}
      {isLoading ? (
        <div className="py-8 text-center text-xs text-text-muted">
          Loading candidate sites...
        </div>
      ) : filteredSites.length === 0 ? (
        <div className="rounded border border-dashed border-border-strong p-4 text-center text-xs text-text-muted font-mono">
          No sites match filter criteria.
        </div>
      ) : (
        <div className="space-y-1.5 max-h-[520px] overflow-y-auto pr-1">
          {filteredSites.map((site) => {
            const isSelected = selectedSiteId === site.id;
            const isApproved = site.status.toLowerCase() === "approved";
            const isRejected = site.status.toLowerCase() === "rejected";

            return (
              <button
                key={site.id}
                type="button"
                onClick={() => onSelectSite(site.id)}
                className={`w-full text-left rounded-lg p-2.5 transition-all border ${
                  isSelected
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-950/40 shadow-xs ring-1 ring-primary-500 text-text-primary"
                    : "border-border-subtle bg-surface-elevated hover:bg-surface-raised hover:border-border-strong text-text-secondary"
                }`}
              >
                <div className="flex items-start justify-between gap-1 mb-1">
                  <span className="font-semibold text-xs text-text-primary line-clamp-1">
                    {site.name}
                  </span>
                  <Badge
                    variant={isApproved ? "success" : isRejected ? "danger" : "default"}
                    size="sm"
                    className="text-[10px] shrink-0"
                  >
                    {site.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-1 text-[11px] font-mono text-text-muted">
                  <span title="Elevation">
                    {site.elevation_m != null ? `${site.elevation_m}m` : "—"}
                  </span>
                  <span title="Terrain Slope">
                    {site.terrain_slope_deg != null ? `${site.terrain_slope_deg}°` : "—"}
                  </span>
                  <span title="Site Area" className="text-right">
                    {site.area_sq_m != null
                      ? `${Math.round(site.area_sq_m / 1000)}k m²`
                      : "—"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
