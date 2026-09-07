"use client";

import React from "react";
import { MetricCard } from "@/components/ui/MetricCard";
import {
  CandidateSiteRead,
  RelocationAssignmentRead,
  ScenarioDefinitionRead,
  TelemetryOverviewRead,
} from "@/types/dashboard";
import { PaginatedResponse } from "@/types/api";

export interface DashboardKpiStripProps {
  sitesData?: PaginatedResponse<CandidateSiteRead> | null;
  sitesLoading?: boolean;
  sitesError?: boolean;

  assignmentsData?: PaginatedResponse<RelocationAssignmentRead> | null;
  assignmentsLoading?: boolean;
  assignmentsError?: boolean;

  telemetryOverview?: TelemetryOverviewRead | null;
  telemetryLoading?: boolean;
  telemetryError?: boolean;

  scenariosData?: ScenarioDefinitionRead[] | null;
  scenariosLoading?: boolean;
  scenariosError?: boolean;
}

export const DashboardKpiStrip: React.FC<DashboardKpiStripProps> = ({
  sitesData,
  sitesLoading = false,
  sitesError = false,

  assignmentsData,
  assignmentsLoading = false,
  assignmentsError = false,

  telemetryOverview,
  telemetryLoading = false,
  telemetryError = false,

  scenariosData,
  scenariosLoading = false,
  scenariosError = false,
}) => {
  const sitesTotal = sitesLoading
    ? "..."
    : sitesError
    ? "Unavailable"
    : String(sitesData?.pagination?.total ?? (sitesData?.data ? sitesData.data.length : 0));

  const assignmentsTotal = assignmentsLoading
    ? "..."
    : assignmentsError
    ? "Unavailable"
    : String(
        assignmentsData?.pagination?.total ??
          (assignmentsData?.data ? assignmentsData.data.length : 0)
      );

  const feedsTotal = telemetryLoading
    ? "..."
    : telemetryError
    ? "Unavailable"
    : String(telemetryOverview?.total_sources ?? 0);

  const freshRatio = telemetryLoading
    ? "..."
    : telemetryError
    ? "Unavailable"
    : telemetryOverview
    ? `${telemetryOverview.fresh_count}/${telemetryOverview.total_sources}`
    : "0/0";

  const scenariosTotal = scenariosLoading
    ? "..."
    : scenariosError
    ? "Unavailable"
    : String(scenariosData?.length ?? 0);

  return (
    <section aria-labelledby="executive-kpi-heading" className="space-y-3">
      <h2
        id="executive-kpi-heading"
        className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400"
      >
        Executive Operational KPIs
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* 1. Candidate Relocation Sites */}
        <MetricCard
          label="Candidate Safe Sites"
          value={sitesTotal}
          unit={sitesError || sitesLoading ? undefined : "Sites"}
          subtext={sitesError ? "API Error" : "Verified Relocation Havens"}
          status={sitesError ? "warning" : "normal"}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />

        {/* 2. Relocation Assignments */}
        <MetricCard
          label="Planned Relocations"
          value={assignmentsTotal}
          unit={assignmentsError || assignmentsLoading ? undefined : "Moves"}
          subtext={assignmentsError ? "API Error" : "Matched Settlements"}
          status={assignmentsError ? "warning" : "info"}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />

        {/* 3. Telemetry Feeds */}
        <MetricCard
          label="Telemetry Feeds"
          value={feedsTotal}
          unit={telemetryError || telemetryLoading ? undefined : "Active"}
          subtext={
            telemetryError
              ? "Service Degraded"
              : telemetryOverview
              ? `${telemetryOverview.healthy_count} Healthy / ${telemetryOverview.degraded_count} Degraded`
              : "Connecting..."
          }
          status={
            telemetryError || (telemetryOverview && telemetryOverview.unavailable_count > 0)
              ? "critical"
              : telemetryOverview && telemetryOverview.degraded_count > 0
              ? "warning"
              : "normal"
          }
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />

        {/* 4. Freshness Ratio */}
        <MetricCard
          label="Data Freshness"
          value={freshRatio}
          unit={telemetryError || telemetryLoading ? undefined : "Fresh"}
          subtext={
            telemetryError
              ? "Telemetry Sync Offline"
              : telemetryOverview
              ? `${telemetryOverview.stale_count} Stale / ${telemetryOverview.unknown_count} Unknown`
              : "Evaluating age..."
          }
          status={
            telemetryError || (telemetryOverview && telemetryOverview.stale_count > 0)
              ? "warning"
              : "normal"
          }
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        {/* 5. What-If Scenarios */}
        <MetricCard
          label="Scenario Models"
          value={scenariosTotal}
          unit={scenariosError || scenariosLoading ? undefined : "Pipelines"}
          subtext={scenariosError ? "API Error" : "Rainfall, Flood, Capacity"}
          status={scenariosError ? "warning" : "normal"}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />

        {/* 6. Habitations Monitored */}
        <MetricCard
          label="Habitations Layer"
          value="Monitored"
          subtext="Active Regional Feed"
          status="normal"
          icon={
            <>
              <span className="sr-only">M5-06</span>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
              </svg>
            </>
          }
        />
      </div>
    </section>
  );
};
