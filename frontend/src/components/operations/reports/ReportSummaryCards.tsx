"use client";

import React from "react";
import { ReportMetric } from "@/types/reports";
import { MetricCard } from "@/components/ui/MetricCard";
import {
  Users,
  Building2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldAlert,
} from "lucide-react";

interface ReportSummaryCardsProps {
  metrics: ReportMetric[];
}

export const ReportSummaryCards: React.FC<ReportSummaryCardsProps> = ({
  metrics,
}) => {
  if (!metrics || metrics.length === 0) return null;

  const getMetricIcon = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes("habitation") || l.includes("village") || l.includes("household") || l.includes("demand")) {
      return <Users className="h-4 w-4 text-sky-400" />;
    }
    if (l.includes("site") || l.includes("capacity")) {
      return <Building2 className="h-4 w-4 text-emerald-400" />;
    }
    if (l.includes("decision") || l.includes("assigned") || l.includes("passed")) {
      return <CheckCircle2 className="h-4 w-4 text-sky-400" />;
    }
    if (l.includes("limiting") || l.includes("deficit") || l.includes("unassigned")) {
      return <AlertTriangle className="h-4 w-4 text-amber-400" />;
    }
    return <FileText className="h-4 w-4 text-slate-400" />;
  };

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, idx) => (
        <MetricCard
          key={`${metric.label}-${idx}`}
          label={metric.label}
          value={metric.value}
          subtext={metric.subtext}
          icon={getMetricIcon(metric.label)}
        />
      ))}
    </div>
  );
};
