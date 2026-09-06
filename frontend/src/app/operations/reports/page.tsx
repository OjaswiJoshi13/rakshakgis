"use client";

import React from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FileText, Download, Layers } from "lucide-react";

export default function ReportsOperationsPage() {
  return (
    <OperationsSectionShell
      title="Report Generation & Export"
      description="Authoritative relocation dossiers, multi-hazard risk summaries, and machine-readable data export conforming to disaster management documentation standards."
      chunkId="M6-07"
      chunkTitle="Report Generation & Export UI"
      prerequisiteChunk="Chunk M6-02 & M6-03 (Relocation Workflow & Sites)"
      actionToolbar={
        <Button variant="secondary" size="sm" disabled className="opacity-70 cursor-not-allowed">
          <Download className="h-3.5 w-3.5 mr-1.5" />
          <span>Generate Dossier</span>
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Mount Point / Workflow Container for Chunk M6-07 */}
        <Card className="border-dashed border-slate-800 bg-slate-900/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sky-950/80 border border-sky-600/60 text-sky-400 mb-4">
            <FileText className="h-6 w-6" />
          </div>

          <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-600/50 mb-2">
            Chunk M6-07 Workspace Mount Point
          </Badge>

          <CardTitle className="text-lg font-bold text-slate-100">
            Report Generation & Export Canvas
          </CardTitle>

          <CardDescription className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto mt-2">
            This operational container provides the layout shell for Chunk M6-07. When implemented,
            it will provide template selection, PDF/JSON export generation, and statutory 
            dossier compilation for district administration.
          </CardDescription>

          <div className="mt-6 inline-flex items-center gap-2 rounded-md bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-400">
            <Layers className="h-3.5 w-3.5 text-emerald-400" />
            <span>Backend Binding: Relocation Dossier Engine & Data Exporters</span>
          </div>
        </Card>
      </div>
    </OperationsSectionShell>
  );
}
