"use client";

import React, { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import {
  AlertSummaryCards,
  AlertFilterBar,
  AlertCard,
  AlertDetailModal,
  ThresholdConfigCard,
} from "@/components/operations/alerts";
import {
  listAlerts,
  getThresholdConfig,
  getAlertSummaryMetrics,
  acknowledgeAlert,
  acknowledgeAllAlerts,
} from "@/lib/api/alerts";
import {
  AlertFilterCriteria,
  AlertSummaryMetrics,
  DynamicThresholdSummary,
  OperationalAlertItem,
} from "@/types/alerts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { ShieldCheck, RefreshCw, CheckCircle2, Inbox } from "lucide-react";

function AlertsOperationsContent() {
  const searchParams = useSearchParams();

  // State management
  const [alerts, setAlerts] = useState<OperationalAlertItem[]>([]);
  const [metrics, setMetrics] = useState<AlertSummaryMetrics>({
    total_alerts: 0,
    triggered_count: 0,
    pending_acknowledgment: 0,
    insufficient_data_count: 0,
    critical_extreme_count: 0,
  });
  const [thresholds, setThresholds] = useState<DynamicThresholdSummary | null>(null);

  const [filters, setFilters] = useState<AlertFilterCriteria>({
    severity: (searchParams.get("severity") as any) || "all",
    status: (searchParams.get("status") as any) || "all",
    indicator: (searchParams.get("indicator") as any) || "all",
    is_acknowledged:
      searchParams.get("acknowledged") === "true"
        ? true
        : searchParams.get("acknowledged") === "false"
        ? false
        : "all",
    search: searchParams.get("q") || "",
  });

  const [selectedAlert, setSelectedAlert] = useState<OperationalAlertItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAcknowledging, setIsAcknowledging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const targetAlertId = searchParams.get("id");

  // Load telemetry feeds and summary metrics
  const loadAlertsData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [alertsResp, metricsResp, thresholdsResp] = await Promise.all([
        listAlerts(filters),
        getAlertSummaryMetrics(),
        getThresholdConfig("himalayan_pilot"),
      ]);

      if (alertsResp.success && alertsResp.data) {
        setAlerts(alertsResp.data);
        if (targetAlertId) {
          const found = alertsResp.data.find((a) => a.id === targetAlertId);
          if (found) {
            setSelectedAlert(found);
            setIsModalOpen(true);
          }
        }
      }
      if (metricsResp.success && metricsResp.data) {
        setMetrics(metricsResp.data);
      }
      if (thresholdsResp.success && thresholdsResp.data) {
        setThresholds(thresholdsResp.data);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load real-time alerts telemetry.");
    } finally {
      setIsLoading(false);
    }
  }, [filters, targetAlertId]);

  useEffect(() => {
    loadAlertsData();
  }, [loadAlertsData]);

  // Acknowledge single alert
  const handleAcknowledgeSingle = async (alertId: string) => {
    setIsAcknowledging(true);
    try {
      const resp = await acknowledgeAlert(alertId, "District Magistrate (Duty Officer)");
      if (resp.success && resp.data) {
        setAlerts((prev) =>
          prev.map((a) => (a.id === alertId ? resp.data : a))
        );
        setSuccessNotice(`Alert ${alertId} has been successfully acknowledged.`);
        // Refresh metrics
        const metResp = await getAlertSummaryMetrics();
        if (metResp.success && metResp.data) {
          setMetrics(metResp.data);
        }
      }
    } catch (err: any) {
      setError(err?.message || `Failed to acknowledge alert ${alertId}.`);
    } finally {
      setIsAcknowledging(false);
    }
  };

  // Bulk acknowledge all unread alerts
  const handleAcknowledgeAll = async () => {
    setIsAcknowledging(true);
    try {
      const resp = await acknowledgeAllAlerts("District Magistrate (Duty Officer)");
      if (resp.success && resp.data) {
        const count = resp.data.acknowledged_count;
        setSuccessNotice(
          `Successfully acknowledged ${count} unread alert${count === 1 ? "" : "s"}.`
        );
        // Refresh list and metrics
        await loadAlertsData();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to execute bulk acknowledgment.");
    } finally {
      setIsAcknowledging(false);
    }
  };

  const handleInspectAlert = (alert: OperationalAlertItem) => {
    setSelectedAlert(alert);
    setIsModalOpen(true);
  };

  const pendingCount = useMemo(() => {
    return alerts.filter((a) => !a.is_acknowledged).length;
  }, [alerts]);

  return (
    <OperationsSectionShell
      title="Real-Time Alerts & Warnings"
      description="Real-time multi-hazard telemetry alerts, dynamic Red Zone threshold breach notifications, and early warning dispatch interfaces."
      chunkId="M6-05"
      chunkTitle="Real-Time Alerts & Threshold Warnings UI"
      prerequisiteChunk="Chunk M3-11 (Dynamic Red Zone Engine — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={loadAlertsData}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            <span>Refresh Telemetry</span>
          </Button>

          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={handleAcknowledgeAll}
            disabled={isAcknowledging || pendingCount === 0}
            leftIcon={<ShieldCheck className="h-3.5 w-3.5" />}
          >
            <span>Acknowledge All ({pendingCount})</span>
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Success Notice */}
        {successNotice && (
          <Alert
            severity="success"
            title="Operational Acknowledgment Logged"
            onClose={() => setSuccessNotice(null)}
          >
            {successNotice}
          </Alert>
        )}

        {/* Error Notice */}
        {error && (
          <Alert severity="danger" title="Telemetry Ingestion Error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Summary KPI Cards */}
        <AlertSummaryCards metrics={metrics} isLoading={isLoading} />

        {/* Authoritative Dynamic Threshold Configuration Panel */}
        {thresholds && <ThresholdConfigCard thresholds={thresholds} />}

        {/* Filter & Search Controls */}
        <AlertFilterBar
          filters={filters}
          onFilterChange={setFilters}
          totalFiltered={alerts.length}
          totalAll={metrics.total_alerts}
        />

        {/* Alert Cards Feed */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 animate-pulse bg-slate-900/40 border-slate-800">
                <div className="h-4 bg-slate-800 rounded w-1/4 mb-3" />
                <div className="h-4 bg-slate-800 rounded w-3/4 mb-2" />
                <div className="h-3 bg-slate-800/60 rounded w-1/2" />
              </Card>
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-border-base bg-surface-raised">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-surface-base border border-border-base text-text-muted mb-3">
              <Inbox className="h-6 w-6" />
            </div>
            <h4 className="text-base font-semibold text-text-primary">
              No Alerts Match Current Filter Criteria
            </h4>
            <p className="text-xs sm:text-sm text-text-secondary max-w-md mx-auto mt-1">
              Adjust your filter criteria or reset the search query to view all regional telemetry feeds.
            </p>
            <div className="mt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  setFilters({
                    severity: "all",
                    status: "all",
                    indicator: "all",
                    is_acknowledged: "all",
                    search: "",
                  })
                }
              >
                Reset Filter Criteria
              </Button>
            </div>
          </Card>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={handleAcknowledgeSingle}
                onInspect={handleInspectAlert}
                isAcknowledging={isAcknowledging}
              />
            ))}
          </div>
        )}

        {/* Audit Detail Modal */}
        <AlertDetailModal
          alert={selectedAlert}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onAcknowledge={handleAcknowledgeSingle}
          isAcknowledging={isAcknowledging}
        />
      </div>
    </OperationsSectionShell>
  );
}

export default function AlertsOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-slate-400 font-mono text-sm">
          Loading Real-Time Alerts & Threshold Warnings Console...
        </div>
      }
    >
      <AlertsOperationsContent />
    </Suspense>
  );
}
