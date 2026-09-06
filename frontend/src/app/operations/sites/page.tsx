"use client";

import React from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { MapPin, Layers } from "lucide-react";

export default function SitesOperationsPage() {
  return (
    <OperationsSectionShell
      title="Relocation Sites & Infrastructure"
      description="Candidate relocation site suitability assessment, 5-dimensional infrastructure sizing (water, land, sanitation, healthcare, shelters), and physical hazard buffer validation."
      chunkId="M6-03"
      chunkTitle="Relocation Site Details & Infrastructure UI"
      prerequisiteChunk="Chunk M4-01 & M4-03 (Candidate Sites & Capacity Sizing — COMMITTED)"
      actionToolbar={
        <Button variant="secondary" size="sm" disabled className="opacity-70 cursor-not-allowed">
          <MapPin className="h-3.5 w-3.5 mr-1.5" />
          <span>Inspect Site Suitability</span>
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Mount Point / Workflow Container for Chunk M6-03 */}
        <Card className="border-dashed border-slate-800 bg-slate-900/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sky-950/80 border border-sky-600/60 text-sky-400 mb-4">
            <MapPin className="h-6 w-6" />
          </div>

          <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-600/50 mb-2">
            Chunk M6-03 Workspace Mount Point
          </Badge>

          <CardTitle className="text-lg font-bold text-slate-100">
            Relocation Site Details & Infrastructure Canvas
          </CardTitle>

          <CardDescription className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto mt-2">
            This operational container provides the layout shell for Chunk M6-03. When implemented,
            it will render the 12 candidate relocation sites, 9 suitability criteria evaluation cards,
            and infrastructure deficit charts.
          </CardDescription>

          <div className="mt-6 inline-flex items-center gap-2 rounded-md bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-400">
            <Layers className="h-3.5 w-3.5 text-emerald-400" />
            <span>Backend Binding: Sites Engine (M4-01) & Capacity Sizing (M4-03)</span>
          </div>
        </Card>
      </div>
    </OperationsSectionShell>
  );
}
