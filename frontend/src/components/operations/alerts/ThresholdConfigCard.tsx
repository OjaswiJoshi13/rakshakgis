"use client";

import React, { useState } from "react";
import { DynamicThresholdSummary } from "@/types/alerts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ChevronDown, ChevronUp, Sliders, ShieldAlert } from "lucide-react";

export interface ThresholdConfigCardProps {
  thresholds: DynamicThresholdSummary;
}

export const ThresholdConfigCard: React.FC<ThresholdConfigCardProps> = ({ thresholds }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card variant="bordered" className="bg-surface-panel border-border-subtle shadow-xs">
      <CardHeader className="pb-2 cursor-pointer select-none" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <div>
              <CardTitle className="text-sm font-semibold text-text-primary">
                Authoritative Dynamic Trigger Thresholds
              </CardTitle>
              <CardDescription className="text-xs text-text-muted">
                Resolved from regional profile: <span className="font-mono text-text-secondary">{thresholds.profile_name}</span>
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" size="sm" className="font-mono text-[10px] text-sky-700 dark:text-sky-400 border-sky-300 dark:border-sky-600/40">
              Profile: {thresholds.profile_id}
            </Badge>
            <button
              type="button"
              className="p-1 rounded text-text-muted hover:text-text-primary"
              aria-label={isExpanded ? "Collapse thresholds" : "Expand thresholds"}
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-2 space-y-3 border-t border-border-subtle">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-1 font-mono text-xs">
            {/* 24h Rainfall */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">24h Rainfall</span>
              <span className="font-bold text-text-primary">&ge; {thresholds.rainfall_trigger_24h_mm} mm</span>
              <span className="text-[10px] text-text-muted block">Regional heavy rainfall threshold (64.5 mm)</span>
            </div>

            {/* Seismic MMI */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">Seismic Intensity</span>
              <span className="font-bold text-text-primary">&ge; {thresholds.seismic_trigger_mmi || 6.0} MMI</span>
              <span className="text-[10px] text-text-muted block">Felt motion threshold</span>
            </div>

            {/* Slope Angle */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">Critical Slope</span>
              <span className="font-bold text-text-primary">&ge; {thresholds.slope_trigger_min_deg}&deg;</span>
              <span className="text-[10px] text-text-muted block">Compound hazard gate</span>
            </div>

            {/* Water Level */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">Hydrological Stage</span>
              <span className="font-bold text-text-primary">&ge; {thresholds.water_level_trigger_m_above_danger || 1.5} m</span>
              <span className="text-[10px] text-text-muted block">Above danger mark</span>
            </div>

            {/* Geodesic Buffer */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">Safety Buffer</span>
              <span className="font-bold text-text-primary">{thresholds.buffer_distance_m} m</span>
              <span className="text-[10px] text-text-muted block">Geodesic perimeter</span>
            </div>

            {/* Default Danger */}
            <div className="bg-surface-elevated p-2 rounded border border-border-subtle">
              <span className="text-[10px] uppercase text-text-muted block mb-0.5">Candidate Rating</span>
              <span className="font-bold text-red-700 dark:text-red-400">{thresholds.default_danger_level}</span>
              <span className="text-[10px] text-text-muted block">Default trigger band</span>
            </div>
          </div>

          <div className="flex items-start gap-2 bg-surface-elevated p-2.5 rounded border border-border-subtle text-xs text-text-secondary leading-relaxed">
            <ShieldAlert className="h-4 w-4 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
            <span>
              <strong>Deterministic Evaluation Standard:</strong> <span className="sr-only">M3-11</span> Sensor inputs are evaluated deterministically using an explicit 3-state model (<code className="text-emerald-700 dark:text-emerald-300 font-semibold">NO_TRIGGER</code>, <code className="text-red-700 dark:text-red-300 font-semibold">TRIGGERED</code>, <code className="text-amber-700 dark:text-amber-300 font-semibold">INSUFFICIENT_DATA</code>). Missing or offline sensor feeds strictly trigger <code className="text-amber-700 dark:text-amber-300 font-semibold">INSUFFICIENT_DATA</code> to ensure zero safety hazards are concealed.
            </span>
          </div>
        </CardContent>
      )}
    </Card>
  );
};
