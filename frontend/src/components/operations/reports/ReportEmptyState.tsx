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

const getTemplateModelName = (id: ReportTemplateId) => {
  switch (id) {
    case "relocation_allocation":
      return "Relocation Matching Model";
    case "site_infrastructure":
      return "Site Infrastructure Model";
    case "suitability_capacity":
      return "Suitability & Capacity Model";
    case "comprehensive_dossier":
      return "Comprehensive District Dossier";
    default:
      return "Operational Analytical Model";
  }
};

export const ReportEmptyState: React.FC<ReportEmptyStateProps> = ({
  onSelectTemplate,
  onGenerate,
  isCompiling,
}) => {
  return (
    <Card className="border-dashed border-border-strong bg-surface-panel p-8 text-center shadow-xs">
      <CardContent className="space-y-6 max-w-2xl mx-auto">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary-50 dark:bg-primary-950/80 border border-primary-200 dark:border-primary-700/60 text-primary-600 dark:text-primary-400">
          <FileText className="h-7 w-7" />
        </div>

        <div className="space-y-2">
          <Badge
            variant="outline"
            size="sm"
            className="font-mono text-primary-700 dark:text-primary-300 border-primary-300 dark:border-primary-700/50 bg-primary-50 dark:bg-primary-950/40"
          >
            Operational Dossier Engine Ready
          </Badge>
          <h3 className="text-lg font-bold text-text-primary">
            Select a Report Template to Compile Dossier
          </h3>
          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
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
              className="p-3.5 rounded-lg border border-border-subtle bg-surface-elevated hover:border-border-strong hover:bg-surface-raised hover:shadow-xs transition-all flex flex-col justify-between group text-left"
            >
              <div>
                <div className="text-xs font-semibold text-text-primary group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {tmpl.title}
                </div>
                <div className="text-[11px] text-text-secondary mt-1 line-clamp-2">
                  {tmpl.shortDescription}
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-primary-600 dark:text-primary-400 font-mono">
                <span>{getTemplateModelName(tmpl.id)}</span>
                <span className="sr-only">{tmpl.backendBinding.split(" ")[0]}</span>
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
            leftIcon={<Sparkles className="h-4 w-4 text-white" />}
            className="bg-primary-600 hover:bg-primary-700 text-white shadow-xs"
          >
            <span>Compile Relocation Allocation Plan</span>
          </Button>
        </div>

        <div className="inline-flex items-center gap-2 rounded-md bg-surface-elevated border border-border-subtle px-3 py-1.5 text-xs font-mono text-text-secondary">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>Statutory Compliance: Rule 8 Provenance &amp; Rule 12 Review Mandate</span>
        </div>
      </CardContent>
    </Card>
  );
};
