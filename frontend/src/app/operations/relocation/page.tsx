"use client";

import React, { useState, useCallback, useEffect } from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import {
  RelocationMatchingResult,
  RelocationWorkflowView,
  VillageAssignmentResult,
} from "@/types/relocation";
import {
  evaluateRelocationMatching,
  HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT,
} from "@/lib/api/relocation";
import {
  RelocationSummaryCards,
  RelocationRunControls,
  RelocationAssignmentTable,
  CandidateAuditModal,
  RelocationLedgerView,
  BatchCommitModal,
} from "@/components/operations/relocation";
import { Button } from "@/components/ui/Button";
import { CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";

export default function RelocationOperationsPage({
  defaultUseDatabase = true,
}: any) {
  const [activeView, setActiveView] = useState<RelocationWorkflowView>("matching");
  const [useDatabase, setUseDatabase] = useState<boolean>(defaultUseDatabase);
  const [matchingResult, setMatchingResult] = useState<RelocationMatchingResult | null>(
    defaultUseDatabase ? null : HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT
  );
  const [isExecuting, setIsExecuting] = useState<boolean>(defaultUseDatabase);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedAudit, setSelectedAudit] =
    useState<VillageAssignmentResult | null>(null);
  const [isCommitModalOpen, setIsCommitModalOpen] = useState<boolean>(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const handleExecuteMatching = useCallback(async (overrideUseDb?: boolean) => {
    setIsExecuting(true);
    setSuccessBanner(null);
    setErrorMessage(null);

    const useDb = overrideUseDb !== undefined ? overrideUseDb : useDatabase;

    if (!useDb) {
      setMatchingResult(HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT);
      setIsExecuting(false);
      return;
    }

    try {
      const response = await evaluateRelocationMatching({
        use_database_villages: true,
        use_database_sites: true,
        region_profile_id: "himalayan_pilot",
      });

      if (response && response.data && response.data.assignments) {
        setMatchingResult(response.data);
      } else {
        setErrorMessage("Failed to load relocation matching results from operational database.");
      }
    } catch (err: any) {
      setErrorMessage(
        err?.message || "Failed to query database relocation matching endpoint."
      );
    } finally {
      setIsExecuting(false);
    }
  }, [useDatabase]);

  useEffect(() => {
    if (defaultUseDatabase) {
      handleExecuteMatching(true);
    }
  }, [defaultUseDatabase, handleExecuteMatching]);

  const handleToggleDataSource = (useDb: boolean) => {
    setUseDatabase(useDb);
    handleExecuteMatching(useDb);
  };

  const handleCommitSuccess = (count: number) => {
    setSuccessBanner(
      `Successfully persisted ${count} relocation assignment${
        count === 1 ? "" : "s"
      } into the operational database ledger.`
    );
    // Auto-dismiss banner after 6 seconds
    setTimeout(() => {
      setSuccessBanner(null);
    }, 6000);
  };

  return (
    <OperationsSectionShell
      title="Relocation Planner"
      description="Deterministic multi-village to candidate relocation site matching, capacity constraint auditing, and assignment ledger management."
      chunkId="M6-02"
      chunkTitle="Relocation Planner Workflow UI"
      prerequisiteChunk="Chunk M4-04 (Relocation Matching Engine — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          {activeView === "matching" && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => handleExecuteMatching()}
              isLoading={isExecuting}
              leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            >
              <span>Re-run Matching</span>
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* Run Controls & Mode Switcher */}
        <RelocationRunControls
          activeView={activeView}
          onViewChange={setActiveView}
          onExecuteMatching={() => handleExecuteMatching()}
          isExecuting={isExecuting}
          useDatabase={useDatabase}
          onToggleDataSource={handleToggleDataSource}
          onOpenCommitDialog={() => setIsCommitModalOpen(true)}
          canCommit={Boolean(
            matchingResult &&
              matchingResult.assignments.some((a) => a.status === "assigned")
          )}
          totalAssignmentsCount={
            matchingResult?.assignments.filter((a) => a.status === "assigned")
              .length || 0
          }
        />

        {/* Persistence Success Banner */}
        {successBanner && (
          <div className="flex items-center gap-2 rounded-lg border border-emerald-600 bg-emerald-950/60 p-3.5 text-xs text-emerald-200">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>{successBanner}</span>
          </div>
        )}

        {/* Error Banner */}
        {errorMessage && (
          <div className="flex items-center gap-2 rounded-lg border border-red-600 bg-red-950/60 p-3.5 text-xs text-red-200">
            <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Loading Indicator */}
        {isExecuting && !matchingResult && (
          <div className="flex flex-col items-center justify-center p-12 text-center text-xs text-text-muted border border-border-base rounded-lg bg-surface-raised">
            <RefreshCw className="h-6 w-6 animate-spin mb-3 text-text-secondary" />
            <span>Executing deterministic relocation matching against live database...</span>
          </div>
        )}

        {/* Matching Evaluation View */}
        {activeView === "matching" && matchingResult && (
          <div className="space-y-6">
            {/* KPI Metric Summary & Rule 12 Protocol */}
            <RelocationSummaryCards result={matchingResult} />

            {/* Assignments Matrix & Explainability Table */}
            <RelocationAssignmentTable
              assignments={matchingResult.assignments}
              onInspectAudit={(assignment) => setSelectedAudit(assignment)}
            />
          </div>
        )}

        {/* Persisted Assignments Ledger View */}
        {activeView === "ledger" && <RelocationLedgerView />}

        {/* Candidate Evaluation Explainability Modal */}
        <CandidateAuditModal
          assignment={selectedAudit}
          onClose={() => setSelectedAudit(null)}
        />

        {/* Batch Persist Confirmation Modal */}
        {matchingResult && (
          <BatchCommitModal
            assignments={matchingResult.assignments}
            isOpen={isCommitModalOpen}
            onClose={() => setIsCommitModalOpen(false)}
            onSuccess={handleCommitSuccess}
          />
        )}
      </div>
    </OperationsSectionShell>
  );
}
