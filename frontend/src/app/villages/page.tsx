"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { apiClient, useApiQuery } from "@/lib/api";
import { useOperational } from "@/context/OperationalContext";
import { ResponseEnvelope, PaginatedResponse } from "@/types/api";
import { RelocationAssignmentRead } from "@/types/dashboard";
import { RouteRead } from "@/types/gis";
import {
  HabitationDetail,
  ScenarioSimulationOutput,
  VillageRiskStageResult,
  PriorityStageResult,
  MatchingAssignmentSummary,
  RoutingPathSummary,
  parseRiskBand,
  parseRelocationPriorityBand,
} from "@/types/villages";
import {
  VillageSelectorBar,
  VillageIdentityHeader,
  PopulationExposureCard,
  VulnerabilityAnalysisCard,
  MultiHazardRiskCard,
  RelocationPriorityCard,
  HistoricalEventsCard,
  CriticalInfrastructureCard,
  ExplainabilitySummary,
} from "@/components/villages";
import { Button } from "@/components/ui/Button";

function VillageAnalysisContent() {
  const searchParams = useSearchParams();
  const deepLinkedId = searchParams.get("id") || searchParams.get("village_id");

  const { activeRegion, dataMode } = useOperational();
  const [selectedVillageId, setSelectedVillageId] = useState<string | null>(deepLinkedId);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Reset selected village on activeRegion change to prevent cross-region state leak
  useEffect(() => {
    setSelectedVillageId(null);
  }, [activeRegion]);

  // 1. Primary Query: Execute Scenario Baseline Pipeline for activeRegion
  // This evaluates M3-06 Risk, M3-09 Vulnerability, M3-11 Red Zone, M3-12 Priority, M4-04 Matching, M4-05 Routing
  const {
    data: scenarioEnvelope,
    isLoading: scenarioLoading,
    isError: scenarioError,
    error: scenarioErrObj,
    refetch: refetchScenario,
  } = useApiQuery<ResponseEnvelope<ScenarioSimulationOutput>>(
    `villages-baseline-${activeRegion}`,
    (signal) =>
      apiClient.post(
        "/scenarios/run",
        {
          scenario_type: "NORMAL",
          region_profile_id: activeRegion,
        },
        { signal }
      ),
    { cacheTtlMs: 60000 }
  );

  // 2. Secondary Query: Relocation Assignments for active region
  const {
    data: assignmentsEnvelope,
    isLoading: assignmentsLoading,
    refetch: refetchAssignments,
  } = useApiQuery<PaginatedResponse<RelocationAssignmentRead>>(
    `villages-assignments-${activeRegion}`,
    (signal) =>
      apiClient.get("/relocation/assignments", {
        params: { page: 1, page_size: 50 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 3. Secondary Query: Evacuation Routes for active region
  const {
    data: routesEnvelope,
    refetch: refetchRoutes,
  } = useApiQuery<PaginatedResponse<RouteRead>>(
    `villages-routes-${activeRegion}`,
    (signal) =>
      apiClient.get("/routes", {
        params: { page: 1, page_size: 50 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // Transform backend pipeline outputs into unified HabitationDetail models
  const habitations: HabitationDetail[] = useMemo(() => {
    const baseline = scenarioEnvelope?.data?.baseline_pipeline;
    const simOutput = scenarioEnvelope?.data;

    if (!baseline && !assignmentsEnvelope?.data) {
      return [];
    }

    const map = new Map<string, HabitationDetail>();

    // 1. Process Scenario Baseline Risk & Priority Results
    if (baseline) {
      const riskMap = new Map<string, VillageRiskStageResult>();
      baseline.risk_results.forEach((r) => riskMap.set(r.village_id, r));

      const priorityMap = new Map<string, PriorityStageResult>();
      baseline.priority_results.forEach((p) => priorityMap.set(p.village_id, p));

      const matchingMap = new Map<string, MatchingAssignmentSummary>();
      if (baseline.matching_result?.assignments) {
        baseline.matching_result.assignments.forEach((m) => matchingMap.set(m.village_id, m));
      }

      const routingMap = new Map<string, RoutingPathSummary>();
      if (baseline.routing_result?.routes) {
        baseline.routing_result.routes.forEach((rt) => routingMap.set(rt.village_id, rt));
      }

      const triggeredSet = new Set<string>(baseline.red_zone_result?.triggered_village_ids || []);

      baseline.risk_results.forEach((r) => {
        const priority = priorityMap.get(r.village_id);
        const match = matchingMap.get(r.village_id);
        const route = routingMap.get(r.village_id);
        const isRedZone = triggeredSet.has(r.village_id);

        const factors = r.factor_breakdown || {};
        const socialVuln = factors.social_vulnerability ?? null;
        const infraVuln = factors.infrastructure_vulnerability ?? null;

        map.set(r.village_id, {
          id: r.village_id,
          name: r.village_name,
          census_code: null,
          region_profile_id: simOutput?.region_profile_id || activeRegion,
          district: null,
          block: null,
          coordinates: null, // Pure region-agnostic; coordinates provided if supplied by spatial backend
          elevation_m: null,
          slope_deg: null, // Physical terrain slope only populated when supplied by spatial DEM backend (not inferred from susceptibility index)
          demographics: {
            total_population: null, // Authoritative census population only populated if provided by backend (never synthesized as households * 4)
            households: match?.demanded_households ?? null,
            elderly_count: null,
            children_count: null,
            disabled_count: null,
          },
          vulnerability: {
            social_vulnerability_score: socialVuln,
            infrastructure_vulnerability_score: infraVuln,
            vulnerability_band: null,
          },
          risk: {
            risk_score: r.risk_score,
            risk_band: parseRiskBand(r.risk_band),
            raw_band_string: r.risk_band,
            factors,
            is_red_zone_triggered: isRedZone,
          },
          relocation: {
            priority_score: priority?.priority_score ?? null,
            priority_band: parseRelocationPriorityBand(priority?.priority_band),
            raw_priority_band_string: priority?.priority_band ?? null,
            is_assigned: match?.is_assigned ?? false,
            assigned_site_id: match?.assigned_site_id ?? null,
            assigned_site_name: match?.assigned_site_name ?? null,
            demanded_households: match?.demanded_households ?? null,
            allocated_households: match?.allocated_households ?? null,
            unassigned_code: match?.unassigned_code ?? null,
          },
          evacuation: route
            ? {
                route_feasible: route.is_feasible,
                distance_km: route.distance_km ?? null,
                estimated_time_minutes: route.estimated_time_minutes ?? null,
                blocked_corridors_count: route.blocked_avoided_count ?? 0,
                route_status: route.route_status,
              }
            : undefined,
        });
      });
    }

    // 2. Supplement / Merge with Relocation Assignments if present
    if (assignmentsEnvelope?.data) {
      assignmentsEnvelope.data.forEach((a) => {
        const vId = String(a.village_id);
        const existing = map.get(vId);

        if (existing) {
          existing.relocation.is_assigned = true;
          existing.relocation.assigned_site_id = String(a.candidate_site_id);
          existing.relocation.assigned_site_name = a.candidate_site_name ?? existing.relocation.assigned_site_name;
          existing.relocation.allocated_households = a.assigned_households;
          if (a.assigned_population && (!existing.demographics.total_population || existing.demographics.total_population === 0)) {
            existing.demographics.total_population = a.assigned_population;
          }
        } else if (a.village_name) {
          map.set(vId, {
            id: vId,
            name: a.village_name,
            region_profile_id: activeRegion,
            demographics: {
              total_population: a.assigned_population,
              households: a.assigned_households,
            },
            vulnerability: {
              social_vulnerability_score: null,
              infrastructure_vulnerability_score: null,
            },
            risk: {
              risk_score: null,
              risk_band: null,
              factors: {},
              is_red_zone_triggered: false,
            },
            relocation: {
              priority_score: null,
              priority_band: null,
              is_assigned: true,
              assigned_site_id: String(a.candidate_site_id),
              assigned_site_name: a.candidate_site_name,
              demanded_households: a.assigned_households,
              allocated_households: a.assigned_households,
            },
          });
        }
      });
    }

    return Array.from(map.values());
  }, [scenarioEnvelope?.data, assignmentsEnvelope?.data, activeRegion]);

  // Keep selection synchronized
  useEffect(() => {
    if (habitations.length > 0) {
      if (deepLinkedId && habitations.some((h) => h.id === deepLinkedId)) {
        setSelectedVillageId(deepLinkedId);
      } else if (!selectedVillageId || !habitations.some((h) => h.id === selectedVillageId)) {
        setSelectedVillageId(habitations[0].id);
      }
    } else {
      setSelectedVillageId(null);
    }
  }, [habitations, deepLinkedId, selectedVillageId]);

  const selectedHabitation = useMemo(() => {
    if (!selectedVillageId) return null;
    return habitations.find((h) => h.id === selectedVillageId) || null;
  }, [habitations, selectedVillageId]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([refetchScenario(), refetchAssignments(), refetchRoutes()]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const isLoading = scenarioLoading || assignmentsLoading;
  const isError = scenarioError && habitations.length === 0;

  return (
    <div className="space-y-6">
      {/* Top Selector Bar */}
      <VillageSelectorBar
        villages={habitations}
        selectedVillageId={selectedVillageId}
        onSelectVillage={setSelectedVillageId}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
        isLoading={isLoading}
      />

      {/* Pilot Baseline Assessment Scope Notice (Truthful settlement discovery disclosure) */}
      {!isLoading && habitations.length > 0 && (
        <div
          className="p-3 bg-slate-900/80 border border-slate-800 rounded-md flex items-start sm:items-center justify-between gap-3 text-xs text-slate-400 font-mono"
          role="note"
          aria-label="Pilot dataset evaluation notice"
        >
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" aria-hidden="true" />
            <span>
              <strong className="text-slate-300">Baseline Assessment Scope:</strong> Displaying {habitations.length} representative settlements evaluated by the active scenario baseline pipeline (M4-06). A comprehensive regional registry (<code>GET /api/v1/villages</code>) is pending backend API implementation.
            </span>
          </div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider shrink-0 hidden md:inline">
            Authoritative Records
          </span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && habitations.length === 0 && (
        <div
          className="p-12 text-center bg-slate-900 border border-slate-800 rounded-lg"
          role="status"
          aria-live="polite"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-800 text-sky-400 mb-3 animate-pulse">
            <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-slate-200 mb-1">
            Evaluating Settlement Vulnerability & Risk...
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Executing deterministic backend assessment engines (M3-06, M3-09, M3-12, M4-04)
          </p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div
          className="p-8 text-center bg-red-950/30 border border-red-800/60 rounded-lg text-red-200"
          role="alert"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-900/50 text-red-300 mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-red-100 mb-1">
            Failed to Load Settlement Vulnerability Data
          </h2>
          <p className="text-xs text-red-300 mb-4 max-w-md mx-auto">
            {scenarioErrObj?.message || "Unable to retrieve backend evaluation for the active region."}
          </p>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry Assessment
          </Button>
        </div>
      )}

      {/* Empty State when zero habitations returned */}
      {!isLoading && !isError && habitations.length === 0 && (
        <div
          className="p-12 text-center bg-slate-900 border border-slate-800 rounded-lg text-slate-300"
          role="region"
          aria-label="No habitations available"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-800 text-slate-400 mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-slate-200 mb-1">
            No Settlements Available for Region &apos;{activeRegion}&apos;
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto mb-4 leading-relaxed">
            The backend has not returned settlement records for this region. Note that direct registry endpoint <code>GET /api/v1/villages</code> is pending backend implementation; settlements are currently loaded via scenario baseline and relocation assignment evaluations.
          </p>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Re-evaluate Pipeline
          </Button>
        </div>
      )}

      {/* Detailed Analysis View for Selected Settlement */}
      {selectedHabitation && (
        <>
          {/* Decision Support Trace Pipeline */}
          <ExplainabilitySummary habitation={selectedHabitation} />

          {/* Identity & Context Header */}
          <VillageIdentityHeader habitation={selectedHabitation} />

          {/* Primary Metrics & Analysis Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Multi-Hazard Risk Card */}
            <MultiHazardRiskCard habitation={selectedHabitation} />

            {/* Relocation Priority & Routing Card */}
            <RelocationPriorityCard habitation={selectedHabitation} />

            {/* Demographics & Exposure Card */}
            <PopulationExposureCard habitation={selectedHabitation} />

            {/* Vulnerability & Isolation Card */}
            <VulnerabilityAnalysisCard habitation={selectedHabitation} />

            {/* Historical Events Card */}
            <HistoricalEventsCard />

            {/* Critical Infrastructure Card */}
            <CriticalInfrastructureCard />
          </div>
        </>
      )}
    </div>
  );
}

export default function VillageAnalysisPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <Suspense
          fallback={
            <div className="p-12 text-center text-slate-400 font-mono text-sm">
              Loading Habitation Analysis...
            </div>
          }
        >
          <VillageAnalysisContent />
        </Suspense>
      </AppLayout>
    </ProtectedRoute>
  );
}
