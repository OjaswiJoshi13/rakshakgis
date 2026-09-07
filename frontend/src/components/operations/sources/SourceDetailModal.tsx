"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  ExternalLink,
  History,
  Radio,
  RefreshCw,
  Server,
  ShieldAlert,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import {
  DataIngestionRunRead,
  DataSourceDetailRead,
  DataSourceTelemetryRead,
} from "@/types/telemetry";
import { getDataSourceDetail, listDataSourceRuns } from "@/lib/api/telemetry";

export interface SourceDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  source: DataSourceTelemetryRead | null;
  onProbeSource: (source: DataSourceTelemetryRead) => Promise<void>;
  isProbing?: boolean;
}

export const SourceDetailModal: React.FC<SourceDetailModalProps> = ({
  isOpen,
  onClose,
  source,
  onProbeSource,
  isProbing = false,
}) => {
  const [detail, setDetail] = useState<DataSourceDetailRead | null>(null);
  const [runs, setRuns] = useState<DataIngestionRunRead[]>([]);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  useEffect(() => {
    if (!isOpen || !source) return;

    let isMounted = true;
    setIsLoadingDetail(true);

    const loadData = async () => {
      try {
        const detailData = await getDataSourceDetail(source.source_id);
        if (isMounted) {
          setDetail(detailData);
          setRuns(detailData.recent_runs || []);
        }
      } catch (err) {
        // Fallback to source object
      } finally {
        if (isMounted) setIsLoadingDetail(false);
      }
    };

    loadData();

    return () => {
      isMounted = false;
    };
  }, [isOpen, source]);

  if (!isOpen || !source) return null;

  const activeSource = detail || source;
  const freshness = activeSource.freshness;

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "success":
        return (
          <Badge variant="success" size="sm" className="font-mono text-[10px] uppercase">
            SUCCESS
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="danger" size="sm" className="font-mono text-[10px] uppercase">
            FAILED
          </Badge>
        );
      case "running":
        return (
          <Badge variant="info" size="sm" className="font-mono text-[10px] uppercase">
            RUNNING
          </Badge>
        );
      case "partial":
        return (
          <Badge variant="warning" size="sm" className="font-mono text-[10px] uppercase">
            PARTIAL
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="font-mono text-[10px] uppercase">
            {status}
          </Badge>
        );
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="source-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs overflow-y-auto"
    >
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-xl border border-border-subtle bg-surface-panel shadow-2xl overflow-hidden my-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border-subtle p-5 bg-surface-elevated/40">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-sky-600 dark:text-sky-400 font-semibold">
                Source #{activeSource.source_id}
              </span>
              <span className="text-text-muted">•</span>
              <Badge variant="outline" size="sm" className="capitalize font-mono text-text-secondary border-border-subtle">
                {activeSource.category?.replace("_", " ") || "Other"}
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono text-[10px] uppercase text-sky-700 dark:text-sky-400 border-sky-400/40">
                {activeSource.provider_mode}
              </Badge>
              {activeSource.is_synthetic && (
                <Badge variant="outline" size="sm" className="font-mono text-[10px] text-purple-700 dark:text-purple-400 border-purple-400/40 bg-purple-50 dark:bg-purple-950/40">
                  SYNTHETIC
                </Badge>
              )}
            </div>
            <h2
              id="source-modal-title"
              className="text-lg sm:text-xl font-bold text-text-primary"
            >
              {activeSource.name}
            </h2>
            <div className="text-xs text-text-muted font-mono">
              Provider: <span className="text-text-secondary font-medium">{activeSource.provider}</span> ({activeSource.provider_id})
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-lg p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-5 overflow-y-auto flex-1">
          {/* 1. Freshness Diagnostics Block */}
          <div className="rounded-lg border border-border-subtle bg-surface-elevated/30 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-sky-600 dark:text-sky-400" />
                <h3 className="text-sm font-semibold text-text-primary">
                  Deterministic Freshness Evaluation
                </h3>
              </div>
              <Badge
                variant={freshness.status === "fresh" ? "success" : freshness.status === "stale" ? "warning" : "danger"}
                size="sm"
                className="font-mono uppercase tracking-wide"
              >
                {freshness.status.toUpperCase()}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="rounded border border-border-subtle bg-surface-panel p-2.5 space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Observed Age</span>
                <span className="text-text-primary font-bold">
                  {freshness.age_seconds !== null ? `${Math.round(freshness.age_seconds)}s (${(freshness.age_seconds / 60).toFixed(1)}m)` : "No timestamp"}
                </span>
              </div>
              <div className="rounded border border-border-subtle bg-surface-panel p-2.5 space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Category Cutoff</span>
                <span className="text-text-primary font-bold">
                  {freshness.threshold_seconds}s ({(freshness.threshold_seconds / 3600).toFixed(1)}h)
                </span>
              </div>
              <div className="rounded border border-border-subtle bg-surface-panel p-2.5 space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Usable for Decision Support</span>
                <span className={freshness.is_usable ? "text-emerald-700 dark:text-emerald-400 font-bold" : "text-amber-700 dark:text-amber-400 font-bold"}>
                  {freshness.is_usable ? "YES (USABLE)" : "NO (STALE / INSUFFICIENT)"}
                </span>
              </div>
            </div>

            <div className="text-xs text-text-secondary font-mono bg-surface-panel p-2.5 rounded border border-border-subtle">
              <span className="text-text-muted">Evaluation Reason: </span>
              {freshness.reason}
            </div>
          </div>

          {/* 2. Source Configuration & Endpoint Metadata */}
          <div className="rounded-lg border border-border-subtle bg-surface-elevated/30 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Server className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              Adapter Configuration & Telemetry Parameters
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2 rounded bg-surface-panel border border-border-subtle space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Polling Cadence</span>
                <span className="text-text-primary">
                  {activeSource.polling_interval_seconds ? `${activeSource.polling_interval_seconds}s` : "Event-driven"}
                </span>
              </div>
              <div className="p-2 rounded bg-surface-panel border border-border-subtle space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Region Identifier</span>
                <span className="text-text-primary">{activeSource.region_id || "All Regions"}</span>
              </div>
              <div className="p-2 rounded bg-surface-panel border border-border-subtle space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Records Ingested</span>
                <span className="text-emerald-700 dark:text-emerald-400 font-bold">
                  {activeSource.records_ingested_total.toLocaleString()}
                </span>
              </div>
              <div className="p-2 rounded bg-surface-panel border border-border-subtle space-y-1">
                <span className="text-[10px] text-text-muted uppercase block">Records Failed</span>
                <span className={activeSource.records_failed_total > 0 ? "text-red-700 dark:text-red-400 font-bold" : "text-text-muted"}>
                  {activeSource.records_failed_total.toLocaleString()}
                </span>
              </div>
            </div>

            {activeSource.endpoint_url && (
              <div className="text-xs font-mono bg-surface-panel p-2 rounded border border-border-subtle flex items-center justify-between gap-2 overflow-hidden">
                <span className="text-text-muted shrink-0">Endpoint URL:</span>
                <span className="text-sky-700 dark:text-sky-300 truncate">{activeSource.endpoint_url}</span>
              </div>
            )}
          </div>

          {/* 3. Ingestion Runs History Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <History className="h-4 w-4 text-sky-600 dark:text-sky-400" />
                Recent Ingestion Execution Runs
              </h3>
              <span className="text-xs text-text-muted font-mono">
                {runs.length} recent executions
              </span>
            </div>

            {runs.length === 0 ? (
              <div className="rounded border border-border-subtle p-6 text-center text-xs text-text-muted font-mono">
                No ingestion runs recorded for this data source yet.
              </div>
            ) : (
              <div className="rounded-lg border border-border-subtle bg-surface-panel overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface-elevated text-text-secondary font-mono border-b border-border-subtle uppercase text-[10px]">
                    <tr>
                      <th className="py-2.5 px-3">Run ID</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Ingested / Failed</th>
                      <th className="py-2.5 px-3">Execution Time</th>
                      <th className="py-2.5 px-3">Diagnostic Log</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle font-mono text-[11px]">
                    {runs.map((run) => (
                      <tr key={run.id} className="hover:bg-surface-elevated/50 transition-colors">
                        <td className="py-2.5 px-3 text-text-primary font-medium">#{run.id}</td>
                        <td className="py-2.5 px-3">{getStatusBadge(run.status)}</td>
                        <td className="py-2.5 px-3">
                          <span className="text-emerald-700 dark:text-emerald-400 font-semibold">{run.records_ingested}</span>
                          {" / "}
                          <span className={run.records_failed > 0 ? "text-red-700 dark:text-red-400 font-semibold" : "text-text-muted"}>
                            {run.records_failed}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-text-secondary text-[10px]">
                          {run.started_at ? new Date(run.started_at).toLocaleTimeString() : "—"}
                        </td>
                        <td className="py-2.5 px-3 text-text-muted max-w-xs truncate text-[10px]">
                          {run.log_details || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 4. Statutory Rule 8 & Rule 12 Advisory */}
          <Alert severity="info" title="Statutory Governance & Provenance Disclosure">
            Data source telemetry and provider health diagnostics strictly reflect M3-13 evaluation invariants.
            All demo adapters operate under Rule 8 with synthetic provenance. Downstream hazard assessments require
            operational verification under Rule 12.
          </Alert>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-border-subtle p-4 bg-surface-elevated/40">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onProbeSource(activeSource)}
            isLoading={isProbing}
            leftIcon={<Radio className="h-3.5 w-3.5" />}
            className="text-xs text-sky-700 dark:text-sky-300 border-sky-400/40 hover:bg-sky-50 dark:hover:bg-sky-950/40"
          >
            <span>Trigger Health Probe</span>
          </Button>

          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onClose}
            className="text-xs"
          >
            <span>Close</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
