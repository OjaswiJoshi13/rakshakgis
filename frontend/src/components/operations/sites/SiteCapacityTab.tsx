"use client";

import React from "react";
import { SiteCapacityResult } from "@/types/sites";
import { MetricCard } from "@/components/ui/MetricCard";
import { Badge } from "@/components/ui/Badge";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Home,
  Droplets,
  Boxes,
  HeartPulse,
  Tent,
  FileText,
} from "lucide-react";

export interface SiteCapacityTabProps {
  capacity: SiteCapacityResult | null;
  isLoading?: boolean;
}

export const SiteCapacityTab: React.FC<SiteCapacityTabProps> = ({
  capacity,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="py-16 text-center text-xs text-slate-400">
        Loading carrying capacity and infrastructure sizing evaluation...
      </div>
    );
  }

  if (!capacity) {
    return (
      <div className="rounded-lg border border-dashed border-border-subtle p-8 text-center text-xs text-text-muted">
        No carrying capacity evaluation data available for this site.
      </div>
    );
  }

  const effectiveHH = capacity.effective_capacity_households ?? 0;
  const availableHH = capacity.available_capacity_households ?? 0;
  const occupancyHH = capacity.current_occupancy_households;

  const getDimensionIcon = (dim: string) => {
    switch (dim.toLowerCase()) {
      case "housing":
        return <Home className="h-4 w-4" />;
      case "water":
        return <Droplets className="h-4 w-4" />;
      case "sanitation":
        return <Boxes className="h-4 w-4" />;
      case "healthcare":
        return <HeartPulse className="h-4 w-4" />;
      case "shelter":
        return <Tent className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Weakest-Link Bottleneck Alert */}
      <div className="flex items-start gap-3 rounded-lg border border-primary-200 dark:border-sky-800/60 bg-primary-50 dark:bg-sky-950/30 p-4 text-xs text-primary-900 dark:text-sky-200">
        <Activity className="h-5 w-5 text-primary-600 dark:text-sky-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-primary-800 dark:text-sky-300 font-mono tracking-wide">
              Weakest-Link Bottleneck Invariant:
            </span>
            <Badge variant="outline" size="sm" className="font-mono text-primary-800 dark:text-sky-300 border-primary-300 dark:border-sky-600/50">
              min(housing, water, sanitation, healthcare, shelter)
            </Badge>
          </div>
          <p className="text-primary-900/90 dark:text-sky-200/90 leading-relaxed">
            Effective site carrying capacity is strictly governed by the most constrained physical or utility dimension.
            {capacity.limiting_factors.length > 0 && (
              <span>
                {" "}Primary limiting factor: <strong className="text-text-primary capitalize">{capacity.limiting_factors.join(", ")}</strong>.
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard
          label="Effective Carrying Capacity"
          value={effectiveHH.toLocaleString()}
          unit="HH"
          subtext="Weakest-link bound across 5 dimensions"
          status="info"
          icon={<Home className="h-4 w-4" />}
        />

        <MetricCard
          label="Current Occupancy"
          value={occupancyHH.toLocaleString()}
          unit="HH"
          subtext="Allocated household population"
          status={occupancyHH > 0 ? "warning" : "normal"}
          icon={<Activity className="h-4 w-4" />}
        />

        <MetricCard
          label="Available Capacity Margin"
          value={availableHH.toLocaleString()}
          unit="HH"
          subtext={availableHH > 0 ? "Safe unreserved households" : "Capacity exhausted"}
          status={availableHH > 0 ? "normal" : "critical"}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
      </div>

      {/* 5-Dimensional Infrastructure Sizing Grid */}
      <div className="space-y-3 rounded-lg border border-border-subtle bg-surface-panel p-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-border-subtle pb-2">
          <h4 className="text-xs font-mono uppercase tracking-wider text-text-muted flex items-center gap-1.5">
            <Boxes className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
            <span>5-Dimensional Infrastructure Capacity &amp; Sizing</span>
          </h4>
          <span className="text-[11px] font-mono text-text-muted">
            Engine Analysis
            <span className="sr-only">M4-03 Engine Analysis</span>
          </span>
        </div>

        {Object.keys(capacity.infrastructure_results).length === 0 ? (
          <p className="text-xs text-text-muted italic p-4 text-center">
            No infrastructure dimension sizing results recorded.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(capacity.infrastructure_results).map(([dimKey, dim]) => {
              const isLimiting = capacity.limiting_factors.includes(dimKey);
              const isAdequate = dim.is_adequate;

              return (
                <div
                  key={dimKey}
                  className={`rounded-lg border p-3.5 flex flex-col justify-between ${
                    isLimiting
                      ? "border-amber-300 dark:border-amber-600/80 bg-amber-50 dark:bg-amber-950/20"
                      : "border-border-subtle bg-surface-elevated"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-1 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-primary-600 dark:text-sky-400">{getDimensionIcon(dimKey)}</span>
                        <span className="font-semibold text-xs text-text-primary">
                          {dim.dimension_name}
                        </span>
                      </div>

                      <Badge
                        variant={isAdequate ? "success" : "danger"}
                        size="sm"
                        className="font-mono text-[10px]"
                      >
                        {isAdequate ? "Adequate" : "Deficit"}
                      </Badge>
                    </div>

                    <div className="space-y-1 my-2 text-xs font-mono">
                      <div className="flex justify-between text-text-muted">
                        <span>Current Capacity:</span>
                        <span className="text-text-primary font-bold">
                          {dim.current_capacity !== null
                            ? `${dim.current_capacity} ${dim.unit}`
                            : "Not Monitored"}
                        </span>
                      </div>

                      <div className="flex justify-between text-text-muted">
                        <span>Required Demand:</span>
                        <span className="text-text-secondary">
                          {dim.required_capacity} {dim.unit}
                        </span>
                      </div>

                      {dim.deficit > 0 && (
                        <div className="flex justify-between text-red-600 dark:text-red-400 font-bold">
                          <span>Capacity Deficit:</span>
                          <span>-{dim.deficit} {dim.unit}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {isLimiting && (
                    <div className="mt-2 pt-2 border-t border-amber-300 dark:border-amber-900/60 text-[11px] text-amber-800 dark:text-amber-300 flex items-center gap-1 font-mono">
                      <AlertTriangle className="h-3 w-3 shrink-0" />
                      <span>Limiting Bottleneck Factor</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Audit Reasons */}
      {capacity.reasons.length > 0 && (
        <div className="rounded-lg border border-border-subtle bg-surface-elevated p-4 space-y-2">
          <h4 className="text-xs font-mono uppercase tracking-wider text-text-muted flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
            <span>Capacity Audit Statements</span>
          </h4>
          <ul className="list-disc list-inside space-y-1 text-xs text-text-secondary">
            {capacity.reasons.map((reason, idx) => (
              <li key={idx} className="leading-relaxed">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
