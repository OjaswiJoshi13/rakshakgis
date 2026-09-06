"use client";

import React from "react";
import { OperationalAlertItem } from "@/types/alerts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import {
  X,
  ShieldCheck,
  CheckCircle2,
  MapPin,
  Clock,
  Layers,
  Info,
} from "lucide-react";

export interface AlertDetailModalProps {
  alert: OperationalAlertItem | null;
  isOpen: boolean;
  onClose: () => void;
  onAcknowledge?: (alertId: string) => void;
  isAcknowledging?: boolean;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  isOpen,
  onClose,
  onAcknowledge,
  isAcknowledging = false,
}) => {
  if (!isOpen || !alert) return null;

  const explainability = alert.explainability;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="alert-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150 overflow-y-auto"
    >
      <div className="relative w-full max-w-2xl rounded-xl bg-slate-900 border border-slate-700 shadow-2xl p-6 space-y-5 my-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-3 border-b border-slate-800">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  alert.severity === "extreme" || alert.severity === "severe"
                    ? "danger"
                    : alert.severity === "warning"
                    ? "warning"
                    : "info"
                }
                size="sm"
              >
                {alert.severity}
              </Badge>
              <Badge
                variant={
                  alert.status === "triggered"
                    ? "danger"
                    : alert.status === "insufficient_data"
                    ? "warning"
                    : "success"
                }
                size="sm"
              >
                {alert.status}
              </Badge>
              {alert.candidate_id && (
                <span className="text-xs font-mono text-slate-400">
                  {alert.candidate_id}
                </span>
              )}
            </div>
            <h3
              id="alert-modal-title"
              className="text-lg font-bold text-slate-100"
            >
              {alert.headline}
            </h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Narrative & Location Context */}
        <div className="space-y-3">
          <p className="text-sm text-slate-300 leading-relaxed">
            {alert.message}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-500 block">
                Settlement
              </span>
              <span className="text-slate-200 font-medium flex items-center gap-1 mt-0.5">
                <MapPin className="h-3 w-3 text-rose-400" />
                {alert.village_name || "Regional"}
              </span>
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-500 block">
                Geodesic Buffer
              </span>
              <span className="text-slate-200 font-mono mt-0.5 block">
                {alert.buffer_m || 500}m Radius
              </span>
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-500 block">
                Telemetry Station
              </span>
              <span className="text-slate-200 font-mono mt-0.5 block">
                {alert.source_id || "Regional AWS"}
              </span>
            </div>
          </div>
        </div>

        {/* Granular Trigger Evaluations Table (M3-11 Contract) */}
        {explainability && explainability.trigger_evaluations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-sky-400" />
              <span>M3-11 Deterministic Trigger Evaluations</span>
            </h4>

            <div className="overflow-x-auto rounded border border-slate-800">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2">Hazard Indicator</th>
                    <th className="px-3 py-2">Observed</th>
                    <th className="px-3 py-2">Op</th>
                    <th className="px-3 py-2">Threshold</th>
                    <th className="px-3 py-2">Decision</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-950/60 font-mono">
                  {explainability.trigger_evaluations.map((evalItem, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50">
                      <td className="px-3 py-2 text-slate-200 font-semibold">
                        {evalItem.indicator}
                      </td>
                      <td className="px-3 py-2 text-slate-300">
                        {evalItem.observed_value !== null && evalItem.observed_value !== undefined
                          ? `${evalItem.observed_value} ${evalItem.unit || ""}`
                          : "null (offline)"}
                      </td>
                      <td className="px-3 py-2 text-slate-400 font-bold">
                        {evalItem.operator}
                      </td>
                      <td className="px-3 py-2 text-slate-400">
                        {evalItem.configured_threshold !== null && evalItem.configured_threshold !== undefined
                          ? `${evalItem.configured_threshold} ${evalItem.unit || ""}`
                          : "unconfigured"}
                      </td>
                      <td className="px-3 py-2">
                        {evalItem.status === "triggered" ? (
                          <span className="text-red-400 font-bold">TRIGGERED</span>
                        ) : evalItem.status === "insufficient_data" ? (
                          <span className="text-amber-400 font-bold">INSUFFICIENT DATA</span>
                        ) : (
                          <span className="text-emerald-400 font-bold">NO TRIGGER</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Audit Notes */}
            <div className="space-y-1 pt-1">
              {explainability.trigger_evaluations.map((item, idx) => (
                <p key={idx} className="text-[11px] text-slate-400 italic">
                  &bull; {item.audit_note}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Statutory Rule 12 Mandate Notice */}
        <Alert severity="warning" title="Statutory Mandate: Candidate Advisory Status">
          {explainability?.governance_notice ||
            "PROPOSED DYNAMIC ALERT CANDIDATE ONLY: This event-driven candidate notification is generated for operational decision support and early warning. It does NOT constitute a statutory disaster declaration or legal evacuation order. Formal executive action requires officer review and authorization (Chunk M6-08 workflow)."}
        </Alert>

        {/* Footer */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span>Issued: {new Date(alert.issued_at).toLocaleString()}</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs"
            >
              Close
            </Button>

            {!alert.is_acknowledged && onAcknowledge && (
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={() => {
                  onAcknowledge(alert.id);
                  onClose();
                }}
                disabled={isAcknowledging}
                className="text-xs"
              >
                <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                <span>Acknowledge Alert</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
