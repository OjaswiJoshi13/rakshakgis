"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  History,
  Radio,
  RefreshCw,
  Server,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DataSourceTelemetryRead, FreshnessStatus, ProviderHealth } from "@/types/telemetry";

export interface SourceTableProps {
  sources: DataSourceTelemetryRead[];
  onSelectSource: (source: DataSourceTelemetryRead) => void;
  onProbeSource: (source: DataSourceTelemetryRead) => void;
  probingSourceId: number | null;
  isLoading?: boolean;
}

export const SourceTable: React.FC<SourceTableProps> = ({
  sources,
  onSelectSource,
  onProbeSource,
  probingSourceId,
  isLoading,
}) => {
  const getHealthBadge = (health: ProviderHealth | string) => {
    switch (health.toLowerCase()) {
      case "healthy":
        return (
          <Badge variant="success" size="sm" className="font-mono gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
            <span>HEALTHY</span>
          </Badge>
        );
      case "degraded":
        return (
          <Badge variant="warning" size="sm" className="font-mono gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 inline-block" />
            <span>DEGRADED</span>
          </Badge>
        );
      case "unavailable":
        return (
          <Badge variant="danger" size="sm" className="font-mono gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-red-400 inline-block" />
            <span>OFFLINE</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="font-mono text-slate-400 border-slate-700">
            <span>UNKNOWN</span>
          </Badge>
        );
    }
  };

  const getFreshnessBadge = (status: FreshnessStatus | string, isUsable: boolean) => {
    switch (status.toLowerCase()) {
      case "fresh":
        return (
          <Badge variant="success" size="sm" className="font-mono">
            FRESH
          </Badge>
        );
      case "stale":
        return (
          <Badge variant="warning" size="sm" className="font-mono">
            STALE
          </Badge>
        );
      case "clock_skew":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-purple-300 border-purple-600/60 bg-purple-950/40">
            CLOCK SKEW
          </Badge>
        );
      case "unavailable":
        return (
          <Badge variant="danger" size="sm" className="font-mono">
            UNAVAILABLE
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="font-mono text-slate-400 border-slate-700">
            UNKNOWN
          </Badge>
        );
    }
  };

  const formatAgeAndCutoff = (ageSeconds: number | null, thresholdSeconds: number) => {
    if (ageSeconds === null) return "No timestamp";
    const formatDur = (s: number) => {
      if (s < 60) return `${Math.round(s)}s`;
      if (s < 3600) return `${Math.round(s / 60)}m`;
      if (s < 86400) return `${(s / 3600).toFixed(1)}h`;
      return `${(s / 86400).toFixed(1)}d`;
    };
    return `${formatDur(ageSeconds)} old / ${formatDur(thresholdSeconds)} max`;
  };

  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-8 text-center">
        <RefreshCw className="h-6 w-6 text-sky-400 animate-spin mx-auto mb-2" />
        <p className="text-xs text-slate-400 font-mono">Loading telemetry and freshness diagnostics...</p>
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-12 text-center">
        <Server className="h-8 w-8 text-slate-600 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-300">No Data Sources Match Filter Criteria</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          No registered telemetry feeds or provider adapters match your active search or category filters.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 font-mono border-b border-slate-800 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="py-3 px-4">Data Source & Provider</th>
              <th className="py-3 px-3">Category</th>
              <th className="py-3 px-3">Provider Health</th>
              <th className="py-3 px-3">Temporal Freshness</th>
              <th className="py-3 px-3">Ingestion Totals</th>
              <th className="py-3 px-3">Mode & Provenance</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {sources.map((source) => {
              const isProbing = probingSourceId === source.source_id;

              return (
                <tr
                  key={source.source_id}
                  className="hover:bg-slate-800/30 transition-colors group"
                >
                  {/* Source Name & ID */}
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-200 group-hover:text-sky-300 transition-colors">
                      {source.name}
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono mt-0.5">
                      <span>ID: #{source.source_id}</span>
                      <span>•</span>
                      <span className="text-slate-500">{source.provider_id || source.provider}</span>
                    </div>
                  </td>

                  {/* Category */}
                  <td className="py-3 px-3">
                    <Badge variant="outline" size="sm" className="capitalize font-mono text-[11px] text-slate-300 border-slate-700">
                      {source.category?.replace("_", " ") || "Other"}
                    </Badge>
                  </td>

                  {/* Health */}
                  <td className="py-3 px-3">
                    {getHealthBadge(source.provider_health)}
                  </td>

                  {/* Freshness */}
                  <td className="py-3 px-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5">
                        {getFreshnessBadge(source.freshness.status, source.freshness.is_usable)}
                        {!source.freshness.is_usable && (
                          <span className="text-[10px] font-mono text-amber-400">
                            (Unusable)
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] font-mono text-slate-400">
                        {formatAgeAndCutoff(source.freshness.age_seconds, source.freshness.threshold_seconds)}
                      </div>
                    </div>
                  </td>

                  {/* Ingestion Totals */}
                  <td className="py-3 px-3 font-mono text-[11px]">
                    <div className="text-emerald-400">
                      {source.records_ingested_total.toLocaleString()} synced
                    </div>
                    {source.records_failed_total > 0 ? (
                      <div className="text-red-400 text-[10px]">
                        {source.records_failed_total} failed
                      </div>
                    ) : (
                      <div className="text-slate-500 text-[10px]">0 failed</div>
                    )}
                  </td>

                  {/* Mode & Provenance */}
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Badge variant="outline" size="sm" className="font-mono text-[10px] uppercase text-sky-400 border-sky-800">
                        {source.provider_mode}
                      </Badge>
                      {source.is_synthetic && (
                        <Badge variant="outline" size="sm" className="font-mono text-[10px] text-purple-400 border-purple-800 bg-purple-950/30">
                          SYNTHETIC
                        </Badge>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => onSelectSource(source)}
                        leftIcon={<History className="h-3 w-3" />}
                        className="text-xs"
                      >
                        <span>History</span>
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onProbeSource(source)}
                        isLoading={isProbing}
                        leftIcon={<Radio className="h-3 w-3" />}
                        className="text-xs text-sky-400 border-sky-700/60 hover:bg-sky-950/40"
                      >
                        <span>Probe</span>
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
