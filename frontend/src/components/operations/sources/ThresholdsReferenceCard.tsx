"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Clock, Info, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { CATEGORY_FRESHNESS_THRESHOLDS } from "@/lib/api/telemetry";

export const ThresholdsReferenceCard: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Clock className="h-4 w-4 text-sky-400" />
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Platform Freshness Thresholds & Clock-Skew Policies
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Chunk M3-13 deterministic category expiration cutoffs (Rainfall 1h, Flood 1h, Landslide 24h, Sensors 1h, Census 7d)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-slate-400 border-slate-700 hidden sm:inline-flex">
            5 Categories
          </Badge>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="p-4 pt-0 border-t border-slate-800/60 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-3">
            {CATEGORY_FRESHNESS_THRESHOLDS.map((cat) => (
              <div
                key={cat.category}
                className="rounded border border-slate-800/80 bg-slate-950/60 p-3 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">{cat.name}</span>
                  <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-800/60 text-[10px]">
                    {cat.threshold_seconds < 86400
                      ? `${cat.threshold_seconds / 3600} Hour`
                      : `${cat.threshold_seconds / 86400} Days`}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400 font-mono leading-relaxed">
                  {cat.description}
                </p>
                <div className="text-[10px] font-mono text-slate-500">
                  Threshold: {cat.threshold_seconds.toLocaleString()} seconds
                </div>
              </div>
            ))}

            {/* Clock Skew Tolerance */}
            <div className="rounded border border-purple-900/40 bg-purple-950/20 p-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-200">Clock-Skew Guard</span>
                <Badge variant="outline" size="sm" className="font-mono text-purple-300 border-purple-700/60 text-[10px]">
                  60 Seconds
                </Badge>
              </div>
              <p className="text-[11px] text-slate-400 font-mono leading-relaxed">
                Observations with timestamps exceeding current server time by &gt;60s are flagged as CLOCK_SKEW.
              </p>
              <div className="text-[10px] font-mono text-purple-400/80">
                Guard: Max acceptable future drift
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500 pt-1">
            <Info className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <span>
              Invariants: Missing timestamps strictly evaluate to UNKNOWN. Future timestamps beyond 60s flag CLOCK_SKEW. Offline adapters flag UNAVAILABLE.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
