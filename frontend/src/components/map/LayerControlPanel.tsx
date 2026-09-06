"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { MapLayerConfig } from "@/types/gis";

export interface LayerControlPanelProps {
  layers: MapLayerConfig[];
  layerVisibility: Record<string, boolean>;
  onToggleLayer: (layerId: string) => void;
  featureCounts?: Record<string, number>;
  className?: string;
}

export const LayerControlPanel: React.FC<LayerControlPanelProps> = ({
  layers,
  layerVisibility,
  onToggleLayer,
  featureCounts = {},
  className = "",
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  return (
    <div
      className={`bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-xl shadow-2xl p-3.5 transition-all text-xs z-10 ${className}`}
      data-testid="layer-control-panel"
    >
      {/* Header with Collapse Button */}
      <div className="flex items-center justify-between gap-4 border-b border-slate-800/80 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4 text-sky-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          <span className="font-semibold text-slate-100 uppercase tracking-wider font-mono text-[11px]">
            GIS Layer Controls
          </span>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? "Expand GIS layer controls" : "Collapse GIS layer controls"}
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

      {/* Layer Items */}
      {!isCollapsed && (
        <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
          {layers.map((layer) => {
            const isAvailable = layer.status === "available";
            const isVisible = isAvailable && (layerVisibility[layer.id] ?? layer.defaultVisible);
            const count = featureCounts[layer.id];

            return (
              <div
                key={layer.id}
                className={`flex flex-col gap-1 p-2 rounded-lg border transition-colors ${
                  isAvailable
                    ? isVisible
                      ? "bg-slate-900/80 border-slate-700/80"
                      : "bg-slate-950/60 border-slate-800/60 opacity-75"
                    : "bg-slate-950/40 border-slate-900 opacity-60"
                }`}
                data-testid={`layer-item-${layer.id}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <label
                    htmlFor={`toggle-layer-${layer.id}`}
                    className={`flex items-center gap-2 cursor-pointer select-none ${
                      !isAvailable ? "cursor-not-allowed" : ""
                    }`}
                  >
                    <input
                      id={`toggle-layer-${layer.id}`}
                      type="checkbox"
                      checked={isVisible}
                      disabled={!isAvailable}
                      onChange={() => onToggleLayer(layer.id)}
                      className="rounded border-slate-700 text-sky-600 focus:ring-sky-500 bg-slate-950 h-3.5 w-3.5 cursor-pointer disabled:cursor-not-allowed"
                      aria-label={`Toggle visibility of ${layer.name}`}
                    />
                    <span
                      className={`font-medium ${
                        isVisible ? "text-slate-100" : "text-slate-400"
                      }`}
                    >
                      {layer.name}
                    </span>
                  </label>

                  {/* Status & Count Badges */}
                  <div className="flex items-center gap-1.5">
                    {isAvailable ? (
                      count !== undefined ? (
                        <span className="font-mono text-[10px] text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                          {count} {count === 1 ? "feature" : "features"}
                        </span>
                      ) : (
                        <Badge variant="success" size="sm" className="text-[9px]">
                          Active
                        </Badge>
                      )
                    ) : (
                      <Badge variant="outline" size="sm" className="text-[9px] text-slate-400">
                        Pending
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Description or Pending Note */}
                <p className="text-[10px] text-slate-400 pl-5 leading-tight">
                  {!isAvailable && layer.pendingNote ? (
                    <span className="text-amber-400/90 font-mono">{layer.pendingNote}</span>
                  ) : (
                    layer.description
                  )}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
