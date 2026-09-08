"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import { useOperational } from "@/context/OperationalContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { TelemetryOverviewRead } from "@/types/dashboard";

export interface DashboardHeaderProps {
  telemetryOverview?: TelemetryOverviewRead | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  lastUpdated?: Date | null;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  telemetryOverview,
  isRefreshing = false,
  onRefresh,
  lastUpdated,
}) => {
  const { user } = useAuth();
  const { activeRegion, dataMode } = useOperational();

  const isAllHealthy =
    telemetryOverview &&
    telemetryOverview.unavailable_count === 0 &&
    telemetryOverview.degraded_count === 0;

  return (
    <div className="border-b border-border-subtle pb-5">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left: Branding & Operational Title */}
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-text-secondary bg-surface-elevated border border-border-subtle px-2.5 py-0.5 rounded-md">
              Operational Posture
            </span>
            <Badge variant="outline" size="sm" className="text-xs text-text-secondary border-border-subtle">
              Region: {activeRegion}
            </Badge>
            <span
              data-testid="data-mode-indicator"
              className={`text-xs font-medium px-2.5 py-0.5 rounded-md border ${
                dataMode === "live"
                  ? "bg-emerald-100 border-emerald-300 text-emerald-800 dark:bg-emerald-950/80 dark:border-emerald-700 dark:text-emerald-300"
                  : "bg-amber-100 border-amber-300 text-amber-800 dark:bg-amber-950/80 dark:border-amber-700 dark:text-amber-300"
              }`}
            >
              {dataMode === "live" ? (
                "LIVE (Telemetry)"
              ) : (
                <>
                  Simulation Baseline
                  <span className="sr-only"> DEMO (Synthetic)</span>
                </>
              )}
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-text-primary">
            Executive Command Dashboard
          </h1>

          <p className="text-xs sm:text-sm text-text-muted max-w-3xl leading-relaxed">
            Multi-hazard disaster overview, candidate relocation safe havens, scenario contingencies,
            and data feed telemetry.
          </p>
        </div>

        {/* Right: Officer Context & Refresh Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* System Health Pill */}
          <div className="flex items-center gap-2 bg-surface-elevated border border-border-subtle rounded-md px-3 py-1.5 text-xs">
            <StatusIndicator
              status={isAllHealthy ? "normal" : telemetryOverview?.unavailable_count ? "critical" : "warning"}
              showPulse={Boolean(telemetryOverview?.unavailable_count)}
            />
            <span className="font-medium text-text-secondary">
              {telemetryOverview
                ? `${telemetryOverview.healthy_count}/${telemetryOverview.total_sources} Feeds Healthy`
                : "Checking Telemetry..."}
            </span>
          </div>

          {/* User profile capsule if logged in */}
          {user && (
            <div className="hidden sm:flex items-center gap-2 bg-surface-elevated border border-border-subtle rounded-md px-3 py-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-600 dark:bg-emerald-400" />
              <span className="text-text-primary font-medium">{user.full_name}</span>
              <span className="text-text-muted text-xs">
                ({user.role.replace("_", " ")})
              </span>
            </div>
          )}

          {/* Refresh Action */}
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              isLoading={isRefreshing}
              className="text-xs"
              title={lastUpdated ? `Last updated: ${lastUpdated.toLocaleTimeString()}` : "Refresh metrics"}
            >
              <svg
                className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin" : ""}`}
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
