"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  ScenarioConfigPanel,
  ScenarioComparisonSummary,
  ScenarioDeltaTabs,
} from "@/components/operations/scenarios";
import {
  listScenarioDefinitions,
  runScenarioSimulation,
  CANONICAL_SCENARIO_CATALOG,
  HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS,
} from "@/lib/api/scenarios";
import {
  ScenarioDefinitionRead,
  ScenarioParameters,
  ScenarioSimulationOutput,
  ScenarioType,
} from "@/types/scenarios";
import { Sliders, RotateCcw, AlertCircle, RefreshCw } from "lucide-react";

function ScenariosOperationsContent() {
  const searchParams = useSearchParams();
  const initialTypeParam = searchParams.get("scenario")?.toUpperCase() as ScenarioType | null;

  const [catalog, setCatalog] = useState<ScenarioDefinitionRead[]>(
    CANONICAL_SCENARIO_CATALOG
  );
  const [selectedScenarioType, setSelectedScenarioType] = useState<ScenarioType>(
    initialTypeParam && ["NORMAL", "EXTREME_RAINFALL", "FLASH_FLOOD", "CAPACITY_CRISIS"].includes(initialTypeParam)
      ? initialTypeParam
      : "EXTREME_RAINFALL"
  );
  const [parameters, setParameters] = useState<ScenarioParameters>(() => {
    const defaultDef =
      CANONICAL_SCENARIO_CATALOG.find((s) => s.scenario_type === (initialTypeParam || "EXTREME_RAINFALL")) ||
      CANONICAL_SCENARIO_CATALOG[1];
    return { ...defaultDef.default_parameters };
  });

  const [simulationOutput, setSimulationOutput] =
    useState<ScenarioSimulationOutput | null>(() => {
      return (
        HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[
          initialTypeParam || "EXTREME_RAINFALL"
        ] || HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.EXTREME_RAINFALL
      );
    });

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load catalog definitions
  useEffect(() => {
    async function loadCatalog() {
      try {
        const resp = await listScenarioDefinitions();
        if (resp.success && resp.data && resp.data.length > 0) {
          setCatalog(resp.data);
        }
      } catch {
        // Keeps default CANONICAL_SCENARIO_CATALOG
      }
    }
    loadCatalog();
  }, []);

  // Handle switching preset scenario
  const handleSelectScenarioType = (type: ScenarioType) => {
    setSelectedScenarioType(type);
    const def = catalog.find((s) => s.scenario_type === type);
    if (def) {
      setParameters({ ...def.default_parameters });
    }
    // Update simulation output preview immediately for canonical presets
    if (HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[type]) {
      setSimulationOutput(HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[type]);
    }
  };

  // Handle resetting parameters to canonical defaults
  const handleResetDefaults = () => {
    const def = catalog.find((s) => s.scenario_type === selectedScenarioType);
    if (def) {
      setParameters({ ...def.default_parameters });
    }
  };

  // Execute simulation run
  const handleRunSimulation = useCallback(async () => {
    setIsRunning(true);
    setError(null);
    try {
      const resp = await runScenarioSimulation({
        scenario_type: selectedScenarioType,
        region_profile_id: "himalayan_pilot",
        parameters,
      });
      if (resp.success && resp.data) {
        setSimulationOutput(resp.data);
      } else {
        setError("Simulation execution failed.");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to communicate with scenario simulator backend.");
      // Fallback
      if (HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[selectedScenarioType]) {
        setSimulationOutput(
          HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[selectedScenarioType]
        );
      }
    } finally {
      setIsRunning(false);
    }
  }, [selectedScenarioType, parameters]);

  return (
    <OperationsSectionShell
      title="Scenario Simulator"
      description="Deterministic parameter perturbation for disaster scenario exploration: simulate extreme rainfall spikes, flash floods, and site capacity contractions to evaluate cascading relocation and routing impacts."
      chunkId="M6-04"
      chunkTitle="Scenario Simulator UI"
      prerequisiteChunk="Chunk M6-01 (Operations Shell) & M4-06 (Scenario Simulator Integration — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleResetDefaults}
            leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
          >
            <span>Reset Parameters</span>
          </Button>

          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={handleRunSimulation}
            isLoading={isRunning}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            <span>Re-run Simulation</span>
          </Button>
        </div>
      }
    >
      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/30 p-3 text-xs text-rose-200 flex items-center gap-2 font-mono">
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Left Column: Configuration & Parameter Sliders */}
        <div className="lg:col-span-4">
          <ScenarioConfigPanel
            catalog={catalog}
            selectedScenarioType={selectedScenarioType}
            onSelectScenarioType={handleSelectScenarioType}
            parameters={parameters}
            onChangeParameters={setParameters}
            onResetDefaults={handleResetDefaults}
            onRunSimulation={handleRunSimulation}
            isRunning={isRunning}
          />
        </div>

        {/* Right Column: Comparison KPIs & Domain Impact Tabs */}
        <div className="lg:col-span-8 space-y-6">
          {simulationOutput ? (
            <>
              {/* Delta Comparison Summary Cards & Narrative */}
              <ScenarioComparisonSummary simulationOutput={simulationOutput} />

              {/* Domain Impact Tabs (Risk, Relocation, Routing) */}
              <ScenarioDeltaTabs simulationOutput={simulationOutput} />
            </>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-800 p-12 text-center text-xs text-slate-400 font-mono">
              <Sliders className="h-8 w-8 mx-auto text-slate-600 mb-3" />
              <p>Configure scenario parameters and execute a simulation to inspect before-vs-after delta impacts.</p>
            </div>
          )}
        </div>
      </div>
    </OperationsSectionShell>
  );
}

export default function ScenariosOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs text-slate-400 font-mono">
          Loading scenario simulator workspace...
        </div>
      }
    >
      <ScenariosOperationsContent />
    </Suspense>
  );
}
