"use client";

import React from "react";
import {
  ScenarioDefinitionRead,
  ScenarioParameters,
  ScenarioType,
} from "@/types/scenarios";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  Sliders,
  CloudRain,
  Waves,
  Building2,
  Activity,
  RotateCcw,
  Play,
  Layers,
} from "lucide-react";

export interface ScenarioConfigPanelProps {
  catalog: ScenarioDefinitionRead[];
  selectedScenarioType: ScenarioType;
  onSelectScenarioType: (type: ScenarioType) => void;
  parameters: ScenarioParameters;
  onChangeParameters: (params: ScenarioParameters) => void;
  onResetDefaults: () => void;
  onRunSimulation: () => void;
  isRunning: boolean;
}

export const ScenarioConfigPanel: React.FC<ScenarioConfigPanelProps> = ({
  catalog,
  selectedScenarioType,
  onSelectScenarioType,
  parameters,
  onChangeParameters,
  onResetDefaults,
  onRunSimulation,
  isRunning,
}) => {
  const getScenarioIcon = (type: string) => {
    switch (type) {
      case "EXTREME_RAINFALL":
        return <CloudRain className="h-4 w-4 text-amber-400" />;
      case "FLASH_FLOOD":
        return <Waves className="h-4 w-4 text-cyan-400" />;
      case "CAPACITY_CRISIS":
        return <Building2 className="h-4 w-4 text-rose-400" />;
      default:
        return <Activity className="h-4 w-4 text-sky-400" />;
    }
  };

  const updateParam = <K extends keyof ScenarioParameters>(
    key: K,
    value: ScenarioParameters[K]
  ) => {
    onChangeParameters({
      ...parameters,
      [key]: value,
      scenario_type:
        selectedScenarioType === "NORMAL" && key !== "scenario_type"
          ? "CUSTOM"
          : parameters.scenario_type,
    });
  };

  return (
    <div className="space-y-4 rounded-lg border border-border-subtle bg-surface-panel p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          <h3 className="text-xs font-mono uppercase tracking-wider text-text-primary font-semibold">
            Scenario Configuration
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="text-[10px] font-mono border-border-subtle text-text-muted">
          Simulation Engine
          <span className="sr-only">M4-06 Engine</span>
        </Badge>
      </div>

      {/* Scenario Presets */}
      <div>
        <label className="block text-[11px] font-mono text-text-muted uppercase tracking-wide mb-2">
          Canonical Presets
        </label>
        <div className="grid grid-cols-1 gap-2">
          {catalog.map((sc) => {
            const isSelected = selectedScenarioType === sc.scenario_type;
            return (
              <button
                key={sc.scenario_type}
                type="button"
                onClick={() => onSelectScenarioType(sc.scenario_type as ScenarioType)}
                className={`w-full text-left rounded-lg p-2.5 transition-all border ${
                  isSelected
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-950/40 shadow-xs ring-1 ring-primary-500 text-text-primary"
                    : "border-border-subtle bg-surface-elevated hover:bg-surface-raised hover:border-border-strong text-text-secondary"
                }`}
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <div className="flex items-center gap-2">
                    {getScenarioIcon(sc.scenario_type)}
                    <span className="font-semibold text-xs text-text-primary">
                      {sc.name}
                    </span>
                  </div>
                  {isSelected && (
                    <Badge variant="success" size="sm" className="text-[9px] py-0">
                      Active
                    </Badge>
                  )}
                </div>
                <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed">
                  {sc.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Parameter Controls */}
      <div className="space-y-3.5 pt-2 border-t border-border-subtle">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono text-text-muted uppercase tracking-wide">
            Perturbation Parameters
          </span>
          <button
            type="button"
            onClick={onResetDefaults}
            className="inline-flex items-center gap-1 text-[11px] font-mono text-text-muted hover:text-text-primary transition-colors cursor-pointer"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reset Defaults</span>
          </button>
        </div>

        {/* Rainfall Multiplier Slider */}
        <div className="space-y-1 rounded bg-surface-elevated p-2.5 border border-border-subtle">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-primary flex items-center gap-1.5">
              <CloudRain className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              <span>Rainfall Multiplier</span>
            </span>
            <span className="font-bold text-amber-700 dark:text-amber-400">
              {(parameters.rainfall_multiplier ?? 1.0).toFixed(2)}x
            </span>
          </div>
          <p className="text-[10px] text-text-muted font-mono leading-tight">
            Simulation parameter: Deterministic rainfall perturbation (not an observed weather measurement)
          </p>
          <input
            type="range"
            min="1.0"
            max="2.5"
            step="0.05"
            value={parameters.rainfall_multiplier ?? 1.0}
            onChange={(e) =>
              updateParam("rainfall_multiplier", parseFloat(e.target.value))
            }
            className="w-full accent-amber-600 dark:accent-amber-500 cursor-pointer h-1.5 bg-surface-panel rounded-lg"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>1.0x (Normal)</span>
            <span>1.4x (Cloudburst)</span>
            <span>2.5x (Catastrophic)</span>
          </div>
        </div>

        {/* Road Blockage Percentage Slider */}
        <div className="space-y-1 rounded bg-surface-elevated p-2.5 border border-border-subtle">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-primary flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400" />
              <span>Road Network Blockage</span>
            </span>
            <span className="font-bold text-cyan-700 dark:text-cyan-400">
              {(parameters.road_blockage_percentage ?? 0).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={parameters.road_blockage_percentage ?? 0}
            onChange={(e) =>
              updateParam("road_blockage_percentage", parseFloat(e.target.value))
            }
            className="w-full accent-cyan-600 dark:accent-cyan-500 cursor-pointer h-1.5 bg-surface-panel rounded-lg"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>0% (Open)</span>
            <span>15% (Flash Flood)</span>
            <span>50%+ (Severe Cutoff)</span>
          </div>
        </div>

        {/* Site Capacity Reduction Percentage Slider */}
        <div className="space-y-1 rounded bg-surface-elevated p-2.5 border border-border-subtle">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-primary flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
              <span>Site Capacity Reduction</span>
            </span>
            <span className="font-bold text-rose-700 dark:text-rose-400">
              {(parameters.capacity_reduction_percentage ?? 0).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={parameters.capacity_reduction_percentage ?? 0}
            onChange={(e) =>
              updateParam("capacity_reduction_percentage", parseFloat(e.target.value))
            }
            className="w-full accent-rose-600 dark:accent-rose-500 cursor-pointer h-1.5 bg-surface-panel rounded-lg"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>0% (Full Slots)</span>
            <span>50% (Crisis Strain)</span>
            <span>100% (Total Deficit)</span>
          </div>
        </div>

        {/* Flood Hazard Increase Slider */}
        <div className="space-y-1 rounded bg-surface-elevated p-2.5 border border-border-subtle">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-primary flex items-center gap-1.5">
              <Waves className="h-3.5 w-3.5 text-primary-600 dark:text-sky-400" />
              <span>Flood Hazard Increase</span>
            </span>
            <span className="font-bold text-primary-700 dark:text-sky-400">
              +{(parameters.flood_hazard_increase ?? 0).toFixed(0)} pts
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="50"
            step="5"
            value={parameters.flood_hazard_increase ?? 0}
            onChange={(e) =>
              updateParam("flood_hazard_increase", parseFloat(e.target.value))
            }
            className="w-full accent-primary-600 dark:accent-sky-500 cursor-pointer h-1.5 bg-surface-panel rounded-lg"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>+0 pts</span>
            <span>+25 pts (GLOF)</span>
            <span>+50 pts (Inundation)</span>
          </div>
        </div>
      </div>

      {/* Primary Execution Button */}
      <div className="pt-2">
        <Button
          type="button"
          variant="primary"
          size="md"
          className="w-full font-mono text-xs uppercase tracking-wider"
          onClick={onRunSimulation}
          isLoading={isRunning}
          leftIcon={<Play className="h-3.5 w-3.5 fill-current" />}
        >
          <span>{isRunning ? "Simulating Pipeline..." : "Execute Simulation"}</span>
        </Button>
      </div>
    </div>
  );
};
