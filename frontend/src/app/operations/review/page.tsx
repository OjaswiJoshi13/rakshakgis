"use client";

import React from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ShieldCheck, CheckCircle2, Layers } from "lucide-react";

export default function ReviewOperationsPage() {
  return (
    <OperationsSectionShell
      title="Officer Review & Sign-Off"
      description="Statutory Rule 12 verification gateway: review AI-recommended relocation assignments and Red Zone demarcations, record official legal declarations, and execute multi-officer sign-offs."
      chunkId="M6-08"
      chunkTitle="Officer Review & Action Sign-Off Workflow"
      prerequisiteChunk="Chunk M6-02 & M6-04 (Relocation & Scenario Workflows)"
      actionToolbar={
        <Button variant="primary" size="sm" disabled className="opacity-70 cursor-not-allowed">
          <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
          <span>Approve Action Dossier</span>
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Mount Point / Workflow Container for Chunk M6-08 */}
        <Card className="border-dashed border-slate-800 bg-slate-900/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sky-950/80 border border-sky-600/60 text-sky-400 mb-4">
            <ShieldCheck className="h-6 w-6" />
          </div>

          <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-600/50 mb-2">
            Chunk M6-08 Workspace Mount Point
          </Badge>

          <CardTitle className="text-lg font-bold text-slate-100">
            Officer Review & Action Sign-Off Canvas
          </CardTitle>

          <CardDescription className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto mt-2">
            This operational container provides the layout shell for Chunk M6-08. When implemented,
            it will feature the statutory officer approval form, legal declaration checklist,
            digital endorsement signature capture, and action dispatch controls.
          </CardDescription>

          <div className="mt-6 inline-flex items-center gap-2 rounded-md bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-400">
            <Layers className="h-3.5 w-3.5 text-emerald-400" />
            <span>Governance Rule: Rule 12 Mandatory Officer Review</span>
          </div>
        </Card>
      </div>
    </OperationsSectionShell>
  );
}
