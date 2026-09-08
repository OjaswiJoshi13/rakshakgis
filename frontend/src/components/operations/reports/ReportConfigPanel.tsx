"use client";

import React from "react";
import {
  ReportConfig,
  ReportStatusFilter,
  ReportTemplateId,
} from "@/types/reports";
import { REPORT_TEMPLATES } from "@/lib/api/reports";
import { CandidateSiteRead } from "@/types/sites";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  FileText,
  MapPin,
  CheckCircle2,
  Filter,
  Building2,
  Layers,
  Sliders,
  Sparkles,
} from "lucide-react";

interface ReportConfigPanelProps {
  config: ReportConfig;
  onConfigChange: (config: ReportConfig) => void;
  sites: CandidateSiteRead[];
  onCompile: () => void;
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

export const ReportConfigPanel: React.FC<ReportConfigPanelProps> = ({
  config,
  onConfigChange,
  sites,
  onCompile,
  isCompiling,
}) => {
  const currentTemplate =
    REPORT_TEMPLATES.find((t) => t.id === config.templateId) ||
    REPORT_TEMPLATES[0];

  const handleTemplateSelect = (templateId: ReportTemplateId) => {
    onConfigChange({
      ...config,
      templateId,
    });
  };

  const handleStatusFilter = (statusFilter: ReportStatusFilter) => {
    onConfigChange({
      ...config,
      statusFilter,
    });
  };

  const handleSiteSelect = (siteId: string) => {
    onConfigChange({
      ...config,
      selectedSiteId: siteId === "all" ? "all" : parseInt(siteId, 10),
    });
  };

  const handleToggleAudits = (e: React.ChangeEvent<HTMLInputElement>) => {
    onConfigChange({
      ...config,
      includeAudits: e.target.checked,
    });
  };

  const handleToggleDeficits = (e: React.ChangeEvent<HTMLInputElement>) => {
    onConfigChange({
      ...config,
      includeDeficits: e.target.checked,
    });
  };

  return (
    <Card className="border-border-subtle bg-surface-panel shadow-xs">
      <CardContent className="p-5 space-y-6">
        {/* Template Selector Section */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
              <span>Select Report Template & Scope</span>
            </h3>
            <span className="text-[11px] font-mono text-text-muted">
              Region: {config.regionProfileId}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {REPORT_TEMPLATES.map((tmpl) => {
              const isSelected = config.templateId === tmpl.id;
              let Icon = FileText;
              if (tmpl.id === "site_infrastructure") Icon = Building2;
              if (tmpl.id === "suitability_capacity") Icon = Sliders;
              if (tmpl.id === "comprehensive_dossier") Icon = Layers;

              return (
                <button
                  key={tmpl.id}
                  data-testid={`template-btn-${tmpl.id}`}
                  type="button"
                  onClick={() => handleTemplateSelect(tmpl.id)}
                  className={`flex flex-col text-left p-3.5 rounded-lg border transition-all ${
                    isSelected
                      ? "border-primary-500 bg-primary-50 dark:bg-primary-950/40 text-text-primary shadow-xs ring-1 ring-primary-500"
                      : "border-border-subtle bg-surface-elevated text-text-secondary hover:border-border-strong hover:bg-surface-raised"
                  }`}
                >
                  <div className="flex items-start justify-between w-full mb-2">
                    <div
                      className={`p-1.5 rounded-md ${
                        isSelected
                          ? "bg-primary-100 dark:bg-primary-900/60 text-primary-600 dark:text-primary-400"
                          : "bg-surface-panel text-text-muted"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    {isSelected && (
                      <CheckCircle2 className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    )}
                  </div>
                  <div className="font-medium text-xs sm:text-sm text-text-primary mb-1">
                    {tmpl.title}
                  </div>
                  <div className="text-[11px] text-text-secondary leading-snug line-clamp-2 mb-2">
                    {tmpl.shortDescription}
                  </div>
                  <div className="mt-auto pt-2 border-t border-border-subtle w-full flex items-center justify-between">
                    <Badge
                      variant="outline"
                      size="sm"
                      className="text-[10px] font-mono border-border-subtle text-text-muted"
                    >
                      {getTemplateModelName(tmpl.id)}
                      <span className="sr-only">{tmpl.backendBinding.split(" ")[0]}</span>
                    </Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Configuration Filters & Options */}
        <div className="p-4 rounded-lg bg-surface-elevated border border-border-subtle space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            <Filter className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
            <span>Operational Parameters &amp; Filters</span>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 items-center">
            {/* Status Filter */}
            {currentTemplate.applicableFilters.statusFilter && (
              <div>
                <label className="block text-xs font-medium text-text-primary mb-1.5">
                  Village Assignment Status
                </label>
                <div className="inline-flex rounded-md bg-surface-panel p-0.5 border border-border-subtle w-full">
                  {(["all", "assigned", "unassigned"] as ReportStatusFilter[]).map(
                    (st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => handleStatusFilter(st)}
                        className={`flex-1 py-1 text-xs font-medium rounded capitalize transition-colors ${
                          config.statusFilter === st
                            ? "bg-primary-600 text-white font-semibold shadow-xs"
                            : "text-text-secondary hover:text-text-primary"
                        }`}
                      >
                        {st === "all" ? "All Statuses" : st}
                      </button>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Candidate Site Selector */}
            {currentTemplate.applicableFilters.siteSelector && (
              <div>
                <label
                  htmlFor="site-selector"
                  className="block text-xs font-medium text-text-primary mb-1.5"
                >
                  Target Candidate Site
                </label>
                <div className="relative">
                  <select
                    id="site-selector"
                    value={
                      config.selectedSiteId === "all"
                        ? "all"
                        : String(config.selectedSiteId)
                    }
                    onChange={(e) => handleSiteSelect(e.target.value)}
                    className="w-full rounded-md border border-border-subtle bg-surface-panel py-1.5 px-3 text-xs text-text-primary focus:border-primary-500 focus:outline-hidden focus:ring-1 focus:ring-primary-500 font-mono"
                  >
                    <option value="all">All Registered Candidate Sites</option>
                    {sites.map((s) => (
                      <option key={s.id} value={s.id}>
                        [Site {s.id}] {s.name}
                      </option>
                    ))}
                  </select>
                  <MapPin className="h-3.5 w-3.5 absolute right-3 top-2.5 text-text-muted pointer-events-none" />
                </div>
              </div>
            )}

            {/* Checkbox Toggles */}
            <div className="space-y-2 pt-1 md:pt-4">
              {currentTemplate.applicableFilters.includeAudits && (
                <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer select-none hover:text-text-primary">
                  <input
                    type="checkbox"
                    checked={config.includeAudits}
                    onChange={handleToggleAudits}
                    className="rounded border-border-subtle bg-surface-panel text-primary-600 focus:ring-primary-500 h-3.5 w-3.5"
                  />
                  <span>Include Candidate Rejection Audits</span>
                </label>
              )}

              {currentTemplate.applicableFilters.includeDeficits && (
                <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer select-none hover:text-text-primary">
                  <input
                    type="checkbox"
                    checked={config.includeDeficits}
                    onChange={handleToggleDeficits}
                    className="rounded border-border-subtle bg-surface-panel text-primary-600 focus:ring-primary-500 h-3.5 w-3.5"
                  />
                  <span>Include Infrastructure Deficit Analysis</span>
                </label>
              )}
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              Operational Model:{" "}
              <strong className="text-text-primary font-medium">
                {currentTemplate.backendBinding.replace(/M\d+-\d+\s*/g, "")}
              </strong>
            </span>
          </div>

          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={onCompile}
            isLoading={isCompiling}
            leftIcon={<Sparkles className="h-4 w-4 text-white" />}
            className="bg-primary-600 hover:bg-primary-700 text-white shadow-xs font-medium"
          >
            <span>Compile Operational Dossier</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
