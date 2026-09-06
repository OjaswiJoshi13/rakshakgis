"use client";

import React from "react";
import { useOperational } from "@/context/OperationalContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export interface MapHeaderProps {
  totalSites?: number;
  totalRoutes?: number;
  totalRedZones?: number;
  totalVillages?: number;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  onResetView?: () => void;
  className?: string;
}

export const MapHeader: React.FC<MapHeaderProps> = ({
  totalSites = 0,
  totalRoutes = 0,
  totalRedZones = 0,
  totalVillages = 0,
  isRefreshing = false,
  onRefresh,
  onResetView,
  className = "",
}) => {
  const { activeRegion, dataMode } = useOperational();

  return (
    <div className={`border-b border-slate-800 pb-4 ${className}`}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Branding & Operational Status */}
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-sky-400 bg-sky-950/80 border border-sky-800 px-2 py-0.5 rounded">
              Spatial Decision Support
            </span>
            <Badge variant="outline" size="sm" className="font-mono">
              Region: {activeRegion}
            </Badge>
            <span
              data-testid="map-data-mode"
              className={`text-xs font-mono font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                dataMode === "live"
                  ? "bg-emerald-950/80 border-emerald-700 text-emerald-300"
                  : "bg-amber-950/80 border-amber-700 text-amber-300"
              }`}
            >
              Mode: {dataMode === "live" ? "LIVE (Telemetry)" : "DEMO (Synthetic)"}
            </span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            Command GIS Map Canvas
          </h1>

          <p className="text-xs text-slate-400 max-w-2xl">
            Interactive multi-hazard geospatial canvas visualizing candidate relocation safe havens,
            evacuation road corridors, and regional zoning bounds.
          </p>
        </div>

        {/* Right: Metrics & Viewport Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Active Features Count Badge */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-300">
            <span className="w-2 h-2 rounded-full bg-sky-400" />
            <span>
              {totalSites} Havens &bull; {totalRoutes} Corridors
              {totalRedZones > 0 ? ` • ${totalRedZones} Red Zones` : ""}
              {totalVillages > 0 ? ` • ${totalVillages} Habitations` : ""}
            </span>
          </div>

          {/* Reset View Button */}
          {onResetView && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onResetView}
              className="font-mono text-xs"
              title="Recenter and fit map to loaded features"
            >
              <svg className="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Fit Bounds
            </Button>
          )}

          {/* Refresh Data Button */}
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              isLoading={isRefreshing}
              className="font-mono text-xs"
              title="Refresh spatial layers from backend"
            >
              <svg
                className={`w-3.5 h-3.5 mr-1 ${isRefreshing ? "animate-spin" : ""}`}
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
              Refresh
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
