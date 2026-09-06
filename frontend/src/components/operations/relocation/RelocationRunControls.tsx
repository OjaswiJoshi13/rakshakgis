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
}) => {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      {/* Top Bar: View Switcher and Primary Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* View Switcher */}
        <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeView === "matching"}
            onClick={() => onViewChange("matching")}
            className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeView === "matching"
                ? "bg-sky-600 text-white shadow-sm font-semibold"
                : "text-slate-400 hover:text-slate-200"
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
            className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              activeView === "ledger"
                ? "bg-sky-600 text-white shadow-sm font-semibold"
                : "text-slate-400 hover:text-slate-200"
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
                  leftIcon={<Save className="h-3.5 w-3.5 text-emerald-400" />}
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
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800 text-xs text-slate-300">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Sliders className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-slate-400 font-mono">Region Profile:</span>
              <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-700/50">
                himalayan_pilot (Chamoli)
              </Badge>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 font-mono">Algorithm:</span>
              <Badge variant="default" size="sm" className="font-mono text-slate-300">
                greedy_priority (M4-04)
              </Badge>
            </div>
          </div>

          {/* Data Source Selection */}
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-mono text-xs">Data Source:</span>
            <div className="inline-flex rounded border border-slate-800 bg-slate-950 p-0.5">
              <button
                type="button"
                onClick={() => onToggleDataSource(false)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  !useDatabase
                    ? "bg-slate-800 text-sky-300 font-medium"
                    : "text-slate-400 hover:text-slate-200"
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
                    ? "bg-slate-800 text-sky-300 font-medium"
                    : "text-slate-400 hover:text-slate-200"
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
