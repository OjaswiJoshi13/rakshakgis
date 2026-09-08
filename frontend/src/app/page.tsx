"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { useAuth } from "@/context/AuthContext";
import { useOperational } from "@/context/OperationalContext";
import { apiClient, useApiQuery } from "@/lib/api";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
import {
  CandidateSiteRead,
  RelocationAssignmentRead,
  ScenarioDefinitionRead,
  TelemetryOverviewRead,
} from "@/types/dashboard";
import { Button } from "@/components/ui/Button";
import { Badge, RiskBadge, RelocationBadge } from "@/components/ui/Badge";
import { MetricCard } from "@/components/ui/MetricCard";
import { Alert } from "@/components/ui/Alert";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { RISK_BANDS, RELOCATION_PRIORITY_BANDS } from "@/design-system/tokens";
import {
  Map,
  RefreshCw,
  ChevronRight,
  ExternalLink,
  Compass,
} from "lucide-react";

export default function HomePage() {
  const { user } = useAuth();
  const { activeRegion, dataMode } = useOperational();
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 1. Platform Telemetry Overview
  const {
    data: overviewEnvelope,
    isLoading: overviewLoading,
    isError: overviewError,
    refetch: refetchOverview,
  } = useApiQuery<ResponseEnvelope<TelemetryOverviewRead>>(
    "home-telemetry-overview",
    (signal) => apiClient.get("/telemetry/overview", { signal }),
    { cacheTtlMs: 30000 }
  );

  // 2. Candidate Relocation Sites
  const {
    data: sitesData,
    isLoading: sitesLoading,
    isError: sitesError,
    refetch: refetchSites,
  } = useApiQuery<PaginatedResponse<CandidateSiteRead>>(
    "home-candidate-sites",
    (signal) =>
      apiClient.get("/sites", {
        params: { page: 1, page_size: 5 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 3. Relocation Assignments
  const {
    data: assignmentsData,
    isLoading: assignmentsLoading,
    isError: assignmentsError,
    refetch: refetchAssignments,
  } = useApiQuery<PaginatedResponse<RelocationAssignmentRead>>(
    "home-relocation-assignments",
    (signal) =>
      apiClient.get("/relocation/assignments", {
        params: { page: 1, page_size: 5 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 4. Contingency Scenarios
  const {
    data: scenariosEnvelope,
    isLoading: scenariosLoading,
    refetch: refetchScenarios,
  } = useApiQuery<ResponseEnvelope<ScenarioDefinitionRead[]>>(
    "home-scenarios",
    (signal) => apiClient.get("/scenarios", { signal }),
    { cacheTtlMs: 120000 }
  );

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.allSettled([
        refetchOverview(),
        refetchSites(),
        refetchAssignments(),
        refetchScenarios(),
      ]);
      setLastRefreshed(new Date());
    } finally {
      setIsRefreshing(false);
    }
  };

  const telemetryOverview = overviewEnvelope?.data || null;
  const sites = sitesData?.data || [];
  const assignments = assignmentsData?.data || [];
  const scenarios = scenariosEnvelope?.data || [];

  const totalSites = sitesData?.pagination?.total ?? sites.length;
  const totalAssignments = assignmentsData?.pagination?.total ?? assignments.length;
  const totalFeeds = telemetryOverview?.total_sources ?? 0;
  const healthyFeeds = telemetryOverview?.healthy_count ?? 0;

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="space-y-6 pb-12">
          {/* 1. TOP: Operational Command Briefing Header (Where am I?) */}
          <div className="border-b border-border-subtle pb-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <span className="sr-only">Chunk M5-01</span>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-surface-elevated border border-border-subtle text-text-secondary">
                    Sector: Himalayan Pilot (Chamoli)
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20">
                    Simulation Baseline
                    <span className="sr-only"> DEMO MODE</span>
                  </span>
                  <span className="text-xs text-text-muted tabular-nums">
                    Refreshed: {lastRefreshed.toLocaleTimeString("en-IN", { hour12: false })} IST
                  </span>
                </div>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
                  RakshakGIS Command Center Shell
                </h1>
                <p className="text-xs sm:text-sm text-text-muted mt-1 max-w-2xl leading-relaxed">
                  Authority-facing spatial decision support system for multi-hazard risk assessment,
                  dynamic red zone demarcation, and climate-resilient relocation planning.
                </p>
              </div>

              {/* Context Actions & Telemetry Indicator */}
              <div className="flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-2 bg-surface-elevated border border-border-subtle rounded-md px-3 py-1.5 text-xs text-text-secondary">
                  <StatusIndicator
                    status={
                      telemetryOverview && telemetryOverview.unavailable_count > 0
                        ? "critical"
                        : telemetryOverview && telemetryOverview.degraded_count > 0
                        ? "warning"
                        : "normal"
                    }
                  />
                  <span className="font-semibold text-text-primary">
                    {telemetryOverview
                      ? `${healthyFeeds}/${totalFeeds} Sensors Healthy`
                      : "Telemetry Active"}
                  </span>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleRefresh}
                  isLoading={isRefreshing}
                  className="text-xs gap-1.5"
                  title={`Last synchronized: ${lastRefreshed.toLocaleTimeString()}`}
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
                  <span>Sync Feeds</span>
                </Button>

                <Link href="/gis">
                  <Button variant="primary" size="sm" className="gap-1.5 text-xs font-medium">
                    <Map className="h-3.5 w-3.5" />
                    <span>Open GIS Map</span>
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* 2. DOMINANT SECTION: WHAT REQUIRES ATTENTION? */}
          <section aria-labelledby="attention-heading" className="rounded-xl border-2 border-red-500/40 dark:border-red-600/40 bg-surface-panel p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2">
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-600" />
                </span>
                <h2 id="attention-heading" className="text-base font-bold text-text-primary tracking-tight">
                  What Requires Immediate Officer Attention
                </h2>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-red-100 text-red-800 dark:bg-red-950/80 dark:text-red-300 border border-red-300 dark:border-red-800 self-start sm:self-auto">
                2 Active Priority Incidents
              </span>
            </div>

            {/* Critical Early Warning Alerts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Alert severity="danger" title="CRITICAL: Dynamic Red Zone Threshold Exceeded">
                Landslide slope telemetry in Joshimath Sector B exceeded warning trigger (35.2°).
                Immediate officer review required under SOP-RZ-01.
              </Alert>
              <Alert severity="warning" title="WEATHER WATCH: IMD Rainfall Warning">
                Heavy rainfall observation detected (72.4 mm/24h &gt; 64.5 mm threshold). Soil moisture
                saturation escalating in Dasholi block.
              </Alert>
            </div>

            {/* Supporting Operational Context Notices */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 border-t border-border-subtle/60">
              <Alert severity="info" title="OPERATIONAL CONTEXT: Regional Baseline Active">
                Authoritative baseline telemetry engaged for Himalayan pilot sector (40 villages, 12 candidate safe terraces).
                Synchronized with regional environmental sensor networks.
              </Alert>
              <Alert severity="success" title="OPERATIONAL PROTOCOL: Decision Support Ready">
                Unified command shell active. Statutory Rule 12 verification gateway configured for multi-hazard spatial assessment and relocation planning.
              </Alert>
            </div>
          </section>

          {/* 3. SITUATION SUMMARY: Operational Decision Sequence */}
          <section aria-labelledby="workflow-sequence-heading" className="rounded-lg border border-border-subtle bg-surface-panel p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2.5">
              <div className="flex items-center gap-2">
                <Compass className="h-4 w-4 text-text-muted" />
                <h2 id="workflow-sequence-heading" className="text-xs font-bold text-text-primary uppercase tracking-wider">
                  Operational Decision Progression
                </h2>
              </div>
              <span className="text-xs text-text-muted">
                Rule 12 Standard Operating Procedure
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-border-subtle bg-surface-elevated/40 rounded-md border border-border-subtle overflow-hidden">
              <div className="p-3">
                <div className="flex items-center gap-1.5 text-xs text-text-muted mb-1">
                  <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">1</span>
                  <span className="font-medium">Understand</span>
                </div>
                <div className="text-xs font-semibold text-text-primary">Situational Risk</div>
                <div className="text-xs text-text-muted mt-0.5 truncate">Current posture</div>
              </div>

              <Link
                href="/gis"
                className="p-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">2</span>
                    <span className="font-medium">Locate</span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-text-muted group-hover:text-text-primary" />
                </div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-text-primary">
                  Spatial GIS Map
                </div>
                <div className="text-xs text-text-muted mt-0.5 truncate">Slope & Red Zones</div>
              </Link>

              <Link
                href="/villages"
                className="p-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">3</span>
                    <span className="font-medium">Assess</span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-text-muted group-hover:text-text-primary" />
                </div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-text-primary">
                  Habitations
                </div>
                <div className="text-xs text-text-muted mt-0.5 truncate">Vulnerability Index</div>
              </Link>

              <Link
                href="/operations/sites"
                className="p-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">4</span>
                    <span className="font-medium">Compare</span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-text-muted group-hover:text-text-primary" />
                </div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-text-primary">
                  Safe Terraces
                </div>
                <div className="text-xs text-text-muted mt-0.5 truncate">{totalSites} Verified Sites</div>
              </Link>

              <Link
                href="/operations/relocation"
                className="p-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">5</span>
                    <span className="font-medium">Decide</span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-text-muted group-hover:text-text-primary" />
                </div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-text-primary">
                  Relocation Plan
                </div>
                <div className="text-xs text-text-muted mt-0.5 truncate">{totalAssignments} Assignments</div>
              </Link>

              <Link
                href="/operations/review"
                className="p-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-panel border border-border-strong text-[10px] font-semibold text-text-primary">6</span>
                    <span className="font-medium">Verify</span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-text-muted group-hover:text-text-primary" />
                </div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-text-primary">
                  Officer Sign-Off
                </div>
                <div className="text-xs text-text-muted mt-0.5 truncate">Audit & Seal</div>
              </Link>
            </div>
          </section>


          {/* 5. System Baseline & Governance Reference (Secondary Technical Specification) */}
          <section aria-labelledby="system-parameters-heading" className="space-y-4 pt-2">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <h2
                id="system-parameters-heading"
                className="text-xs font-semibold text-text-muted"
              >
                System Baseline & Architecture Parameters
              </h2>
              <span className="text-xs text-text-muted">Specification Registry</span>
            </div>

            {/* Baseline Parameters Specification Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <MetricCard
                label="Region Profile"
                value="Himalayan"
                subtext="Chamoli District Pilot"
                status="normal"
              />
              <MetricCard
                label="Multi-Hazard Model"
                value="6"
                unit="Factors"
                subtext="0.30H+0.20F+0.15R+0.15S+0.10D+0.10V"
                status="info"
              />
              <MetricCard
                label="Relocation Priority"
                value="4"
                unit="Bands"
                subtext="Immediate, Short, Medium, Monitor"
                status="warning"
              />
              <MetricCard
                label="Coordinate System"
                value="EPSG:4326"
                subtext="WGS 84 Standard Lat/Long"
                status="normal"
              />
            </div>

            {/* Composite Risk Score Classifications — Unified Specification Ledger */}
            <div className="rounded-lg border border-border-subtle bg-surface-panel p-4 space-y-3">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">
                  Composite Risk Score Classifications
                </h3>
                <p className="text-xs text-text-muted">
                  Deterministic risk score bands matching domain engine thresholds.
                </p>
              </div>

              <div className="overflow-x-auto rounded-md border border-border-subtle">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface-elevated/70 text-xs font-semibold text-text-secondary border-b border-border-subtle">
                    <tr>
                      <th className="px-3.5 py-2">Band</th>
                      <th className="px-3.5 py-2">Score Range</th>
                      <th className="px-3.5 py-2">Operational Classification & Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle bg-surface-panel">
                    {(
                      Object.keys(RISK_BANDS) as Array<keyof typeof RISK_BANDS>
                    ).map((bandKey) => {
                      const band = RISK_BANDS[bandKey];
                      return (
                        <tr key={bandKey} className="hover:bg-surface-elevated/40 transition-colors">
                          <td className="px-3.5 py-2">
                            <RiskBadge band={bandKey} showScore={false} />
                          </td>
                          <td className="px-3.5 py-2 tabular-nums text-text-secondary font-medium">
                            {band.min}–{band.max}
                          </td>
                          <td className="px-3.5 py-2 text-text-secondary leading-snug">
                            {band.description}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Relocation Urgency Bands — Unified Specification Ledger */}
            <div className="rounded-lg border border-border-subtle bg-surface-panel p-4 space-y-3">
              <h3
                id="relocation-tokens-heading"
                className="text-xs font-semibold text-text-muted"
              >
                Relocation Urgency Bands (Authoritative Specification)
              </h3>

              <div className="overflow-x-auto rounded-md border border-border-subtle">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface-elevated/70 text-xs font-semibold text-text-secondary border-b border-border-subtle">
                    <tr>
                      <th className="px-3.5 py-2">Urgency Tier</th>
                      <th className="px-3.5 py-2">Index Score</th>
                      <th className="px-3.5 py-2">Action Horizon & Mandate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle bg-surface-panel">
                    {(
                      Object.keys(RELOCATION_PRIORITY_BANDS) as Array<
                        keyof typeof RELOCATION_PRIORITY_BANDS
                      >
                    ).map((bandKey) => {
                      const band = RELOCATION_PRIORITY_BANDS[bandKey];
                      return (
                        <tr key={bandKey} className="hover:bg-surface-elevated/40 transition-colors">
                          <td className="px-3.5 py-2">
                            <RelocationBadge band={bandKey} />
                          </td>
                          <td className="px-3.5 py-2 tabular-nums text-text-secondary font-medium">
                            Score: {band.min}–{band.max}
                          </td>
                          <td className="px-3.5 py-2 text-text-secondary">
                            Action horizon: {band.label}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
