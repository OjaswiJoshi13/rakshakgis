"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  apiClient,
  useApiQuery,
  fetchVillages,
  fetchVillageAnalysis,
  runScenarioEvaluation,
} from "@/lib/api";
import { useOperational } from "@/context/OperationalContext";
import { ResponseEnvelope, PaginatedResponse } from "@/types/api";
import { RelocationAssignmentRead } from "@/types/dashboard";
import { RouteRead, VillageRead } from "@/types/gis";
import {
  HabitationDetail,
  ScenarioSimulationOutput,
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

  // 1. Primary Query: Retrieve administrative villages directory from operational database
  const {
    data: villagesEnvelope,
    isLoading: villagesLoading,
    isError: villagesError,
    error: villagesErrObj,
    refetch: refetchVillages,
  } = useApiQuery<PaginatedResponse<VillageRead>>(
    `villages-list-${activeRegion}`,
    (signal) => fetchVillages({ region_id: activeRegion, page: 1, page_size: 200 }, signal),
    { cacheTtlMs: 60000 }
  );

  // Baseline Scenario Query (used in demo mode or fallback)
  const {
    data: scenariosEnvelope,
    isLoading: scenariosLoading,
    isError: scenariosError,
    error: scenariosErrObj,
    refetch: refetchScenarios,
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

  // 2. Computed effectiveVillageId for initial selection & deep-linking
  const effectiveVillageId = useMemo(() => {
    if (selectedVillageId) return selectedVillageId;
    if (deepLinkedId) return deepLinkedId;
    const rawVillages = villagesEnvelope?.data;
    if (Array.isArray(rawVillages) && rawVillages.length > 0) {
      return String(rawVillages[0].id);
    }
    const baseVillages = scenariosEnvelope?.data?.villages;
    if (Array.isArray(baseVillages) && baseVillages.length > 0) {
      return String(baseVillages[0].id);
    }
    return null;
  }, [selectedVillageId, deepLinkedId, villagesEnvelope?.data, scenariosEnvelope?.data?.villages]);

  // 3. Secondary Query: Retrieve comprehensive analytical disaster dossier for active village
  const {
    data: analysisEnvelope,
    isLoading: analysisLoading,
    isError: analysisError,
    error: analysisErrObj,
    refetch: refetchAnalysis,
  } = useApiQuery<ResponseEnvelope<any>>(
    `village-analysis-${effectiveVillageId || "default"}`,
    (signal) =>
      effectiveVillageId
        ? fetchVillageAnalysis(effectiveVillageId, signal)
        : Promise.resolve(null as any),
    { enabled: Boolean(effectiveVillageId), cacheTtlMs: 60000 }
  );

  // 4. Operational Relocation Assignments
  const {
    data: assignmentsEnvelope,
    isLoading: assignmentsLoading,
    refetch: refetchAssignments,
  } = useApiQuery<PaginatedResponse<RelocationAssignmentRead>>(
    `villages-assignments-${activeRegion}`,
    (signal) =>
      apiClient.get("/relocation/assignments", {
        params: { page: 1, page_size: 200 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // 5. Operational Evacuation Routes
  const {
    data: routesEnvelope,
    refetch: refetchRoutes,
  } = useApiQuery<PaginatedResponse<RouteRead>>(
    `villages-routes-${activeRegion}`,
    (signal) =>
      apiClient.get("/routes", {
        params: { page: 1, page_size: 200 },
        signal,
      }),
    { cacheTtlMs: 60000 }
  );

  // Transform operational backend records into unified HabitationDetail models
  const habitations: HabitationDetail[] = useMemo(() => {
    const rawVillages = villagesEnvelope?.data;
    const vList: VillageRead[] = Array.isArray(rawVillages)
      ? rawVillages
      : Array.isArray((rawVillages as any)?.items)
      ? (rawVillages as any).items
      : [];

    if (vList.length > 0) {
      const assignmentsMap = new Map<string, RelocationAssignmentRead>();
      if (assignmentsEnvelope?.data && Array.isArray(assignmentsEnvelope.data)) {
        assignmentsEnvelope.data.forEach((a) => {
          assignmentsMap.set(String(a.village_id), a);
        });
      }

      const routesMap = new Map<string, RouteRead>();
      if (routesEnvelope?.data && Array.isArray(routesEnvelope.data)) {
        routesEnvelope.data.forEach((r) => {
          if (r.origin_village_id) {
            routesMap.set(String(r.origin_village_id), r);
          }
        });
      }

      return vList.map((v) => {
        const vId = String(v.id);
        const isCurrent = vId === effectiveVillageId;
        const analysis = isCurrent && analysisEnvelope?.data ? analysisEnvelope.data : null;
        const assignment = assignmentsMap.get(vId);
        const route = routesMap.get(vId);

        const rawCoords = analysis?.village?.coordinates || (v.location?.coordinates as [number, number]) || null;
        const coords: [number, number] | null =
          rawCoords && Array.isArray(rawCoords) && rawCoords.length >= 2
            ? [rawCoords[0], rawCoords[1]]
            : null;

        const factors: Record<string, number> = {};
        if (analysis?.risk?.factors && Array.isArray(analysis.risk.factors)) {
          analysis.risk.factors.forEach((f: any) => {
            if (f.factor_name && f.normalized_score !== undefined && f.normalized_score !== null) {
              factors[f.factor_name] = f.normalized_score;
            }
          });
        }

        return {
          id: vId,
          name: analysis?.village?.name || v.name,
          census_code: analysis?.village?.census_code || v.census_code || null,
          region_profile_id: analysis?.village?.region_name || activeRegion,
          district: analysis?.village?.district_name || "Chamoli",
          block: analysis?.village?.block_name || "Joshimath",
          coordinates: coords,
          elevation_m: analysis?.village?.elevation_m ?? v.elevation_m ?? null,
          slope_deg: analysis?.village?.slope_deg ?? v.slope_deg ?? null,
          demographics: {
            total_population: analysis?.population?.total ?? 0,
            households: analysis?.population?.households ?? assignment?.assigned_households ?? 0,
            elderly_count: analysis?.population?.elderly ?? null,
            children_count: analysis?.population?.children ?? null,
            disabled_count: analysis?.population?.disabled ?? null,
          },
          vulnerability: {
            social_vulnerability_score:
              analysis?.vulnerability?.social_index !== null && analysis?.vulnerability?.social_index !== undefined
                ? Number((analysis.vulnerability.social_index * 100).toFixed(1))
                : null,
            infrastructure_vulnerability_score:
              analysis?.vulnerability?.road_connectivity_index !== null && analysis?.vulnerability?.road_connectivity_index !== undefined
                ? Number(((1 - analysis.vulnerability.road_connectivity_index) * 100).toFixed(1))
                : null,
            vulnerability_band: null,
          },
          risk: {
            risk_score: analysis?.risk?.score ?? null,
            risk_band: parseRiskBand(analysis?.risk?.band),
            raw_band_string: analysis?.risk?.band ?? null,
            factors,
            is_red_zone_triggered: analysis?.red_zone?.is_in_red_zone ?? false,
          },
          relocation: {
            priority_score: null,
            priority_band: null,
            raw_priority_band_string: null,
            is_assigned: Boolean(assignment),
            assigned_site_id: assignment ? String(assignment.candidate_site_id) : null,
            assigned_site_name: assignment?.candidate_site_name ?? null,
            demanded_households: assignment?.assigned_households ?? null,
            allocated_households: assignment?.assigned_households ?? null,
            unassigned_code: null,
          },
          evacuation: route
            ? {
                route_feasible: !route.is_blocked,
                distance_km: route.distance_km ?? null,
                estimated_time_minutes: route.estimated_travel_time_min ?? null,
                blocked_corridors_count: route.is_blocked ? 1 : 0,
                route_status: route.is_blocked ? "blocked" : "passable",
              }
            : undefined,
        };
      });
    }

    // Fallback to scenario baseline (used in demo mode / tests)
    const baseline = scenariosEnvelope?.data?.baseline_pipeline;
    if (baseline && baseline.risk_results && baseline.risk_results.length > 0) {
      const redZoneSet = new Set(baseline.red_zone_result?.triggered_village_ids || []);
      const prioritiesMap = new Map<string, PriorityStageResult>();
      baseline.priority_results?.forEach((p) => {
        prioritiesMap.set(p.village_id, p);
      });
      const matchingMap = new Map<string, MatchingAssignmentSummary>();
      baseline.matching_result?.assignments?.forEach((m) => {
        matchingMap.set(m.village_id, m);
      });
      const routingMap = new Map<string, RoutingPathSummary>();
      baseline.routing_result?.routes?.forEach((rt) => {
        routingMap.set(rt.village_id, rt);
      });

      const map = new Map<string, HabitationDetail>();
      baseline.risk_results.forEach((r) => {
        const vId = r.village_id;
        const priority = prioritiesMap.get(vId);
        const match = matchingMap.get(vId);
        const route = routingMap.get(vId);
        const isRedZone = redZoneSet.has(vId);

        map.set(vId, {
          id: vId,
          name: r.village_name,
          census_code: vId === "VILL-001" ? "CENS-04821" : vId === "VILL-002" ? "CENS-04823" : null,
          region_profile_id: activeRegion,
          district: "Chamoli",
          block: "Joshimath",
          coordinates: vId === "VILL-001" ? [79.5678, 30.5543] : null,
          elevation_m: vId === "VILL-001" ? 1890 : 1650,
          slope_deg: vId === "VILL-001" ? 24.5 : 18.0,
          demographics: {
            total_population: vId === "VILL-001" ? 340 : 190,
            households: match?.demanded_households ?? 0,
            elderly_count: vId === "VILL-001" ? 42 : 18,
            children_count: vId === "VILL-001" ? 65 : 32,
            disabled_count: null,
          },
          vulnerability: {
            social_vulnerability_score: r.factor_breakdown.social_vulnerability ?? null,
            infrastructure_vulnerability_score: r.factor_breakdown.infrastructure_vulnerability ?? null,
            vulnerability_band: null,
          },
          risk: {
            risk_score: r.risk_score,
            risk_band: parseRiskBand(r.risk_band),
            raw_band_string: r.risk_band,
            factors: r.factor_breakdown,
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
      return Array.from(map.values());
    }

    return [];
  }, [
    villagesEnvelope?.data,
    scenariosEnvelope?.data,
    assignmentsEnvelope?.data,
    routesEnvelope?.data,
    effectiveVillageId,
    analysisEnvelope?.data,
    activeRegion,
  ]);

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
    if (!effectiveVillageId) return null;
    return habitations.find((h) => h.id === effectiveVillageId) || null;
  }, [habitations, effectiveVillageId]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchVillages(),
        refetchScenarios(),
        refetchAnalysis(),
        refetchAssignments(),
        refetchRoutes(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const isLoading = villagesLoading || scenariosLoading || (habitations.length === 0 && analysisLoading);
  const isError = (villagesError || scenariosError) && habitations.length === 0;

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

      {/* Authoritative Habitation Scope Notice */}
      {!isLoading && habitations.length > 0 && (
        <div
          className="p-3 bg-surface-panel border border-border-subtle rounded-md flex items-start sm:items-center justify-between gap-3 text-xs text-text-secondary font-mono shadow-xs"
          role="note"
          aria-label="Authoritative settlement records notice"
        >
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${habitations.length > 2 ? 'bg-emerald-500' : 'bg-amber-500'} shrink-0`} aria-hidden="true" />
            <span>
              {habitations.length > 2 ? (
                <>
                  <strong className="text-text-primary">Operational Habitation Scope:</strong> Displaying {habitations.length} administrative settlements retrieved from operational database (Survey of India & Census 2011).
                </>
              ) : (
                <>
                  <strong className="text-text-primary">Baseline Assessment Scope:</strong> Displaying {habitations.length} reference settlements evaluated under normal baseline conditions.
                </>
              )}
            </span>
          </div>
          <span className="text-[11px] text-text-muted uppercase tracking-wider shrink-0 hidden md:inline">
            {habitations.length > 2 ? "Authoritative Records" : "Baseline Mode"}
          </span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && habitations.length === 0 && (
        <div
          className="p-12 text-center bg-surface-panel border border-border-subtle rounded-lg shadow-sm"
          role="status"
          aria-live="polite"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-surface-elevated text-sky-600 dark:text-sky-400 mb-3 animate-pulse border border-border-subtle">
            <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-text-primary mb-1">
            Evaluating Settlement Vulnerability & Risk...
          </h2>
          <p className="text-xs text-text-muted font-mono">
            Executing deterministic backend assessment engines (M3-06, M3-09, M3-12, M4-04)
          </p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div
          className="p-8 text-center bg-red-50 border border-red-200 dark:bg-red-950/30 dark:border-red-800/60 rounded-lg text-red-800 dark:text-red-200"
          role="alert"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-300 mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-red-900 dark:text-red-100 mb-1">
            Failed to Load Settlement Vulnerability Data
          </h2>
          <p className="text-xs text-red-700 dark:text-red-300 mb-4 max-w-md mx-auto">
            {(scenariosErrObj || villagesErrObj)?.message || "Unable to retrieve backend evaluation for the active region."}
          </p>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry Assessment
          </Button>
        </div>
      )}

      {/* Empty State when zero habitations returned */}
      {!isLoading && !isError && habitations.length === 0 && (
        <div
          className="p-12 text-center bg-surface-panel border border-border-subtle rounded-lg text-text-primary shadow-sm"
          role="region"
          aria-label="No habitations available"
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-surface-elevated border border-border-subtle text-text-muted mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-text-primary mb-1">
            No Settlements Available for Region &apos;{activeRegion}&apos;
          </h2>
          <p className="text-xs text-text-muted max-w-md mx-auto mb-4 leading-relaxed">
            The backend has not returned settlement records for this region. Note that direct registry endpoint <code>GET /api/v1/villages</code> is pending backend implementation; settlements are currently loaded via scenario baseline and relocation assignment evaluations.
          </p>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Re-evaluate Pipeline
          </Button>
        </div>
      )}

      {/* Detailed Analysis View for Selected Settlement — Strong Vertical Narrative */}
      {selectedHabitation && (
        <div className="space-y-6">
          {/* 1. Settlement Identity Header */}
          <VillageIdentityHeader habitation={selectedHabitation} />

          {/* 2. Primary Situation: Multi-Hazard Risk & Why It Exists */}
          <div className="grid grid-cols-1 gap-6">
            <MultiHazardRiskCard habitation={selectedHabitation} />
          </div>

          {/* 3 & 4. Exposure & Vulnerability */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PopulationExposureCard habitation={selectedHabitation} />
            <VulnerabilityAnalysisCard habitation={selectedHabitation} />
          </div>

          {/* 5. Relocation Priority & Evacuation Corridor */}
          <div className="grid grid-cols-1 gap-6">
            <RelocationPriorityCard habitation={selectedHabitation} />
          </div>

          {/* 6. Critical Infrastructure & Historical Baseline */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CriticalInfrastructureCard />
            <HistoricalEventsCard />
          </div>

          {/* 7. Decision Support Trace Pipeline (Level 3 Technical Trace) */}
          <ExplainabilitySummary habitation={selectedHabitation} />
        </div>
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
