"use client";

import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ScenarioDefinitionRead } from "@/types/dashboard";

export interface ScenarioReadinessCardProps {
  scenarios?: ScenarioDefinitionRead[] | null;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string | null;
}

export const ScenarioReadinessCard: React.FC<ScenarioReadinessCardProps> = ({
  scenarios,
  isLoading = false,
  isError = false,
  errorMessage,
}) => {
  return (
    <Card variant="elevated" className="space-y-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Contingency & Scenario Models</CardTitle>
            <CardDescription>
              Pre-configured multi-hazard simulation parameters for stress-testing carrying capacity and evacuation access.
            </CardDescription>
          </div>
          <span className="text-xs font-mono font-medium text-text-secondary bg-surface-elevated border border-border-subtle px-2 py-1 rounded">
            {scenarios?.length || 0} Models Registered
          </span>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="py-8 text-center text-text-muted font-mono text-sm animate-pulse">
            Loading scenario catalog...
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-600 dark:text-red-400">
            <div className="font-semibold mb-1">Failed to Load Scenarios</div>
            <p className="text-xs text-red-600/80 dark:text-red-400/80">
              {errorMessage || "Unable to retrieve scenarios from backend."}
            </p>
          </div>
        ) : !scenarios || scenarios.length === 0 ? (
          <div className="py-8 text-center text-text-muted text-sm font-mono">
            No scenario contingency pipelines available.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {scenarios.map((sc) => (
              <div
                key={sc.scenario_type}
                className="rounded-lg border border-border-subtle bg-surface-elevated/70 p-3 space-y-2 flex flex-col justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text-primary text-sm">{sc.name}</span>
                    <Badge variant="outline" size="sm" className="font-mono text-[10px]">
                      {sc.scenario_type}
                    </Badge>
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">{sc.description}</p>
                </div>

                <div className="pt-2 border-t border-border-subtle flex items-center justify-between text-[11px] font-mono text-text-muted">
                  <span>
                    Rain: <strong className="text-text-secondary">{sc.default_parameters?.rainfall_multiplier ?? 1}x</strong>
                  </span>
                  <span>
                    Blockage: <strong className="text-text-secondary">{sc.default_parameters?.road_blockage_percentage ?? 0}%</strong>
                  </span>
                  {sc.is_canonical && (
                    <span className="text-sky-600 dark:text-sky-400 text-[10px] bg-sky-500/10 border border-sky-500/20 px-1.5 py-0.5 rounded">
                      Canonical
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
