"use client";

import React from "react";
import { RelocationWorkflowView } from "@/types/relocation";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  ArrowRightLeft,
  Database,
  FileCheck2,
  ListOrdered,
  RefreshCw,
  Save,
  Sliders,
} from "lucide-react";

export interface RelocationRunControlsProps {
  activeView: RelocationWorkflowView;
  onViewChange: (view: RelocationWorkflowView) => void;
  onExecuteMatching: () => void;
  isExecuting: boolean;
  useDatabase: boolean;
  onToggleDataSource: (useDb: boolean) => void;
  onOpenCommitDialog?: () => void;
  canCommit?: boolean;
  totalAssignmentsCount?: number;
  regionProfileId?: string;
}

export const RelocationRunControls: React.FC<RelocationRunControlsProps> = ({
  activeView,
  onViewChange,
  onExecuteMatching,
  isExecuting,
  useDatabase,
  onToggleDataSource,
  onOpenCommitDialog,
  canCommit = false,
  totalAssignmentsCount = 0,
  regionProfileId = "himalayan_pilot",
}) => {
  return (
    <div className="space-y-4 rounded-lg border border-border-base bg-surface-raised p-4 shadow-2xs">
      {/* Top Bar: View Switcher and Primary Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* View Switcher */}
        <div className="inline-flex rounded-md bg-surface-base p-1 border border-border-base" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeView === "matching"}
            onClick={() => onViewChange("matching")}
            className={`inline-flex items-center gap-2 rounded px-3 py-1.5 text-xs font-medium transition-all ${
              activeView === "matching"
                ? "bg-surface-raised dark:bg-[#21262d] text-text-primary border border-border-base dark:border-[#30363d] shadow-2xs font-semibold"
                : "text-text-secondary hover:text-text-primary border border-transparent"
            }`}
          >
            <ArrowRightLeft className="h-3.5 w-3.5" />
            <span>Matching Evaluation Run</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeView === "ledger"}
            onClick={() => onViewChange("ledger")}
            className={`inline-flex items-center gap-2 rounded px-3 py-1.5 text-xs font-medium transition-all ${
              activeView === "ledger"
                ? "bg-surface-raised dark:bg-[#21262d] text-text-primary border border-border-base dark:border-[#30363d] shadow-2xs font-semibold"
                : "text-text-secondary hover:text-text-primary border border-transparent"
            }`}
          >
            <ListOrdered className="h-3.5 w-3.5" />
            <span>Persisted Assignments Ledger</span>
          </button>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex items-center gap-2">
          {activeView === "matching" && (
            <>
              {canCommit && onOpenCommitDialog && (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={onOpenCommitDialog}
                  leftIcon={<Save className="h-3.5 w-3.5 text-[#1a7f37] dark:text-[#3fb950]" />}
                >
                  <span>Commit Assignments ({totalAssignmentsCount})</span>
                </Button>
              )}

              <Button
                type="button"
                variant="primary"
                size="sm"
                isLoading={isExecuting}
                onClick={onExecuteMatching}
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              >
                <span>Execute Matching Run</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Control Parameters Bar (When in Matching View) */}
      {activeView === "matching" && (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle text-xs text-text-secondary">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Sliders className="h-3.5 w-3.5 text-text-muted" />
              <span className="text-text-muted font-mono">Region Profile:</span>
              <Badge variant="outline" size="sm" className="font-mono text-text-secondary border-border-base">
                {regionProfileId === "himalayan_pilot" ? "himalayan_pilot (Chamoli)" : regionProfileId}
              </Badge>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-text-muted font-mono">Algorithm:</span>
              <Badge variant="default" size="sm" className="font-mono text-text-secondary border-border-base">
                <span className="sr-only">greedy_priority (Greedy Priority Matching)</span>
                <span aria-hidden="true">greedy_priority</span>
              </Badge>
            </div>
          </div>

          {/* Data Source Selection */}
          <div className="flex items-center gap-2">
            <span className="text-text-muted font-mono text-xs">Data Source:</span>
            <div className="inline-flex rounded border border-border-base bg-surface-base p-0.5">
              <button
                type="button"
                onClick={() => onToggleDataSource(false)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  !useDatabase
                    ? "bg-surface-raised dark:bg-[#21262d] text-text-primary font-medium border border-border-base shadow-2xs"
                    : "text-text-muted hover:text-text-secondary border border-transparent"
                }`}
                title="Use Himalayan Pilot standard evaluation set"
              >
                Pilot Evaluation Set
              </button>
              <button
                type="button"
                onClick={() => onToggleDataSource(true)}
                className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
                  useDatabase
                    ? "bg-surface-raised dark:bg-[#21262d] text-text-primary font-medium border border-border-base shadow-2xs"
                    : "text-text-muted hover:text-text-secondary border border-transparent"
                }`}
                title="Query database prioritized villages and candidate sites"
              >
                <Database className="h-3 w-3" />
                <span>Live Database</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
