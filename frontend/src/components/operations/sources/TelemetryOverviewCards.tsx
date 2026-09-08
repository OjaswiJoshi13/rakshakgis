"use client";

import React from "react";
import { Database, Activity, Clock, ShieldCheck } from "lucide-react";
import { MetricCard } from "@/components/ui/MetricCard";
import { TelemetryOverviewRead } from "@/types/telemetry";

export interface TelemetryOverviewCardsProps {
  overview: TelemetryOverviewRead | null;
  isLoading?: boolean;
}

export const TelemetryOverviewCards: React.FC<TelemetryOverviewCardsProps> = ({
  overview,
  isLoading,
}) => {
  if (isLoading || !overview) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-28 rounded-lg bg-surface-panel border border-border-subtle animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Registered Feeds */}
      <MetricCard
        label="Registered Data Feeds"
        value={overview.total_sources}
        subtext="Active telemetry streams"
        status="info"
        icon={<Database className="h-4 w-4 text-sky-600 dark:text-sky-400" />}
      />

      {/* 2. Provider Health */}
      <MetricCard
        label="Adapter Health"
        value={`${overview.healthy_count}/${overview.total_sources}`}
        subtext={`${overview.degraded_count} degraded • ${overview.unavailable_count} offline`}
        status={overview.unavailable_count > 0 ? "critical" : overview.degraded_count > 0 ? "warning" : "normal"}
        icon={<Activity className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />}
      />

      {/* 3. Freshness Classification */}
      <MetricCard
        label="Freshness Status"
        value={`${overview.fresh_count} Fresh`}
        subtext={`${overview.stale_count} stale • ${overview.unknown_count} unknown`}
        status={overview.stale_count > 0 ? "warning" : "normal"}
        icon={<Clock className="h-4 w-4 text-amber-600 dark:text-amber-400" />}
      />

      {/* 4. Synthetic / Demo Provenance */}
      <MetricCard
        label={<>Source Provenance <span className="sr-only">Demo Provenance</span></>}
        value={`${overview.synthetic_count} Synthetic`}
        subtext="Rule 8 synthetic disclaimer"
        status="normal"
        icon={<ShieldCheck className="h-4 w-4 text-purple-600 dark:text-purple-400" />}
      />
    </div>
  );
};
