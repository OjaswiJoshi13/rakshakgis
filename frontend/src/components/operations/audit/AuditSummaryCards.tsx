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
      <Card className="border-border-base bg-surface-raised p-4 shadow-2xs">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-text-muted">
              Total Audit Events
            </span>
            <div className="flex h-7 w-7 items-center justify-center rounded border border-border-base bg-surface-base text-text-secondary">
              <History className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono tabular-nums text-text-primary">
              {isLoading ? "—" : metrics.totalEvents}
            </span>
            <span className="text-[10px] font-mono text-text-muted">Events</span>
          </div>
          <p className="text-xs text-text-secondary">
            Immutable chronological platform action ledger
          </p>
        </CardContent>
      </Card>

      {/* 2. Officer Sign-Offs (Rule 12) */}
      <Card className="border-border-base bg-surface-raised p-4 shadow-2xs">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-text-muted">
              Officer Sign-Offs
            </span>
            <Badge variant="outline" size="sm" className="font-mono text-[#1a7f37] dark:text-[#3fb950] border-[#1a7f37]/40 bg-[#1a7f37]/10">
              Rule 12
            </Badge>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono tabular-nums text-[#1a7f37] dark:text-[#3fb950]">
              {isLoading ? "—" : metrics.officerSignOffs}
            </span>
            <span className="text-[10px] font-mono text-text-muted">Decisions</span>
          </div>
          <p className="text-xs text-text-secondary">
            Authoritative officer approvals, rejections & revisions
          </p>
        </CardContent>
      </Card>

      {/* 3. Automated Operations */}
      <Card className="border-border-base bg-surface-raised p-4 shadow-2xs">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-text-muted">
              Automated Events
            </span>
            <div className="flex h-7 w-7 items-center justify-center rounded border border-border-base bg-surface-base text-text-secondary">
              <Cpu className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono tabular-nums text-text-primary">
              {isLoading ? "—" : metrics.automatedActions}
            </span>
            <span className="text-[10px] font-mono text-text-muted">Operations</span>
          </div>
          <p className="text-xs text-text-secondary">
            Batch commits, simulations, alerts & telemetry probes
          </p>
        </CardContent>
      </Card>

      {/* 4. Cryptographic Hash Integrity */}
      <Card className="border-border-base bg-surface-raised p-4 shadow-2xs">
        <CardContent className="p-0 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-text-muted">
              Chain Integrity
            </span>
            <Badge variant="outline" size="sm" className="font-mono text-text-secondary border-border-base">
              SHA-256
            </Badge>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono tabular-nums text-text-primary">
              {isLoading ? "—" : `${metrics.integrityPercentage}%`}
            </span>
            <CheckCircle2 className="h-4 w-4 text-[#1a7f37] dark:text-[#3fb950]" />
          </div>
          <p className="text-xs text-text-secondary">
            All records verified against cryptographic hashes
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
