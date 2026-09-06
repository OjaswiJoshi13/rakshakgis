"use client";

import React, { useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { apiClient, useApiQuery } from "@/lib/api";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
import {
  CandidateSiteRead,
  DataSourceTelemetryRead,
  RelocationAssignmentRead,
  ScenarioDefinitionRead,
  TelemetryOverviewRead,
} from "@/types/dashboard";
import {
  DashboardHeader,
  DashboardKpiStrip,
  TelemetryHealthCard,
  CandidateSitesTable,
  RelocationAssignmentsCard,
  ScenarioReadinessCard,
  AlertsNoticeCard,
} from "@/components/dashboard";

export default function ExecutiveDashboardPage() {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // 1. Platform Telemetry Overview
  const {
    data: overviewEnvelope,
    isLoading: overviewLoading,
    isError: overviewError,
    error: overviewErrObj,
    refetch: refetchOverview,
  } = useApiQuery<ResponseEnvelope<TelemetryOverviewRead>>(
    "dashboard-telemetry-overview",
    (signal) => apiClient.get("/telemetry/overview", { signal }),
    { cacheTtlMs: 30000 }
  );

  // 2. Telemetry Ingestion Sources
  const {
    data: sourcesData,
    isLoading: sourcesLoading,
    isError: sourcesError,
    error: sourcesErrObj,
    refetch: refetchSources,
  } = useApiQuery<PaginatedResponse<DataSourceTelemetryRead>>(
    "dashboard-telemetry-sources",
    (signal) =>
      apiClient.get("/telemetry/sources", {
        params: { page: 1, page_size: 10 },
        signal,
      }),
    { cacheTtlMs: 30000 }
  );

  // 3. Candidate Relocation Sites
  const {
    data: sitesData,
    isLoading: sitesLoading,
    isError: sitesError,
    error: sitesErrObj,
    refetch: refetchSites,
  } = useApiQuery<PaginatedResponse<CandidateSiteRead>>(
    "dashboard-candidate-sites",
    (signal) =>
      apiClient.get("/sites", {
        params: { page: 1, page_size: 10 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 4. Relocation Assignments
  const {
    data: assignmentsData,
    isLoading: assignmentsLoading,
    isError: assignmentsError,
    error: assignmentsErrObj,
    refetch: refetchAssignments,
  } = useApiQuery<PaginatedResponse<RelocationAssignmentRead>>(
    "dashboard-relocation-assignments",
    (signal) =>
      apiClient.get("/relocation/assignments", {
        params: { page: 1, page_size: 10 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 5. Pre-configured Contingency Scenarios
  const {
    data: scenariosEnvelope,
    isLoading: scenariosLoading,
    isError: scenariosError,
    error: scenariosErrObj,
    refetch: refetchScenarios,
  } = useApiQuery<ResponseEnvelope<ScenarioDefinitionRead[]>>(
    "dashboard-scenarios",
    (signal) => apiClient.get("/scenarios", { signal }),
    { cacheTtlMs: 120000 }
  );

  // Orchestrated manual refresh across all dashboard feeds
  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    try {
      await Promise.allSettled([
        refetchOverview(),
        refetchSources(),
        refetchSites(),
        refetchAssignments(),
        refetchScenarios(),
      ]);
      setLastUpdated(new Date());
    } finally {
      setIsRefreshing(false);
    }
  };

  const telemetryOverview = overviewEnvelope?.data || null;
  const scenariosData = scenariosEnvelope?.data || null;

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="space-y-6">
          {/* A. Executive Header & Operational Context */}
          <DashboardHeader
            telemetryOverview={telemetryOverview}
            isRefreshing={isRefreshing}
            onRefresh={handleRefreshAll}
            lastUpdated={lastUpdated}
          />

          {/* B. Executive Operational KPI Strip */}
          <DashboardKpiStrip
            sitesData={sitesData}
            sitesLoading={sitesLoading}
            sitesError={sitesError}
            assignmentsData={assignmentsData}
            assignmentsLoading={assignmentsLoading}
            assignmentsError={assignmentsError}
            telemetryOverview={telemetryOverview}
            telemetryLoading={overviewLoading}
            telemetryError={overviewError}
            scenariosData={scenariosData}
            scenariosLoading={scenariosLoading}
            scenariosError={scenariosError}
          />

          {/* C. Primary Operational Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Relocation & Safe Havens */}
            <div className="space-y-6">
              {/* Candidate Relocation Sites Table */}
              <CandidateSitesTable
                sites={sitesData?.data}
                totalCount={sitesData?.pagination?.total}
                isLoading={sitesLoading}
                isError={sitesError}
                errorMessage={sitesErrObj?.message}
              />

              {/* Planned Relocation Assignments */}
              <RelocationAssignmentsCard
                assignments={assignmentsData?.data}
                totalCount={assignmentsData?.pagination?.total}
                isLoading={assignmentsLoading}
                isError={assignmentsError}
                errorMessage={assignmentsErrObj?.message}
              />
            </div>

            {/* Right Column: Platform Telemetry & Contingencies */}
            <div className="space-y-6">
              {/* Data Sources Health & Freshness */}
              <TelemetryHealthCard
                overview={telemetryOverview}
                sources={sourcesData?.data}
                isLoading={overviewLoading || sourcesLoading}
                isError={overviewError || sourcesError}
                errorMessage={overviewErrObj?.message || sourcesErrObj?.message}
              />

              {/* Contingency Scenario Catalog */}
              <ScenarioReadinessCard
                scenarios={scenariosData}
                isLoading={scenariosLoading}
                isError={scenariosError}
                errorMessage={scenariosErrObj?.message}
              />
            </div>
          </div>

          {/* D. Operational Alerts & Threshold Notices */}
          <AlertsNoticeCard />
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
