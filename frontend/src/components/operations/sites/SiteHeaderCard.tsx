"use client";

import React from "react";
import { CandidateSiteDetailRead, SiteDetailTab } from "@/types/sites";
import { Badge } from "@/components/ui/Badge";
import {
  Building2,
  MapPin,
  Mountain,
  Compass,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Scale,
  Activity,
} from "lucide-react";

export interface SiteHeaderCardProps {
  site: CandidateSiteDetailRead;
  activeTab: SiteDetailTab;
  onTabChange: (tab: SiteDetailTab) => void;
}

export const SiteHeaderCard: React.FC<SiteHeaderCardProps> = ({
  site,
  activeTab,
  onTabChange,
}) => {
  const isRejected = site.status.toLowerCase() === "rejected";
  const isSlopeSafe = site.terrain_slope_deg != null && site.terrain_slope_deg <= 15.0;

  return (
    <div className="space-y-4 rounded-lg border border-border-subtle bg-surface-panel p-4 shadow-xs">
      {/* Top Banner: Name, ID, District & Status */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant={isRejected ? "danger" : "warning"}
              size="sm"
              className="font-mono text-xs uppercase"
            >
              {isRejected ? "REJECTED" : "PROPOSED / SYNTHETIC"}
            </Badge>
            <span className="text-xs font-mono text-text-muted">
              Site ID: #{site.id} • District #{site.district_id}
            </span>
          </div>

          <h2 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary-600 dark:text-primary-400 shrink-0" />
            <span>{site.name}</span>
          </h2>
        </div>

        {/* Topographic Quick Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="rounded bg-surface-elevated px-3 py-1.5 border border-border-subtle">
            <span className="text-text-muted block text-[10px] uppercase">Coordinates</span>
            <span className="text-text-primary">
              {site.location.coordinates[0].toFixed(3)}°E, {site.location.coordinates[1].toFixed(3)}°N
            </span>
          </div>

          <div className="rounded bg-surface-elevated px-3 py-1.5 border border-border-subtle">
            <span className="text-text-muted block text-[10px] uppercase">Total Area</span>
            <span className="text-text-primary">
              {site.area_sq_m != null
                ? `${site.area_sq_m.toLocaleString()} m²`
                : "Unspecified"}
            </span>
          </div>

          <div className="rounded bg-surface-elevated px-3 py-1.5 border border-border-subtle">
            <span className="text-text-muted block text-[10px] uppercase">Terrain Slope</span>
            <span className={isSlopeSafe ? "text-emerald-600 dark:text-emerald-400 font-bold" : "text-red-600 dark:text-red-400 font-bold"}>
              {site.terrain_slope_deg != null ? `${site.terrain_slope_deg}°` : "N/A"}
              {site.terrain_slope_deg != null && (
                <span className="text-[10px] font-normal text-text-muted ml-1">
                  ({isSlopeSafe ? "Safe ≤15°" : "Unsafe >15°"})
                </span>
              )}
            </span>
          </div>

          <div className="rounded bg-surface-elevated px-3 py-1.5 border border-border-subtle">
            <span className="text-text-muted block text-[10px] uppercase">Elevation</span>
            <span className="text-text-primary">
              {site.elevation_m != null ? `${site.elevation_m} m AMSL` : "Unspecified"}
            </span>
          </div>
        </div>
      </div>

      {/* Domain Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <div className="inline-flex rounded-lg bg-surface-elevated p-1 border border-border-subtle" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "infrastructure"}
            onClick={() => onTabChange("infrastructure")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "infrastructure"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Overview &amp; Infrastructure ({site.infrastructures.length})</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "suitability"}
            onClick={() => onTabChange("suitability")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "suitability"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Scale className="h-3.5 w-3.5" />
            <span>Suitability Criteria</span>
            <span className="sr-only"> (M4-02)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "capacity"}
            onClick={() => onTabChange("capacity")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "capacity"
                ? "bg-primary-600 text-white font-semibold shadow-xs"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Carrying Capacity &amp; Sizing</span>
            <span className="sr-only"> (M4-03)</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-text-muted">
          Last Updated: {new Date(site.updated_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};
