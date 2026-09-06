"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { OfficerDecisionRecord } from "@/types/review";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  ShieldCheck,
  UserCheck,
  Calendar,
  Quote,
  RotateCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DecisionStatusBannerProps {
  decision: OfficerDecisionRecord;
  onReopenDecision?: () => void;
  isReopening?: boolean;
}

export const DecisionStatusBanner: React.FC<DecisionStatusBannerProps> = ({
  decision,
  onReopenDecision,
  isReopening = false,
}) => {
  const isApproved = decision.action_taken === "approved";
  const isRejected = decision.action_taken === "rejected";
  const isRevision = decision.action_taken === "revision_requested";

  const getBorderColor = () => {
    if (isApproved) return "border-emerald-700/60 bg-emerald-950/40 text-emerald-100";
    if (isRejected) return "border-rose-700/60 bg-rose-950/40 text-rose-100";
    return "border-sky-700/60 bg-sky-950/40 text-sky-100";
  };

  return (
    <div className={cn("rounded-xl border p-5 shadow-xl", getBorderColor())}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/60">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl border shadow-inner",
              isApproved && "border-emerald-500 bg-emerald-900/60 text-emerald-400",
              isRejected && "border-rose-500 bg-rose-900/60 text-rose-400",
              isRevision && "border-sky-500 bg-sky-900/60 text-sky-400"
            )}
          >
            {isApproved && <CheckCircle2 className="h-5 w-5" />}
            {isRejected && <XCircle className="h-5 w-5" />}
            {isRevision && <RotateCcw className="h-5 w-5" />}
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs uppercase tracking-wider font-bold font-mono">
                {isApproved && "OFFICIALLY APPROVED UNDER RULE 12 PROTOCOL"}
                {isRejected && "OFFICIALLY REJECTED BY DISTRICT OFFICER"}
                {isRevision && "RETURNED TO TECHNICAL PLANNERS FOR REVISION"}
              </span>
              {decision.overridden_recommendation && (
                <Badge variant="warning" size="sm" className="font-mono text-[10px]">
                  Officer Override
                </Badge>
              )}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
              Decision Record ID: <span className="text-slate-200">{decision.id}</span>
            </div>
          </div>
        </div>

        {onReopenDecision && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onReopenDecision}
            isLoading={isReopening}
            disabled={isReopening}
            leftIcon={<RotateCw className="h-3.5 w-3.5" />}
            className="text-xs font-mono border-slate-700 hover:bg-slate-800 self-start sm:self-auto"
          >
            <span>Re-evaluate Decision</span>
          </Button>
        )}
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Officer Attribution Details */}
        <div className="space-y-2 rounded-lg bg-slate-950/60 p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
            Sign-Off Authority
          </div>
          <div className="flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-sky-400 shrink-0" />
            <div>
              <div className="font-bold text-slate-200">{decision.officer_name}</div>
              <div className="text-[11px] text-slate-400">{decision.officer_role}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-slate-400 pt-1 border-t border-slate-900 text-[11px] font-mono">
            <Calendar className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            <span>
              Decided on:{" "}
              <strong className="text-slate-300">
                {new Date(decision.decided_at).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "medium",
                })}
              </strong>
            </span>
          </div>
        </div>

        {/* Official Rationale Quote */}
        <div className="space-y-2 rounded-lg bg-slate-950/60 p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Quote className="h-3.5 w-3.5 text-sky-400" />
            <span>Recorded Officer Rationale</span>
          </div>
          <p className="text-xs text-slate-200 italic leading-relaxed">
            &ldquo;{decision.rationale || "Operational action verified and authorized in accordance with statutory guidelines."}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
};
