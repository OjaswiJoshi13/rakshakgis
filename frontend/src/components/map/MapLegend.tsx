"use client";

import React, { useState } from "react";
import { RISK_BANDS } from "@/design-system/tokens";

export interface MapLegendProps {
  className?: string;
}

export const MapLegend: React.FC<MapLegendProps> = ({ className = "" }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  return (
    <div
      className={`bg-surface-panel/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-md p-3 text-xs transition-all ${className}`}
      data-testid="map-legend"
    >
      {/* Legend Header & Collapse Toggle */}
      <div className="flex items-center justify-between gap-3 border-b border-border-subtle pb-2 mb-2">
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4 text-text-secondary"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
            />
          </svg>
          <span className="font-semibold text-text-primary text-xs">
            Operational Legend
          </span>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-text-muted hover:text-text-primary p-1 rounded hover:bg-surface-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? "Expand operational map legend" : "Collapse operational map legend"}
        >
          <svg
            className={`w-3.5 h-3.5 transform transition-transform ${isCollapsed ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {!isCollapsed && (
        <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
          {/* Section 1: Settlement Risk Classification (Authoritative 5 Bands) */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-1.5">
              Habitation Risk Bands
            </div>
            <div className="grid grid-cols-1 gap-1">
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] ring-1 ring-white dark:ring-slate-900 inline-block shrink-0" />
                  <span className="text-text-secondary">Safe</span>
                </div>
                <span className="font-mono text-[10px] text-text-muted">&lt; 25</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b] ring-1 ring-white dark:ring-slate-900 inline-block shrink-0" />
                  <span className="text-text-secondary">Moderate</span>
                </div>
                <span className="font-mono text-[10px] text-text-muted">25 – 49</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#ea580c] ring-1 ring-white dark:ring-slate-900 inline-block shrink-0" />
                  <span className="text-text-secondary">High</span>
                </div>
                <span className="font-mono text-[10px] text-text-muted">50 – 69</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#f43f5e] ring-1 ring-white dark:ring-slate-900 inline-block shrink-0" />
                  <span className="text-text-secondary">Very High</span>
                </div>
                <span className="font-mono text-[10px] text-text-muted">70 – 84</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#dc2626] ring-1 ring-white dark:ring-slate-900 inline-block shrink-0" />
                  <span className="text-text-secondary font-medium text-red-600 dark:text-red-400">Critical / Red</span>
                </div>
                <span className="font-mono text-[10px] text-text-muted">85 – 100</span>
              </div>
            </div>
          </div>

          {/* Section 2: Operational Infrastructure & Demarcations */}
          <div className="border-t border-border-subtle pt-2">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-1.5">
              Demarcations & Corridors
            </div>
            <div className="space-y-1.5 text-[11px]">
              {/* Red Zone */}
              <div className="flex items-center gap-2">
                <span
                  className="w-4 h-3 rounded-xs border border-dashed border-[#b91c1c] bg-[#dc2626]/45 inline-block shrink-0"
                  title="Red Zone"
                />
                <span className="text-text-secondary">Demarcated Red Zone</span>
              </div>

              {/* Evacuation Route */}
              <div className="flex items-center gap-2">
                <span className="w-4 h-1 rounded-xs bg-[#059669] inline-block shrink-0" title="Evacuation Corridor" />
                <span className="text-text-secondary">Evacuation Route</span>
              </div>

              {/* Candidate Site */}
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#10b981] border-2 border-white dark:border-slate-900 inline-block shrink-0" />
                <span className="text-text-secondary">Candidate Relocation Site</span>
              </div>

              {/* Selected Feature Highlight */}
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded-full border-2 border-[#0284c7] bg-[#38bdf8]/40 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#0284c7]" />
                </span>
                <span className="text-text-secondary">Selected Settlement</span>
              </div>

              {/* Earthquake / Seismic */}
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#dc2626] border border-red-200 inline-block shrink-0" />
                <span className="text-text-secondary">Earthquake (NCS / USGS)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
