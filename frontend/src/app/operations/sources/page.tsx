"use client";

import React, { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { RefreshCw, Radio, Server, CheckCircle2 } from "lucide-react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import {
  TelemetryOverviewCards,
  SourceFilterBar,
  SourceTable,
  SourceDetailModal,
  ThresholdsReferenceCard,
} from "@/components/operations/sources";
import {
  DataSourceFilterCriteria,
  DataSourceTelemetryRead,
  TelemetryOverviewRead,
} from "@/types/telemetry";
import {
  getTelemetryOverview,
  listDataSources,
  probeDataSource,
} from "@/lib/api/telemetry";

function DataSourcesContent() {
  const searchParams = useSearchParams();
  const targetSourceId = searchParams ? searchParams.get("sourceId") : null;

  // State
  const [overview, setOverview] = useState<TelemetryOverviewRead | null>(null);
  const [sources, setSources] = useState<DataSourceTelemetryRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [criteria, setCriteria] = useState<DataSourceFilterCriteria>({
    search: "",
    category: "all",
    health: "all",
    freshness: "all",
    mode: "all",
  });

  // Modal inspection state
  const [selectedSource, setSelectedSource] = useState<DataSourceTelemetryRead | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Probe action state
  const [probingSourceId, setProbingSourceId] = useState<number | null>(null);
  const [actionSuccessNotice, setActionSuccessNotice] = useState<string | null>(null);

  // Load telemetry data
  const loadTelemetryData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [overviewData, sourcesData] = await Promise.all([
        getTelemetryOverview(),
        listDataSources(),
      ]);
      setOverview(overviewData);
      setSources(sourcesData.data || []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load operational telemetry from backend."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTelemetryData();
  }, [loadTelemetryData]);

  // Deep-linking via search param
  useEffect(() => {
    if (targetSourceId && sources.length > 0) {
      const found = sources.find(
        (s) =>
          s.source_id.toString() === targetSourceId ||
          s.provider_id === targetSourceId
      );
      if (found) {
        setSelectedSource(found);
        setIsModalOpen(true);
      }
    }
  }, [targetSourceId, sources]);

  // Handle probe action
  const handleProbe = useCallback(
    async (source: DataSourceTelemetryRead) => {
      setProbingSourceId(source.source_id);
      try {
        const probed = await probeDataSource(source.source_id);

        // Update in-memory state
        setSources((prev) =>
          prev.map((s) => (s.source_id === source.source_id ? probed : s))
        );

        if (selectedSource && selectedSource.source_id === source.source_id) {
          setSelectedSource(probed);
        }

        // Refresh overview counts
        const updatedOverview = await getTelemetryOverview();
        setOverview(updatedOverview);

        setActionSuccessNotice(
          `Successfully probed provider adapter: "${source.name}". Status: ${probed.provider_health.toUpperCase()}, Freshness: ${probed.freshness.status.toUpperCase()}.`
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : `Failed to probe provider adapter ${source.provider_id || source.source_id}.`
        );
      } finally {
        setProbingSourceId(null);
      }
    },
    [selectedSource]
  );

  // Filter sources in memory
  const filteredSources = useMemo(() => {
    return sources.filter((source) => {
      // 1. Text Search
      if (criteria.search && criteria.search.trim()) {
        const q = criteria.search.toLowerCase().trim();
        const matchesName = source.name.toLowerCase().includes(q);
        const matchesProvider = source.provider.toLowerCase().includes(q);
        const matchesProviderId =
          source.provider_id && source.provider_id.toLowerCase().includes(q);
        const matchesSourceId = source.source_id.toString() === q;
        const matchesEndpoint =
          source.endpoint_url && source.endpoint_url.toLowerCase().includes(q);

        if (
          !matchesName &&
          !matchesProvider &&
          !matchesProviderId &&
          !matchesSourceId &&
          !matchesEndpoint
        ) {
          return false;
        }
      }

      // 2. Category
      if (criteria.category && criteria.category !== "all") {
        if (source.category !== criteria.category) {
          return false;
        }
      }

      // 3. Health
      if (criteria.health && criteria.health !== "all") {
        if (source.provider_health.toLowerCase() !== criteria.health.toLowerCase()) {
          return false;
        }
      }

      // 4. Freshness
      if (criteria.freshness && criteria.freshness !== "all") {
        if (source.freshness.status.toLowerCase() !== criteria.freshness.toLowerCase()) {
          return false;
        }
      }

      // 5. Mode
      if (criteria.mode && criteria.mode !== "all") {
        if (source.provider_mode.toLowerCase() !== criteria.mode.toLowerCase()) {
          return false;
        }
      }

      return true;
    });
  }, [sources, criteria]);

  const handleResetFilters = useCallback(() => {
    setCriteria({
      search: "",
      category: "all",
      health: "all",
      freshness: "all",
      mode: "all",
    });
  }, []);

  return (
    <OperationsSectionShell
      title="Data Sources & Freshness Monitoring"
      description="Real-time provider adapter health diagnostics, deterministic 5-state temporal freshness evaluation, and automated ingestion run telemetry."
      chunkId="M6-06"
      chunkTitle="Data Sources & Freshness Monitoring UI"
      prerequisiteChunk="Chunk M3-13 (Data Source Freshness & Telemetry Backend — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={loadTelemetryData}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            <span>Refresh Diagnostics</span>
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Action Success Alert */}
        {actionSuccessNotice && (
          <Alert
            severity="success"
            title="Provider Probe Completed"
            onClose={() => setActionSuccessNotice(null)}
          >
            {actionSuccessNotice}
          </Alert>
        )}

        {/* Error Alert */}
        {error && (
          <Alert
            severity="danger"
            title="Telemetry Diagnostic Error"
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {/* 1. Overview KPI Cards */}
        <TelemetryOverviewCards overview={overview} isLoading={isLoading} />

        {/* 2. Collapsible Freshness Threshold Policies */}
        <ThresholdsReferenceCard />

        {/* 3. Search and Filtering Bar */}
        <SourceFilterBar
          criteria={criteria}
          onCriteriaChange={setCriteria}
          onReset={handleResetFilters}
          totalFiltered={filteredSources.length}
          totalAvailable={sources.length}
        />

        {/* 4. Data Sources Table */}
        <SourceTable
          sources={filteredSources}
          onSelectSource={(source) => {
            setSelectedSource(source);
            setIsModalOpen(true);
          }}
          onProbeSource={handleProbe}
          probingSourceId={probingSourceId}
          isLoading={isLoading}
        />

        {/* 5. Source Detail & Ingestion Runs Modal */}
        <SourceDetailModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedSource(null);
          }}
          source={selectedSource}
          onProbeSource={handleProbe}
          isProbing={probingSourceId === selectedSource?.source_id}
        />
      </div>
    </OperationsSectionShell>
  );
}

export default function DataSourcesOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs font-mono text-slate-400">
          Loading Data Sources & Freshness Workspace...
        </div>
      }
    >
      <DataSourcesContent />
    </Suspense>
  );
}
