"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Clock, Info } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { CATEGORY_FRESHNESS_THRESHOLDS } from "@/lib/api/telemetry";

export const ThresholdsReferenceCard: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-border-subtle bg-surface-panel overflow-hidden shadow-sm">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-elevated transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Clock className="h-4 w-4 text-sky-600 dark:text-sky-400" />
          <div>
            <h3 className="text-sm font-semibold text-text-primary">
              Platform Freshness Thresholds & Clock-Skew Policies
            </h3>
            <p className="text-xs text-text-muted font-mono">
              Deterministic category expiration cutoffs (Rainfall 1h, Flood 1h, Landslide 24h, Sensors 1h, Census 7d) <span className="sr-only">Chunk M3-13</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-text-muted border-border-subtle hidden sm:inline-flex">
            5 Categories
          </Badge>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="p-4 pt-0 border-t border-border-subtle space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-3">
            {CATEGORY_FRESHNESS_THRESHOLDS.map((cat) => (
              <div
                key={cat.category}
                className="rounded border border-border-subtle bg-surface-elevated p-3 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-text-primary">{cat.name}</span>
                  <Badge variant="outline" size="sm" className="font-mono text-sky-700 dark:text-sky-300 border-sky-400/40 text-[10px]">
                    {cat.threshold_seconds < 86400
                      ? `${cat.threshold_seconds / 3600} Hour`
                      : `${cat.threshold_seconds / 86400} Days`}
                  </Badge>
                </div>
                <p className="text-[11px] text-text-secondary font-mono leading-relaxed">
                  {cat.description}
                </p>
                <div className="text-[10px] font-mono text-text-muted">
                  Threshold: {cat.threshold_seconds.toLocaleString()} seconds
                </div>
              </div>
            ))}

            {/* Clock Skew Tolerance */}
            <div className="rounded border border-purple-300 dark:border-purple-900/40 bg-purple-50 dark:bg-purple-950/20 p-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-900 dark:text-purple-200">Clock-Skew Guard</span>
                <Badge variant="outline" size="sm" className="font-mono text-purple-800 dark:text-purple-300 border-purple-400 dark:border-purple-700/60 text-[10px]">
                  60 Seconds
                </Badge>
              </div>
              <p className="text-[11px] text-purple-950/80 dark:text-slate-400 font-mono leading-relaxed">
                Observations with timestamps exceeding current server time by &gt;60s are flagged as CLOCK_SKEW.
              </p>
              <div className="text-[10px] font-mono text-purple-700 dark:text-purple-400/80">
                Guard: Max acceptable future drift
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-mono text-text-muted pt-1">
            <Info className="h-3.5 w-3.5 text-text-muted shrink-0" />
            <span>
              Invariants: Missing timestamps strictly evaluate to UNKNOWN. Future timestamps beyond 60s flag CLOCK_SKEW. Offline adapters flag UNAVAILABLE.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
