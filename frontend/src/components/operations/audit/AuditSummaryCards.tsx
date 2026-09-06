"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AuditSummaryKPIs } from "@/types/audit";
import { History, ShieldCheck, Cpu, CheckCircle2 } from "lucide-react";

interface AuditSummaryCardsProps {
  metrics: AuditSummaryKPIs;
  isLoading?: boolean;
}

export const AuditSummaryCards: React.FC<AuditSummaryCardsProps> = ({
  metrics,
  isLoading = false,
}) => {
  return (
    <div
      data-testid="audit-summary-cards"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {/* 1. Total Audit Events */}
      <Card className="border-slate-800 bg-slate-900/50 p-4">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-slate-400">
              Total Audit Events
            </span>
            <div className="flex h-7 w-7 items-center justify-center rounded bg-sky-950/80 border border-sky-600/50 text-sky-400">
              <History className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">
              {isLoading ? "—" : metrics.totalEvents}
            </span>
            <span className="text-[10px] font-mono text-slate-400">Events</span>
          </div>
          <p className="text-xs text-slate-400">
            Immutable chronological platform action ledger
          </p>
        </CardContent>
      </Card>

      {/* 2. Officer Sign-Offs (Rule 12) */}
      <Card className="border-slate-800 bg-slate-900/50 p-4">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-slate-400">
              Officer Sign-Offs
            </span>
            <Badge variant="outline" size="sm" className="font-mono text-emerald-400 border-emerald-600/50">
              Rule 12
            </Badge>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {isLoading ? "—" : metrics.officerSignOffs}
            </span>
            <span className="text-[10px] font-mono text-slate-400">Decisions</span>
          </div>
          <p className="text-xs text-slate-400">
            Authoritative officer approvals, rejections & revisions
          </p>
        </CardContent>
      </Card>

      {/* 3. Automated Operations */}
      <Card className="border-slate-800 bg-slate-900/50 p-4">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-slate-400">
              Automated Events
            </span>
            <div className="flex h-7 w-7 items-center justify-center rounded bg-purple-950/80 border border-purple-600/50 text-purple-400">
              <Cpu className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-purple-300">
              {isLoading ? "—" : metrics.automatedActions}
            </span>
            <span className="text-[10px] font-mono text-slate-400">Operations</span>
          </div>
          <p className="text-xs text-slate-400">
            Batch commits, simulations, alerts & telemetry probes
          </p>
        </CardContent>
      </Card>

      {/* 4. Cryptographic Hash Integrity */}
      <Card className="border-slate-800 bg-slate-900/50 p-4">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-slate-400">
              Chain Integrity
            </span>
            <Badge variant="outline" size="sm" className="font-mono text-sky-400 border-sky-600/50">
              SHA-256
            </Badge>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-sky-300">
              {isLoading ? "—" : `${metrics.integrityPercentage}%`}
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-xs text-slate-400">
            All records verified against cryptographic hashes
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
