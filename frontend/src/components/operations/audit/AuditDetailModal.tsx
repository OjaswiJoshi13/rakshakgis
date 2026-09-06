"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { AuditRecord } from "@/types/audit";
import {
  X,
  ShieldCheck,
  Cpu,
  Lock,
  Copy,
  Check,
  Layers,
  FileCode2,
} from "lucide-react";

interface AuditDetailModalProps {
  record: AuditRecord | null;
  isOpen: boolean;
  onClose: () => void;
}

export const AuditDetailModal: React.FC<AuditDetailModalProps> = ({
  record,
  isOpen,
  onClose,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  if (!isOpen || !record) return null;

  const handleCopyHash = () => {
    if (record.traceability.cryptographic_hash) {
      navigator.clipboard.writeText(record.traceability.cryptographic_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleCopyId = () => {
    navigator.clipboard.writeText(record.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const isOfficer = record.category === "officer_decision";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="audit-detail-title"
      data-testid="audit-detail-modal"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 shadow-2xl space-y-5 p-6 text-slate-100">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs text-sky-400 font-bold">
                {record.id}
              </span>
              <button
                type="button"
                onClick={handleCopyId}
                className="text-slate-400 hover:text-slate-200 transition-colors p-0.5"
                title="Copy Audit Event ID"
                aria-label="Copy Audit Event ID"
              >
                {copiedId ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
              <Badge variant="outline" size="sm" className="font-mono text-slate-400">
                {record.resource_type}
              </Badge>
              {isOfficer && (
                <Badge variant="outline" size="sm" className="font-mono text-emerald-400 border-emerald-600/50">
                  <ShieldCheck className="h-3 w-3 mr-1" />
                  Rule 12 Protocol
                </Badge>
              )}
            </div>
            <h3 id="audit-detail-title" className="text-lg font-bold text-slate-100">
              {record.action_label}
            </h3>
            <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
              <span>
                {new Date(record.timestamp).toLocaleString("en-IN", {
                  dateStyle: "full",
                  timeStyle: "medium",
                })}
              </span>
              <span>•</span>
              <span>IP: {record.ip_address || "127.0.0.1"}</span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            aria-label="Close Audit Detail View"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Actor Credentials & Official Posture */}
        <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-3">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Authorized Actor & Execution Context
          </div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-slate-300">
              {isOfficer ? (
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
              ) : (
                <Cpu className="h-5 w-5 text-purple-400" />
              )}
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100">
                {record.actor.name}
              </div>
              <div className="text-xs text-slate-400 font-mono">
                {record.actor.role}
                {record.actor.department ? ` • ${record.actor.department}` : ""}
              </div>
              {record.actor.email && (
                <div className="text-[11px] text-slate-500 font-mono">
                  {record.actor.email}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Affected Entity & Directives */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Target Entity & Resource Identifier
          </div>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-3.5 text-xs font-mono space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Entity Name:</span>
              <strong className="text-slate-100 font-sans font-semibold">
                {record.target_entity_name}
              </strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Resource ID:</span>
              <span className="text-sky-300">{record.resource_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Decision Outcome:</span>
              <span className="uppercase font-bold text-emerald-400">
                {record.decision_status}
              </span>
            </div>
          </div>
        </div>

        {/* Official Rationale / Reason Quote Block */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Recorded Official Rationale & Operational Instructions
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            {record.reason ? (
              <blockquote className="text-xs sm:text-sm text-slate-200 italic leading-relaxed border-l-2 border-sky-500 pl-3">
                &ldquo;{record.reason}&rdquo;
              </blockquote>
            ) : (
              <p className="text-xs text-slate-500 font-mono italic">
                No supplemental notes recorded for this automated operation.
              </p>
            )}
          </div>
        </div>

        {/* Provenance & Statutory Mandate */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/30 p-3 space-y-1">
            <span className="text-slate-500 block text-[10px] uppercase">
              Source Engine
            </span>
            <span className="text-slate-200 font-semibold">
              {record.traceability.source_engine}
            </span>
          </div>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/30 p-3 space-y-1">
            <span className="text-slate-500 block text-[10px] uppercase">
              Regional Profile
            </span>
            <span className="text-slate-200 font-semibold">
              {record.traceability.region_profile_id} (Chamoli Pilot)
            </span>
          </div>
        </div>

        {/* Statutory Legal Mandate */}
        <div className="rounded-lg border border-amber-900/60 bg-amber-950/30 p-3 text-xs text-amber-200 flex items-start gap-2">
          <Layers className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-amber-400 font-mono">Statutory Authority: </strong>
            <span>{record.traceability.statutory_mandate}</span>
          </div>
        </div>

        {/* Cryptographic SHA-256 Hash Verification Badge */}
        <div className="rounded-lg border border-sky-900/60 bg-sky-950/30 p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono text-sky-300 font-semibold">
              <Lock className="h-3.5 w-3.5 text-sky-400" />
              <span>Cryptographic Provenance Hash (SHA-256)</span>
            </div>
            <Badge variant="outline" size="sm" className="font-mono text-emerald-400 border-emerald-600/50">
              <Check className="h-3 w-3 mr-1" />
              Verified Seal
            </Badge>
          </div>
          <div className="flex items-center justify-between gap-2 bg-slate-950 rounded p-2 border border-slate-800">
            <code className="text-[11px] font-mono text-slate-300 truncate max-w-md select-all">
              {record.traceability.cryptographic_hash}
            </code>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleCopyHash}
              className="text-xs h-6 px-2 shrink-0 gap-1"
              aria-label="Copy SHA-256 Hash"
            >
              {copiedHash ? (
                <>
                  <Check className="h-3 w-3 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Copy</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* JSON Payload Inspection (Before / After) */}
        {(record.traceability.payload_before || record.traceability.payload_after) && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <FileCode2 className="h-3.5 w-3.5 text-slate-400" />
              <span>State Transition Payloads (Before / After)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded bg-slate-950 border border-slate-800 p-2.5">
                <span className="text-slate-500 block mb-1">State Before:</span>
                <pre className="text-slate-300 overflow-x-auto">
                  {JSON.stringify(record.traceability.payload_before || {}, null, 2)}
                </pre>
              </div>
              <div className="rounded bg-slate-950 border border-slate-800 p-2.5">
                <span className="text-emerald-400 block mb-1">State After:</span>
                <pre className="text-slate-300 overflow-x-auto">
                  {JSON.stringify(record.traceability.payload_after || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Read-Only Notice & Footer Actions */}
        <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-slate-500">
          <span>Sealed Immutable Audit Record • Zero Modification Rights</span>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onClose}
            className="w-full sm:w-auto"
          >
            Close Inspector
          </Button>
        </div>
      </div>
    </div>
  );
};
