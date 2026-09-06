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
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 shadow-2xl shadow-black/80 flex flex-col z-10">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 p-5 bg-slate-950/60 sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                M4-04 Explainability Audit
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
              className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2"
            >
              <span>{assignment.village_name}</span>
              <span className="text-sm font-normal font-mono text-slate-400">
                (ID: {assignment.village_id})
              </span>
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close audit modal"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-6 flex-1">
          {/* Village Context Strip */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-lg bg-slate-950/80 border border-slate-800 p-3.5 text-xs font-mono">
            <div>
              <span className="text-slate-500 block">Priority Score:</span>
              <span className="text-slate-200 font-bold text-sm">
                {assignment.priority_score.toFixed(1)} / 100
              </span>
              {assignment.priority_band && (
                <span className="text-slate-400 block capitalize text-[11px]">
                  {assignment.priority_band.replace("_", " ")}
                </span>
              )}
            </div>

            <div>
              <span className="text-slate-500 block">Demanded Households:</span>
              <span className="text-sky-300 font-bold text-sm">
                {assignment.incoming_households} HH
              </span>
            </div>

            <div>
              <span className="text-slate-500 block">Estimated Population:</span>
              <span className="text-slate-300 font-bold text-sm">
                {assignment.incoming_population
                  ? `${assignment.incoming_population} people`
                  : "N/A"}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block">Evaluated Sites:</span>
              <span className="text-emerald-400 font-bold text-sm">
                {assignment.evaluated_candidates.length} candidates
              </span>
            </div>
          </div>

          {/* Outcome Rationale Banner */}
          {isAssigned ? (
            <div className="rounded-lg border border-emerald-700/60 bg-emerald-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm font-mono">
                <CheckCircle2 className="h-4 w-4" />
                <span>Assignment Successful: {assignment.assigned_site_name}</span>
              </div>
              <p className="text-xs text-emerald-200/90 leading-relaxed">
                {assignment.selection_reason || "Selected as the highest-ranking feasible candidate site."}
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-emerald-300/80 pt-1 border-t border-emerald-800/40">
                <span>Distance: {assignment.distance_km?.toFixed(1) ?? "—"} km</span>
                <span>Suitability Score: {assignment.suitability_score?.toFixed(1) ?? "—"}</span>
                <span>
                  Site Capacity Impact: {assignment.available_capacity_before} → {assignment.available_capacity_after} HH
                </span>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-amber-700/60 bg-amber-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm font-mono">
                <ShieldAlert className="h-4 w-4" />
                <span>
                  Village Unassigned: Code [{assignment.unassigned_code || "NO_FEASIBLE_SITE"}]
                </span>
              </div>
              <p className="text-xs text-amber-200/90 leading-relaxed">
                {assignment.unassigned_reason || "All evaluated candidate sites failed either safety constraints, minimum suitability criteria, or carrying capacity limits."}
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
              <p className="text-xs text-slate-500 italic p-4 text-center border border-dashed border-slate-800 rounded-lg">
                No individual candidate site evaluation audits recorded for this village.
              </p>
            ) : (
              <div className="space-y-3">
                {assignment.evaluated_candidates.map((audit, idx) => {
                  const isSelectedSite =
                    isAssigned && String(assignment.assigned_site_id) === String(audit.site_id);

                  return (
                    <div
                      key={`${audit.site_id}-${idx}`}
                      className={`rounded-lg border p-4 transition-all ${
                        isSelectedSite
                          ? "border-emerald-600 bg-emerald-950/20"
                          : audit.is_feasible
                          ? "border-slate-700 bg-slate-800/40"
                          : "border-slate-800 bg-slate-900/40 opacity-80"
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-slate-400" />
                          <h4 className="font-semibold text-slate-200 text-sm">
                            {audit.site_name}
                          </h4>
                          <span className="text-xs font-mono text-slate-500">
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
                              <span>Rejected [{audit.rejection_code || "INELIGIBLE"}]</span>
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Metrics Matrix */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono bg-slate-950/50 rounded p-2.5 my-2 border border-slate-800/60">
                        <div>
                          <span className="text-slate-500 block">Distance:</span>
                          <span className="text-slate-200">
                            {audit.distance_km !== null && audit.distance_km !== undefined
                              ? `${audit.distance_km.toFixed(1)} km`
                              : "N/A"}
                          </span>
                        </div>

                        <div>
                          <span className="text-slate-500 block">Suitability:</span>
                          <span className="text-slate-200">
                            {audit.suitability_score !== null && audit.suitability_score !== undefined
                              ? `${audit.suitability_score.toFixed(1)} (${audit.suitability_decision || "N/A"})`
                              : "N/A"}
                          </span>
                        </div>

                        <div>
                          <span className="text-slate-500 block">Capacity Margin:</span>
                          <span
                            className={
                              audit.capacity_margin !== null && audit.capacity_margin !== undefined
                                ? audit.capacity_margin >= 0
                                  ? "text-emerald-400"
                                  : "text-red-400 font-bold"
                                : "text-slate-400"
                            }
                          >
                            {audit.capacity_margin !== null && audit.capacity_margin !== undefined
                              ? audit.capacity_margin >= 0
                                ? `+${audit.capacity_margin} HH`
                                : `${audit.capacity_margin} HH (Deficit)`
                              : "N/A"}
                          </span>
                        </div>

                        <div>
                          <span className="text-slate-500 block">Composite Rank:</span>
                          <span className="text-sky-300">
                            {audit.rank_score !== null && audit.rank_score !== undefined
                              ? audit.rank_score.toFixed(1)
                              : "N/A"}
                          </span>
                        </div>
                      </div>

                      {/* Rejection Details if Failed */}
                      {!audit.is_feasible && audit.rejection_reasons.length > 0 && (
                        <div className="mt-2 space-y-1 text-xs text-red-300/90 font-mono bg-red-950/30 rounded p-2 border border-red-900/50">
                          <span className="font-semibold text-red-400 block">Constraint Failure(s):</span>
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
        <div className="border-t border-slate-800 p-4 bg-slate-950/60 flex items-center justify-between">
          <div className="text-xs text-slate-500 font-mono flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-sky-400" />
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
