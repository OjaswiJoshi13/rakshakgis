"use client";

import React, { useEffect } from "react";
import { VillageAssignmentResult } from "@/types/relocation";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  X,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Building2,
  Navigation,
  Scale,
  Activity,
  Layers,
} from "lucide-react";

export interface CandidateAuditModalProps {
  assignment: VillageAssignmentResult | null;
  onClose: () => void;
}

export const CandidateAuditModal: React.FC<CandidateAuditModalProps> = ({
  assignment,
  onClose,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!assignment) return null;

  const isAssigned = assignment.status === "assigned";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="audit-modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog Box */}
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl border border-border-subtle bg-surface-panel shadow-2xl flex flex-col z-10">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border-subtle p-5 bg-surface-elevated sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-muted">
                Explainability Audit
              </span>
              <Badge
                variant={isAssigned ? "success" : "warning"}
                size="sm"
                className="font-mono"
              >
                {assignment.status.toUpperCase()}
              </Badge>
            </div>
            <h2
              id="audit-modal-title"
              className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2"
            >
              <span>{assignment.village_name}</span>
              <span className="text-sm font-normal font-mono text-text-muted">
                (ID: {assignment.village_id})
              </span>
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close audit modal"
            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-subtle hover:text-text-primary transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-6 flex-1">
          {/* Village Context Strip */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-lg bg-surface-elevated border border-border-subtle p-3.5 text-xs font-mono">
            <div>
              <span className="text-text-muted block">Priority Score:</span>
              <span className="text-text-primary font-bold text-sm">
                {assignment.priority_score.toFixed(1)} / 100
              </span>
              {assignment.priority_band && (
                <span className="text-text-secondary block capitalize text-[11px]">
                  {assignment.priority_band.replace("_", " ")}
                </span>
              )}
            </div>

            <div>
              <span className="text-text-muted block">Demanded Households:</span>
              <span className="text-sky-700 dark:text-sky-300 font-bold text-sm">
                {assignment.incoming_households} HH
              </span>
            </div>

            <div>
              <span className="text-text-muted block">Estimated Population:</span>
              <span className="text-text-primary font-bold text-sm">
                {assignment.incoming_population
                  ? `${assignment.incoming_population} people`
                  : "N/A"}
              </span>
            </div>

            <div>
              <span className="text-text-muted block">Evaluated Sites:</span>
              <span className="text-emerald-700 dark:text-emerald-400 font-bold text-sm">
                {assignment.evaluated_candidates.length} candidates
              </span>
            </div>
          </div>

          {/* Outcome Rationale Banner */}
          {isAssigned ? (
            <div className="rounded-lg border border-emerald-300 dark:border-emerald-700/60 bg-emerald-50 dark:bg-emerald-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-emerald-900 dark:text-emerald-400 font-semibold text-sm font-mono">
                <CheckCircle2 className="h-4 w-4" />
                <span>Assignment Successful: {assignment.assigned_site_name}</span>
              </div>
              <p className="text-xs text-emerald-800 dark:text-emerald-200/90 leading-relaxed">
                {assignment.selection_reason || "Selected as the highest-ranking feasible candidate site."}
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-emerald-800 dark:text-emerald-300/80 pt-1 border-t border-emerald-200 dark:border-emerald-800/40">
                <span>Distance: {assignment.distance_km?.toFixed(1) ?? "—"} km</span>
                <span>Suitability Score: {assignment.suitability_score?.toFixed(1) ?? "—"}</span>
                <span>
                  Site Capacity Impact: {assignment.available_capacity_before} → {assignment.available_capacity_after} HH
                </span>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-900 dark:text-amber-400 font-semibold text-sm font-mono">
                <ShieldAlert className="h-4 w-4" />
                <span>
                  Village Unassigned — Regional Capacity Shortfall
                </span>
                <span className="sr-only font-mono">
                  Village Unassigned: Code [{assignment.unassigned_code || "insufficient_capacity"}]
                </span>
                <span className="text-[10px] font-mono text-text-muted ml-auto hidden sm:inline">
                  Ref: {assignment.unassigned_code || "INSUFFICIENT_CAPACITY"}
                </span>
              </div>
              <p className="text-xs text-amber-800 dark:text-amber-200/90 leading-relaxed">
                {assignment.unassigned_reason || "All evaluated candidate sites failed mandatory carrying capacity limits or safety criteria for this settlement."}
              </p>
            </div>
          )}

          {/* Candidate Evaluation Audit Trail */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Layers className="h-3.5 w-3.5 text-sky-400" />
              <span>Evaluated Candidate Sites Breakdown ({assignment.evaluated_candidates.length})</span>
            </h3>

            {assignment.evaluated_candidates.length === 0 ? (
              <p className="text-xs text-text-muted italic p-4 text-center border border-dashed border-border-subtle rounded-lg">
                No individual candidate site evaluation audits recorded for this village.
              </p>
            ) : (
              <div className="space-y-3">
                {assignment.evaluated_candidates.map((audit, idx) => {
                  const isSelectedSite =
                    isAssigned && String(assignment.assigned_site_id) === String(audit.site_id);
                  const rejCode = audit.rejection_code ? String(audit.rejection_code).toLowerCase() : "";
                  const isCapRej = rejCode === "insufficient_capacity";
                  const isSafeRej = rejCode === "unsafe_site";
                  const isLowSuitRej = rejCode === "low_suitability";

                  return (
                    <div
                      key={`${audit.site_id}-${idx}`}
                      className={`rounded-lg border p-4 transition-all ${
                        isSelectedSite
                          ? "border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/20"
                          : audit.is_feasible
                          ? "border-border-subtle bg-surface-elevated"
                          : "border-border-subtle bg-surface-subtle opacity-80"
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-text-muted" />
                          <h4 className="font-semibold text-text-primary text-sm">
                            {audit.site_name}
                          </h4>
                          <span className="text-xs font-mono text-text-muted">
                            (ID: {audit.site_id})
                          </span>
                          {isSelectedSite && (
                            <Badge variant="success" size="sm" className="font-mono">
                              Selected Destination
                            </Badge>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {audit.is_feasible ? (
                            <Badge variant="success" size="sm" className="font-mono flex items-center gap-1">
                              <CheckCircle2 className="h-3 w-3" />
                              <span>Feasible</span>
                            </Badge>
                          ) : (
                            <Badge variant="danger" size="sm" className="font-mono flex items-center gap-1">
                              <XCircle className="h-3 w-3" />
                              <span>
                                {isCapRej
                                  ? "REJECTED — INSUFFICIENT CAPACITY"
                                  : isSafeRej
                                  ? "REJECTED — SAFETY CONSTRAINT"
                                  : isLowSuitRej
                                  ? "REJECTED — LOW SUITABILITY"
                                  : `REJECTED — ${audit.rejection_code ? String(audit.rejection_code).toUpperCase() : "INELIGIBLE"}`}
                              </span>
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Metrics Matrix */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono bg-surface-panel rounded p-2.5 my-2 border border-border-subtle">
                        <div>
                          <span className="text-text-muted block">Distance:</span>
                          <span className="text-text-primary">
                            {audit.distance_km !== null && audit.distance_km !== undefined
                              ? `${audit.distance_km.toFixed(1)} km`
                              : "Not evaluated — site rejected before ranking"}
                          </span>
                        </div>

                        <div>
                          <span className="text-text-muted block">Suitability:</span>
                          <span className="text-text-primary">
                            {audit.suitability_score !== null && audit.suitability_score !== undefined
                              ? `${audit.suitability_score.toFixed(1)} (${audit.suitability_decision || "N/A"})`
                              : "Not available in source"}
                          </span>
                        </div>

                        <div>
                          <span className="text-text-muted block">Capacity Margin:</span>
                          <span
                            className={
                              audit.capacity_margin !== null && audit.capacity_margin !== undefined
                                ? audit.capacity_margin >= 0
                                  ? "text-emerald-700 dark:text-emerald-400 font-bold"
                                  : "text-red-700 dark:text-red-400 font-bold"
                                : "text-text-muted"
                            }
                          >
                            {audit.capacity_margin !== null && audit.capacity_margin !== undefined
                              ? audit.capacity_margin >= 0
                                ? `+${audit.capacity_margin} HH (Surplus)`
                                : `${audit.capacity_margin} HH (Deficit: ${Math.abs(audit.capacity_margin)} HH)`
                              : "Not available in source"}
                          </span>
                        </div>

                        <div>
                          <span className="text-text-muted block">Composite Rank:</span>
                          <span className="text-sky-700 dark:text-sky-300 font-bold">
                            {audit.rank_score !== null && audit.rank_score !== undefined
                              ? audit.rank_score.toFixed(1)
                              : isCapRej
                              ? "Not evaluated — failed mandatory capacity constraint"
                              : isSafeRej
                              ? "Not evaluated — failed mandatory safety constraint"
                              : "Not evaluated — prerequisite constraint failed"}
                          </span>
                        </div>
                      </div>

                      {/* Rejection Details if Failed */}
                      {!audit.is_feasible && audit.rejection_reasons.length > 0 && (
                        <div className="mt-2 space-y-1 text-xs text-red-900 dark:text-red-300/90 font-mono bg-red-50 dark:bg-red-950/30 rounded p-2.5 border border-red-200 dark:border-red-900/50">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="font-semibold text-red-800 dark:text-red-400 block">
                              Why this site was rejected
                            </span>
                            <span className="text-[10px] text-red-700 dark:text-red-400 uppercase font-semibold">
                              {isCapRej
                                ? "Capacity constraint"
                                : isSafeRej
                                ? "Safety constraint"
                                : "Feasibility requirement"}
                            </span>
                          </div>
                          <ul className="list-disc list-inside space-y-0.5">
                            {audit.rejection_reasons.map((reason, rIdx) => (
                              <li key={rIdx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border-subtle p-4 bg-surface-elevated flex items-center justify-between">
          <div className="text-xs text-text-muted font-mono flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span>Deterministic Greedy Allocation Engine Trace</span>
          </div>

          <Button type="button" variant="secondary" size="sm" onClick={onClose}>
            Close Audit
          </Button>
        </div>
      </div>
    </div>
  );
};
