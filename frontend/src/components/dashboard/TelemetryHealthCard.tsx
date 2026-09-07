"use client";

import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import {
  DataSourceTelemetryRead,
  TelemetryOverviewRead,
} from "@/types/dashboard";

export interface TelemetryHealthCardProps {
  overview?: TelemetryOverviewRead | null;
  sources?: DataSourceTelemetryRead[] | null;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string | null;
}

export const TelemetryHealthCard: React.FC<TelemetryHealthCardProps> = ({
  overview,
  sources,
  isLoading = false,
  isError = false,
  errorMessage,
}) => {
  const total = overview?.total_sources || 0;
  const healthyPct = total > 0 ? Math.round(((overview?.healthy_count || 0) / total) * 100) : 0;
  const degradedPct = total > 0 ? Math.round(((overview?.degraded_count || 0) / total) * 100) : 0;
  const unavailablePct = total > 0 ? Math.round(((overview?.unavailable_count || 0) / total) * 100) : 0;

  const freshPct = total > 0 ? Math.round(((overview?.fresh_count || 0) / total) * 100) : 0;
  const stalePct = total > 0 ? Math.round(((overview?.stale_count || 0) / total) * 100) : 0;
  const unknownPct = total > 0 ? Math.round(((overview?.unknown_count || 0) / total) * 100) : 0;

  return (
    <Card variant="elevated" className="space-y-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Data Sources & Telemetry Health</CardTitle>
            <CardDescription>
              Real-time feed ingestion status, provider health checks, and observational freshness evaluation.
            </CardDescription>
          </div>
          {overview?.synthetic_count ? (
            <Badge variant="outline" size="sm" className="font-mono text-[11px] text-amber-400 border-amber-800/80">
              Synthetic Feeds: {overview.synthetic_count}/{total}
            </Badge>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="py-8 text-center text-slate-400 font-mono text-sm animate-pulse">
            Connecting to telemetry subsystem...
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-900/60 bg-red-950/30 p-4 text-sm text-red-300">
            <div className="font-semibold mb-1">Telemetry Service Unavailable</div>
            <p className="text-xs text-red-400">
              {errorMessage || "Failed to load telemetry health records from backend."}
            </p>
          </div>
        ) : (
          <>
            {/* Visual Health & Freshness Gauges */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Provider Health Distribution */}
              <div className="bg-surface-elevated/70 border border-border-subtle rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold uppercase tracking-wider text-text-muted">
                    Provider Health
                  </span>
                  <span className="font-mono text-text-primary">
                    {overview?.healthy_count ?? 0} Healthy / {overview?.unavailable_count ?? 0} Down
                  </span>
                </div>

                {/* Progress bar */}
                <div className="h-3 w-full bg-border-strong rounded-full overflow-hidden flex" role="progressbar" aria-label="Provider Health Distribution">
                  <div style={{ width: `${healthyPct}%` }} className="bg-emerald-500 h-full" title={`Healthy: ${healthyPct}%`} />
                  <div style={{ width: `${degradedPct}%` }} className="bg-amber-500 h-full" title={`Degraded: ${degradedPct}%`} />
                  <div style={{ width: `${unavailablePct}%` }} className="bg-red-500 h-full" title={`Unavailable: ${unavailablePct}%`} />
                </div>

                <div className="flex items-center justify-between text-[11px] text-text-muted pt-1 font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                    Healthy ({healthyPct}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                    Degraded ({degradedPct}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                    Down ({unavailablePct}%)
                  </span>
                </div>
              </div>

              {/* Data Freshness Distribution */}
              <div className="bg-surface-elevated/70 border border-border-subtle rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold uppercase tracking-wider text-text-muted">
                    Observation Freshness
                  </span>
                  <span className="font-mono text-text-primary">
                    {overview?.fresh_count ?? 0} Fresh / {overview?.stale_count ?? 0} Stale
                  </span>
                </div>

                {/* Progress bar */}
                <div className="h-3 w-full bg-border-strong rounded-full overflow-hidden flex" role="progressbar" aria-label="Data Freshness Distribution">
                  <div style={{ width: `${freshPct}%` }} className="bg-sky-500 h-full" title={`Fresh: ${freshPct}%`} />
                  <div style={{ width: `${stalePct}%` }} className="bg-amber-500 h-full" title={`Stale: ${stalePct}%`} />
                  <div style={{ width: `${unknownPct}%` }} className="bg-slate-400 dark:bg-slate-600 h-full" title={`Unknown: ${unknownPct}%`} />
                </div>

                <div className="flex items-center justify-between text-[11px] text-text-muted pt-1 font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" />
                    Fresh ({freshPct}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                    Stale ({stalePct}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-600 inline-block" />
                    Unknown ({unknownPct}%)
                  </span>
                </div>
              </div>
            </div>

            {/* Data Sources Table */}
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-text-muted">
                Registered Ingestion Feeds
              </h3>

              {!sources || sources.length === 0 ? (
                <div className="py-4 text-center text-text-muted text-xs font-mono">
                  No data sources registered on this platform.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-border-subtle">
                  <table className="w-full text-left text-xs text-text-secondary">
                    <thead className="bg-surface-elevated/80 text-[11px] font-mono text-text-muted uppercase tracking-wider border-b border-border-subtle">
                      <tr>
                        <th className="px-3 py-2.5">Source Name</th>
                        <th className="px-3 py-2.5">Category</th>
                        <th className="px-3 py-2.5">Provider Health</th>
                        <th className="px-3 py-2.5">Freshness Status</th>
                        <th className="px-3 py-2.5">Last Sync</th>
                        <th className="px-3 py-2.5 text-right">Records</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle bg-surface-panel">
                      {sources.map((src) => (
                        <tr key={src.source_id} className="hover:bg-surface-elevated/60 transition-colors">
                          <td className="px-3 py-2 font-medium text-text-primary">
                            {src.name}
                            {src.is_synthetic && (
                              <span className="ml-1.5 text-[10px] font-mono text-amber-700 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1 py-0.2 rounded">
                                DEMO
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-text-muted font-mono text-[11px] capitalize">
                            {src.category || src.source_type}
                          </td>
                          <td className="px-3 py-2">
                            <span className="inline-flex items-center gap-1.5">
                              <StatusIndicator
                                status={
                                  src.provider_health === "HEALTHY"
                                    ? "normal"
                                    : src.provider_health === "DEGRADED"
                                    ? "warning"
                                    : "critical"
                                }
                              />
                              <span className="font-mono text-[11px] text-text-secondary">
                                {src.provider_health}
                              </span>
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase border ${
                                src.freshness?.status === "FRESH"
                                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30"
                                  : src.freshness?.status === "STALE"
                                  ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                                  : "bg-surface-elevated text-text-muted border-border-strong"
                              }`}
                            >
                              {src.freshness?.status || "UNKNOWN"}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-text-muted font-mono text-[11px]">
                            {src.last_successful_update
                              ? new Date(src.last_successful_update).toLocaleTimeString()
                              : "Never"}
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-text-primary">
                            {src.records_ingested_total.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};
