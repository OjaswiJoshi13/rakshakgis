"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  OfficerDecisionAction,
  RecommendationDossier,
  SubmitDecisionRequest,
} from "@/types/review";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  ShieldCheck,
  UserCheck,
  AlertTriangle,
  FileEdit,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface OfficerDecisionPanelProps {
  dossier: RecommendationDossier;
  onSubmitDecision: (request: SubmitDecisionRequest) => Promise<void>;
  isSubmitting: boolean;
  officerName?: string;
  officerRole?: string;
}

export const OfficerDecisionPanel: React.FC<OfficerDecisionPanelProps> = ({
  dossier,
  onSubmitDecision,
  isSubmitting,
  officerName = "District Disaster Officer",
  officerRole = "District Disaster Management Authority (DDMA)",
}) => {
  const [selectedAction, setSelectedAction] = useState<OfficerDecisionAction>("approved");
  const [rationale, setRationale] = useState("");
  const [statutoryConfirmed, setStatutoryConfirmed] = useState(false);
  const [overrideAi, setOverrideAi] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const trimmedRationale = rationale.trim();

    // Validation 1: Reject requires rationale
    if (selectedAction === "rejected" && !trimmedRationale) {
      setValidationError("Official rationale is mandatory when rejecting an operational recommendation.");
      return;
    }

    // Validation 2: Return for revision requires rationale
    if (selectedAction === "revision_requested" && !trimmedRationale) {
      setValidationError("Specific revision instructions are mandatory when returning a recommendation for revision.");
      return;
    }

    // Validation 3: Approve requires statutory confirmation
    if (selectedAction === "approved" && !statutoryConfirmed) {
      setValidationError("You must confirm the statutory Rule 12 verification checkbox before approving.");
      return;
    }

    try {
      await onSubmitDecision({
        recommendation_id: dossier.id,
        action: selectedAction,
        rationale: trimmedRationale,
        confirm_statutory_verification: statutoryConfirmed,
        override_ai_recommendation: overrideAi,
      });
      // Clear form on success
      setRationale("");
      setStatutoryConfirmed(false);
      setOverrideAi(false);
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : "Failed to record decision.");
    }
  };

  return (
    <Card className="border-slate-800 bg-slate-900/70 shadow-xl overflow-hidden">
      <CardHeader className="p-4 sm:p-5 border-b border-slate-800/80 bg-slate-950/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-950/80 border border-emerald-600/50 text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm sm:text-base font-bold text-slate-100">
                Officer Action & Statutory Endorsement
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Rule 12 Legal Decision Gateway
              </CardDescription>
            </div>
          </div>

          {/* Reviewing Officer Identity */}
          <div className="flex items-center gap-2 rounded-md bg-slate-950 px-3 py-1.5 border border-slate-800">
            <UserCheck className="h-3.5 w-3.5 text-sky-400 shrink-0" />
            <div className="text-[11px] leading-tight font-mono">
              <span className="font-semibold text-slate-200">{officerName}</span>
              <span className="text-slate-500 block text-[10px]">{officerRole}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-5">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Action Choice Buttons */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
              1. Select Binding Operational Decision <span className="text-rose-400">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {/* Approve Button */}
              <button
                type="button"
                onClick={() => {
                  setSelectedAction("approved");
                  setValidationError(null);
                }}
                disabled={isSubmitting}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all flex items-start gap-2.5",
                  selectedAction === "approved"
                    ? "bg-emerald-950/60 border-emerald-500 text-emerald-100 shadow-md shadow-emerald-950/60 ring-1 ring-emerald-500"
                    : "bg-slate-950/50 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60"
                )}
              >
                <div
                  className={cn(
                    "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border",
                    selectedAction === "approved"
                      ? "border-emerald-400 bg-emerald-500 text-white"
                      : "border-slate-600"
                  )}
                >
                  {selectedAction === "approved" && <CheckCircle2 className="h-3 w-3" />}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-100 flex items-center gap-1">
                    <span>Approve Action</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                    Enact operational plan under Rule 12 protocol.
                  </div>
                </div>
              </button>

              {/* Reject Button */}
              <button
                type="button"
                onClick={() => {
                  setSelectedAction("rejected");
                  setValidationError(null);
                }}
                disabled={isSubmitting}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all flex items-start gap-2.5",
                  selectedAction === "rejected"
                    ? "bg-rose-950/60 border-rose-500 text-rose-100 shadow-md shadow-rose-950/60 ring-1 ring-rose-500"
                    : "bg-slate-950/50 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60"
                )}
              >
                <div
                  className={cn(
                    "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border",
                    selectedAction === "rejected"
                      ? "border-rose-400 bg-rose-500 text-white"
                      : "border-slate-600"
                  )}
                >
                  {selectedAction === "rejected" && <XCircle className="h-3 w-3" />}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-100 flex items-center gap-1">
                    <span>Reject Action</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                    Prohibit operational execution; requires justification.
                  </div>
                </div>
              </button>

              {/* Return for Revision Button */}
              <button
                type="button"
                onClick={() => {
                  setSelectedAction("revision_requested");
                  setValidationError(null);
                }}
                disabled={isSubmitting}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all flex items-start gap-2.5",
                  selectedAction === "revision_requested"
                    ? "bg-sky-950/60 border-sky-500 text-sky-100 shadow-md shadow-sky-950/60 ring-1 ring-sky-500"
                    : "bg-slate-950/50 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60"
                )}
              >
                <div
                  className={cn(
                    "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border",
                    selectedAction === "revision_requested"
                      ? "border-sky-400 bg-sky-500 text-white"
                      : "border-slate-600"
                  )}
                >
                  {selectedAction === "revision_requested" && <RotateCcw className="h-3 w-3" />}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-100 flex items-center gap-1">
                    <span>Return for Revision</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                    Instruct technical team to recalibrate model.
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Rationale Textarea */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label
                htmlFor="officer-rationale-input"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono"
              >
                2.{" "}
                {selectedAction === "rejected"
                  ? "Official Justification for Rejection *"
                  : selectedAction === "revision_requested"
                  ? "Specific Revision Instructions *"
                  : "Administrative Directives / Notes (Optional)"}
              </label>
              {(selectedAction === "rejected" || selectedAction === "revision_requested") && (
                <Badge variant="danger" size="sm" className="text-[10px] font-mono">
                  Mandatory Field
                </Badge>
              )}
            </div>

            <textarea
              id="officer-rationale-input"
              rows={3}
              placeholder={
                selectedAction === "rejected"
                  ? "Provide mandatory factual and legal rationale for rejecting this recommendation (e.g. recent slope failure near proposed safe site, ground verification failure)..."
                  : selectedAction === "revision_requested"
                  ? "Provide specific technical instructions for re-running the model (e.g. evaluate alternate route bypassing NH-58, include Tapovan buffer zone)..."
                  : "Optional administrative directives, ground deployment notes, or resource dispatch instructions..."
              }
              value={rationale}
              onChange={(e) => {
                setRationale(e.target.value);
                if (validationError) setValidationError(null);
              }}
              disabled={isSubmitting}
              className={cn(
                "w-full rounded-lg border bg-slate-950 p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1",
                validationError && !rationale.trim() && (selectedAction === "rejected" || selectedAction === "revision_requested")
                  ? "border-rose-500 focus:ring-rose-500"
                  : "border-slate-800 focus:border-sky-500 focus:ring-sky-500"
              )}
            />
          </div>

          {/* Additional Options */}
          <div className="space-y-3 pt-1 border-t border-slate-800/60">
            {/* Approval: Statutory Confirmation Checkbox */}
            {selectedAction === "approved" && (
              <label className="flex items-start gap-2.5 cursor-pointer rounded-lg border border-emerald-900/60 bg-emerald-950/20 p-3 text-xs text-emerald-200">
                <input
                  type="checkbox"
                  checked={statutoryConfirmed}
                  onChange={(e) => {
                    setStatutoryConfirmed(e.target.checked);
                    if (validationError) setValidationError(null);
                  }}
                  disabled={isSubmitting}
                  className="mt-0.5 h-4 w-4 rounded border-emerald-700 bg-slate-950 text-emerald-500 focus:ring-emerald-400"
                />
                <div className="leading-snug">
                  <span className="font-semibold text-emerald-300">
                    Rule 12 Ground Verification Certification (Required):
                  </span>{" "}
                  I hereby certify as an authorized officer that I have verified local terrain,
                  habitation safety, and physical ground conditions under Rule 12 protocol, and
                  officially authorize this operational action.
                </div>
              </label>
            )}

            {/* Override AI Recommendation Checkbox */}
            <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-400 hover:text-slate-300">
              <input
                type="checkbox"
                checked={overrideAi}
                onChange={(e) => setOverrideAi(e.target.checked)}
                disabled={isSubmitting}
                className="h-3.5 w-3.5 rounded border-slate-700 bg-slate-950 text-amber-500 focus:ring-amber-400"
              />
              <span className="font-mono text-[11px]">
                Record as an explicit Officer Override of automated AI algorithmic recommendation
              </span>
            </label>
          </div>

          {/* Validation Error Banner */}
          {validationError && (
            <div className="rounded-md border border-rose-900/80 bg-rose-950/50 p-3 text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="submit"
              size="md"
              isLoading={isSubmitting}
              disabled={isSubmitting}
              leftIcon={<Send className="h-4 w-4" />}
              variant={
                selectedAction === "approved"
                  ? "primary"
                  : selectedAction === "rejected"
                  ? "danger"
                  : "secondary"
              }
              className={cn(
                "min-w-[200px] text-xs font-semibold uppercase tracking-wider font-mono",
                selectedAction === "approved" && "bg-emerald-600 hover:bg-emerald-500 border-emerald-500 text-white"
              )}
            >
              <span>
                {selectedAction === "approved"
                  ? "Sign Off & Enact Action"
                  : selectedAction === "rejected"
                  ? "Submit Official Rejection"
                  : "Return for Technical Revision"}
              </span>
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
