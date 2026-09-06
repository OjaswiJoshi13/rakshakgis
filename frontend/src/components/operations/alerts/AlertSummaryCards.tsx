"use client";

import React from "react";
import { MetricCard } from "@/components/ui/MetricCard";
import { AlertSummaryMetrics } from "@/types/alerts";
import { ShieldAlert, AlertTriangle, Clock, HelpCircle } from "lucide-react";

export interface AlertSummaryCardsProps {
  metrics: AlertSummaryMetrics;
  isLoading?: boolean;
}

export const AlertSummaryCards: React.FC<AlertSummaryCardsProps> = ({
  metrics,
  isLoading = false,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        label="Total Monitored Feeds"
        value={isLoading ? "..." : metrics.total_alerts}
        subtext="Active telemetry streams"
        status="normal"
        icon={<ShieldAlert className="h-5 w-5 text-sky-400" />}
      />

      <MetricCard
        label="Triggered Threshold Breaches"
        value={isLoading ? "..." : metrics.triggered_count}
        subtext="Dynamic candidates requiring review"
        status={metrics.triggered_count > 0 ? "critical" : "normal"}
        icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
      />

      <MetricCard
        label="Pending Acknowledgment"
        value={isLoading ? "..." : metrics.pending_acknowledgment}
        subtext="Awaiting duty officer sign-off"
        status={metrics.pending_acknowledgment > 0 ? "warning" : "normal"}
        icon={<Clock className="h-5 w-5 text-amber-400" />}
      />

      <MetricCard
        label="Sensor Telemetry Gaps"
        value={isLoading ? "..." : metrics.insufficient_data_count}
        subtext="INSUFFICIENT_DATA safety status"
        status={metrics.insufficient_data_count > 0 ? "info" : "normal"}
        icon={<HelpCircle className="h-5 w-5 text-sky-400" />}
      />
    </div>
  );
};
