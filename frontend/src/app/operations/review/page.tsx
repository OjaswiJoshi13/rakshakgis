"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import {
  ReviewQueueCard,
  RecommendationDetailCard,
  OfficerDecisionPanel,
  DecisionStatusBanner,
} from "@/components/operations/review";
import {
  listReviewDossiers,
  submitOfficerDecision,
  resetDossierDecision,
  INITIAL_REVIEW_DOSSIERS,
} from "@/lib/api/review";
import {
  RecommendationDossier,
  SubmitDecisionRequest,
} from "@/types/review";
import { useAuth } from "@/context/AuthContext";
import {
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  FileCheck2,
} from "lucide-react";

function ReviewOperationsContent() {
  const searchParams = useSearchParams();
  const initialDossierId = searchParams.get("dossierId");
  const { user } = useAuth();

  const [dossiers, setDossiers] = useState<RecommendationDossier[]>(INITIAL_REVIEW_DOSSIERS);
  const [selectedDossierId, setSelectedDossierId] = useState<string>(
    initialDossierId || INITIAL_REVIEW_DOSSIERS[0]?.id || ""
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isReopening, setIsReopening] = useState<boolean>(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // Fetch review dossiers
  const loadDossiers = useCallback(async () => {
    setIsLoading(true);
    try {
      const items = await listReviewDossiers();
      setDossiers(items);
      if (items.length > 0) {
        setSelectedDossierId((prev) => {
          if (prev && items.some((i) => i.id === prev)) return prev;
          if (initialDossierId && items.some((i) => i.id === initialDossierId)) return initialDossierId;
          return items[0].id;
        });
      }
    } catch {
      setNotification({
        type: "error",
        message: "Failed to load recommendation dossiers. Please refresh.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [initialDossierId]);

  useEffect(() => {
    loadDossiers();
  }, [loadDossiers]);

  const selectedDossier = dossiers.find((d) => d.id === selectedDossierId) || dossiers[0];

  // Handle officer decision submission
  const handleSubmitDecision = async (request: SubmitDecisionRequest) => {
    setIsSubmitting(true);
    try {
      const officerInfo = {
        id: user?.id || "OFFICER-001",
        name: user?.full_name || user?.username || "District Disaster Officer",
        role: user?.role === "admin" ? "District Collector & Magistrate (DM)" : "District Disaster Management Officer (DDMO)",
        department: "Department of Disaster Management, Chamoli",
      };

      const result = await submitOfficerDecision(request, officerInfo);

      // Update local dossiers state with new status & decision record
      setDossiers((prev) =>
        prev.map((d) => (d.id === result.dossier.id ? result.dossier : d))
      );

      setNotification({
        type: "success",
        message: result.message,
      });
    } catch (err) {
      setNotification({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to record decision.",
      });
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  // Re-open / Re-evaluate a decided recommendation
  const handleReopenDecision = async () => {
    if (!selectedDossier) return;
    setIsReopening(true);
    try {
      const result = await resetDossierDecision(selectedDossier.id);
      setDossiers((prev) =>
        prev.map((d) => (d.id === result.dossier.id ? result.dossier : d))
      );
      setNotification({
        type: "success",
        message: `Recommendation '${selectedDossier.title}' reopened for re-evaluation.`,
      });
    } catch (err) {
      setNotification({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to reopen recommendation.",
      });
    } finally {
      setIsReopening(false);
    }
  };

  const pendingCount = dossiers.filter((d) => d.status === "pending_review").length;
  const approvedCount = dossiers.filter((d) => d.status === "approved").length;

  return (
    <OperationsSectionShell
      title="Officer Review & Sign-Off"
      description="Statutory Rule 12 verification gateway: inspect AI-recommended relocation allocations and scenario simulations, verify local ground conditions, and record binding administrative decisions before operational dispatch."
      chunkId="M6-08"
      chunkTitle="Officer Review & Action Sign-Off Workflow"
      prerequisiteChunk="Chunk M6-02 & M6-04 (Relocation & Scenario Workflows — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={loadDossiers}
            isLoading={isLoading}
            disabled={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            <span>Refresh Queue</span>
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Officer Authority Header Badge */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border-base bg-surface-raised px-3.5 py-2.5 text-xs text-text-secondary font-mono shadow-2xs">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[#1a7f37] dark:text-[#3fb950] shrink-0" />
            <span>
              Authority Level:{" "}
              <strong className="text-text-primary">
                {user?.role === "admin" ? "State / District Magistrate" : "District Disaster Officer"}
              </strong>{" "}
              ({user?.full_name || user?.username || "Officer Session Active"})
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-amber-800 dark:text-amber-300 font-medium">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              <span>{pendingCount} Pending Sign-Off</span>
            </div>
            <span className="text-border-base">|</span>
            <div className="flex items-center gap-1.5 text-[#1a7f37] dark:text-[#3fb950] font-medium">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>{approvedCount} Enacted</span>
            </div>
          </div>
        </div>

        {/* Dismissible Feedback Notification */}
        {notification && (
          <Alert
            severity={notification.type === "success" ? "success" : "danger"}
            title={notification.type === "success" ? "Action Recorded" : "Validation / Service Error"}
          >
            <div className="flex items-center justify-between gap-2">
              <span>{notification.message}</span>
              <button
                type="button"
                onClick={() => setNotification(null)}
                className="text-xs underline font-mono ml-4 hover:opacity-80"
              >
                Dismiss
              </button>
            </div>
          </Alert>
        )}

        {/* 2-Column Responsive Operational Workspace */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
          {/* Left Column: Review Queue (col-span-4) */}
          <div className="lg:col-span-4">
            <ReviewQueueCard
              dossiers={dossiers}
              selectedDossierId={selectedDossier?.id || ""}
              onSelectDossier={(id) => {
                setSelectedDossierId(id);
                setNotification(null);
              }}
              isLoading={isLoading}
            />
          </div>

          {/* Right Column: Selected Dossier Inspector & Decision Form (col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            {selectedDossier ? (
              <>
                {/* Dossier Detail View */}
                <RecommendationDetailCard dossier={selectedDossier} />

                {/* If already decided, show official Decision Status Banner */}
                {selectedDossier.decision && (
                  <DecisionStatusBanner
                    decision={selectedDossier.decision}
                    onReopenDecision={handleReopenDecision}
                    isReopening={isReopening}
                  />
                )}

                {/* Interactive Decision Form Panel (always accessible for pending, or reopened) */}
                {selectedDossier.status === "pending_review" && (
                  <OfficerDecisionPanel
                    dossier={selectedDossier}
                    onSubmitDecision={handleSubmitDecision}
                    isSubmitting={isSubmitting}
                    officerName={user?.full_name || user?.username || "District Disaster Officer"}
                    officerRole={
                      user?.role === "admin"
                        ? "District Collector & District Magistrate"
                        : "District Disaster Management Officer"
                    }
                  />
                )}
              </>
            ) : (
              <div className="rounded-lg border border-dashed border-border-base p-12 text-center text-xs text-text-muted">
                <FileCheck2 className="h-8 w-8 mx-auto text-text-muted mb-3" />
                <p>Select a recommendation dossier from the queue to begin officer review.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </OperationsSectionShell>
  );
}

export default function ReviewOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs text-slate-400 font-mono">
          Loading officer review workspace...
        </div>
      }
    >
      <ReviewOperationsContent />
    </Suspense>
  );
}
