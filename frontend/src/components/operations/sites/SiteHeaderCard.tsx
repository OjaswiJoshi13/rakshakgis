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
  const isApproved = site.status.toLowerCase() === "approved";
  const isRejected = site.status.toLowerCase() === "rejected";
  const isSlopeSafe = site.terrain_slope_deg != null && site.terrain_slope_deg <= 15.0;

  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/80 p-4">
      {/* Top Banner: Name, ID, District & Status */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant={isApproved ? "success" : isRejected ? "danger" : "default"}
              size="sm"
              className="font-mono text-xs uppercase"
            >
              {site.status}
            </Badge>
            <span className="text-xs font-mono text-slate-500">
              Site ID: #{site.id} • District #{site.district_id}
            </span>
          </div>

          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-sky-400 shrink-0" />
            <span>{site.name}</span>
          </h2>
        </div>

        {/* Topographic Quick Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="rounded bg-slate-950 px-3 py-1.5 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Coordinates</span>
            <span className="text-slate-200">
              {site.location.coordinates[0].toFixed(3)}°E, {site.location.coordinates[1].toFixed(3)}°N
            </span>
          </div>

          <div className="rounded bg-slate-950 px-3 py-1.5 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Total Area</span>
            <span className="text-slate-200">
              {site.area_sq_m != null
                ? `${site.area_sq_m.toLocaleString()} m²`
                : "Unspecified"}
            </span>
          </div>

          <div className="rounded bg-slate-950 px-3 py-1.5 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Terrain Slope</span>
            <span className={isSlopeSafe ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
              {site.terrain_slope_deg != null ? `${site.terrain_slope_deg}°` : "N/A"}
              {site.terrain_slope_deg != null && (
                <span className="text-[10px] font-normal text-slate-500 ml-1">
                  ({isSlopeSafe ? "Safe ≤15°" : "Unsafe >15°"})
                </span>
              )}
            </span>
          </div>

          <div className="rounded bg-slate-950 px-3 py-1.5 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Elevation</span>
            <span className="text-slate-200">
              {site.elevation_m != null ? `${site.elevation_m} m AMSL` : "Unspecified"}
            </span>
          </div>
        </div>
      </div>

      {/* Domain Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "infrastructure"}
            onClick={() => onTabChange("infrastructure")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "infrastructure"
                ? "bg-sky-600 text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Overview & Infrastructure ({site.infrastructures.length})</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "suitability"}
            onClick={() => onTabChange("suitability")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "suitability"
                ? "bg-sky-600 text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Scale className="h-3.5 w-3.5" />
            <span>Suitability Criteria (M4-02)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "capacity"}
            onClick={() => onTabChange("capacity")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeTab === "capacity"
                ? "bg-sky-600 text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Carrying Capacity & Sizing (M4-03)</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-slate-500">
          Last Updated: {new Date(site.updated_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};
