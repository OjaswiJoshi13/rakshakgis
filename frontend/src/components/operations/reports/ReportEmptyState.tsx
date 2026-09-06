"use client";

import React from "react";
import { ReportTemplateId } from "@/types/reports";
import { REPORT_TEMPLATES } from "@/lib/api/reports";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FileText, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";

interface ReportEmptyStateProps {
  onSelectTemplate: (templateId: ReportTemplateId) => void;
  onGenerate: () => void;
  isCompiling: boolean;
}

export const ReportEmptyState: React.FC<ReportEmptyStateProps> = ({
  onSelectTemplate,
  onGenerate,
  isCompiling,
}) => {
  return (
    <Card className="border-dashed border-slate-800 bg-slate-900/30 p-8 text-center">
      <CardContent className="space-y-6 max-w-2xl mx-auto">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sky-950/80 border border-sky-600/60 text-sky-400">
          <FileText className="h-7 w-7" />
        </div>

        <div className="space-y-2">
          <Badge
            variant="outline"
            size="sm"
            className="font-mono text-sky-300 border-sky-600/50"
          >
            Operational Dossier Engine Ready
          </Badge>
          <h3 className="text-lg font-bold text-slate-100">
            Select a Report Template to Compile Dossier
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Generate authoritative relocation dossiers, candidate site infrastructure
            inventories, and multi-criteria suitability audits conforming to district disaster
            management standards.
          </p>
        </div>

        {/* Templates Quick Launch */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          {REPORT_TEMPLATES.map((tmpl) => (
            <button
              key={tmpl.id}
              type="button"
              onClick={() => onSelectTemplate(tmpl.id)}
              className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-800/50 transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="text-xs font-semibold text-slate-200 group-hover:text-sky-300 transition-colors">
                  {tmpl.title}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {tmpl.shortDescription}
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-sky-400 font-mono">
                <span>{tmpl.backendBinding.split(" ")[0]}</span>
                <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </button>
          ))}
        </div>

        <div className="pt-2">
          <Button
            type="button"
            variant="primary"
            size="md"
            onClick={onGenerate}
            isLoading={isCompiling}
            leftIcon={<Sparkles className="h-4 w-4 text-sky-200" />}
            className="bg-sky-600 hover:bg-sky-500 text-white shadow-lg"
          >
            <span>Compile Relocation Allocation Plan</span>
          </Button>
        </div>

        <div className="inline-flex items-center gap-2 rounded-md bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-400">
          <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
          <span>Statutory Compliance: Rule 8 Provenance & Rule 12 Review Mandate</span>
        </div>
      </CardContent>
    </Card>
  );
};
