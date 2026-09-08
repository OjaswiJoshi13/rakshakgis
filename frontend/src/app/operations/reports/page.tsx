"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import {
  CompiledDossier,
  ReportConfig,
  ReportTemplateId,
} from "@/types/reports";
import {
  compileReportDossier,
  downloadFile,
  generateAssignmentsCsv,
  generateDossierJson,
  generateSitesCsv,
} from "@/lib/api/reports";
import {
  listCandidateSites,
  HIMALAYAN_PILOT_SAMPLE_SITES,
} from "@/lib/api/sites";
import { CandidateSiteRead } from "@/types/sites";
import {
  ReportConfigPanel,
  ReportSummaryCards,
  DossierViewer,
  ReportEmptyState,
} from "@/components/operations/reports";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import {
  FileText,
  Download,
  Printer,
  RotateCcw,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

function ReportsOperationsContent() {
  const [config, setConfig] = useState<ReportConfig>({
    templateId: "relocation_allocation",
    statusFilter: "all",
    selectedSiteId: "all",
    includeAudits: true,
    includeDeficits: true,
    regionProfileId: "himalayan_pilot",
  });

  const [dossier, setDossier] = useState<CompiledDossier | null>(null);
  const [sites, setSites] = useState<CandidateSiteRead[]>(HIMALAYAN_PILOT_SAMPLE_SITES);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // Load registered candidate sites on mount
  useEffect(() => {
    let isMounted = true;
    async function fetchSites() {
      try {
        const resp = await listCandidateSites();
        if (isMounted && resp && resp.data && resp.data.length > 0) {
          setSites(resp.data);
        }
      } catch {
        // Fallback to Himalayan Pilot baseline sites
        if (isMounted) setSites(HIMALAYAN_PILOT_SAMPLE_SITES);
      }
    }
    fetchSites();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCompile = useCallback(async () => {
    setIsCompiling(true);
    setError(null);
    try {
      const compiled = await compileReportDossier(config);
      setDossier(compiled);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to compile operational report dossier.";
      setError(msg);
    } finally {
      setIsCompiling(false);
    }
  }, [config]);

  const handleSelectTemplate = (templateId: ReportTemplateId) => {
    setConfig((prev) => ({
      ...prev,
      templateId,
    }));
  };

  const showNotification = (message: string) => {
    setExportNotice(message);
    setTimeout(() => {
      setExportNotice(null);
    }, 5000);
  };

  const handleExportJson = () => {
    if (!dossier) return;
    const jsonStr = generateDossierJson(dossier);
    const filename = `${dossier.id.toLowerCase()}.json`;
    downloadFile(filename, jsonStr, "application/json");
    showNotification(`Dossier exported successfully as JSON (${filename}).`);
  };

  const handleExportCsv = () => {
    if (!dossier) return;

    if (
      (dossier.templateId === "relocation_allocation" ||
        dossier.templateId === "comprehensive_dossier") &&
      dossier.filteredAssignments &&
      dossier.filteredAssignments.length > 0
    ) {
      const csvStr = generateAssignmentsCsv(dossier.filteredAssignments);
      const filename = `${dossier.id.toLowerCase()}-assignments.csv`;
      downloadFile(filename, csvStr, "text/csv;charset=utf-8;");
      showNotification(`Village assignments exported as CSV (${filename}).`);
    } else if (dossier.sites && dossier.sites.length > 0) {
      const csvStr = generateSitesCsv(dossier.sites);
      const filename = `${dossier.id.toLowerCase()}-sites.csv`;
      downloadFile(filename, csvStr, "text/csv;charset=utf-8;");
      showNotification(`Candidate sites exported as CSV (${filename}).`);
    } else {
      showNotification("No tabular data available for CSV export.");
    }
  };

  const handlePrint = () => {
    if (typeof window === "undefined") return;
    // Set page title to dossier name for clean print header/PDF filename
    const originalTitle = document.title;
    if (dossier) {
      document.title = `${dossier.title} — RakshakGIS Operational Dossier`;
    }
    // @media print CSS in globals.css hides all application chrome
    // and shows only #operational-dossier-print-root
    window.print();
    // Restore title after print dialog closes
    document.title = originalTitle;
  };


  const handleReset = () => {
    setDossier(null);
    setError(null);
    setExportNotice(null);
  };

  return (
    <OperationsSectionShell
      title="Report Generation & Export"
      description="Authoritative relocation dossiers, multi-hazard risk summaries, and machine-readable data export conforming to disaster management documentation standards."
      chunkId="M6-07"
      chunkTitle="Report Generation & Export UI"
      prerequisiteChunk="Chunk M6-02 & M6-03 (Relocation Workflow & Sites — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2 flex-wrap">
          {dossier ? (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleReset}
                leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
              >
                <span>New Report</span>
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleExportJson}
                leftIcon={<Download className="h-3.5 w-3.5" />}
              >
                <span>Export JSON</span>
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleExportCsv}
                leftIcon={<Download className="h-3.5 w-3.5" />}
              >
                <span>Export CSV</span>
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handlePrint}
                leftIcon={<Printer className="h-3.5 w-3.5" />}
                className="bg-sky-600 hover:bg-sky-500 text-white"
              >
                <span>Print Dossier</span>
              </Button>
            </>
          ) : (
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleCompile}
              isLoading={isCompiling}
              leftIcon={<Sparkles className="h-3.5 w-3.5" />}
              className="bg-sky-600 hover:bg-sky-500 text-white"
            >
              <span>Compile Dossier</span>
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* Export Success Notification Banner */}
        {exportNotice && (
          <div className="flex items-center gap-2 rounded-lg border border-[#1a7f37]/40 bg-[#1a7f37]/10 p-3.5 text-xs text-[#1a7f37] dark:text-[#3fb950] shadow-2xs">
            <CheckCircle2 className="h-4 w-4 text-[#1a7f37] dark:text-[#3fb950] shrink-0" />
            <span>{exportNotice}</span>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <Alert
            severity="danger"
            title="Compilation Error"
            icon={<AlertCircle className="h-4 w-4 text-red-400" />}
          >
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCompile}
                className="ml-4 text-xs"
              >
                Retry
              </Button>
            </div>
          </Alert>
        )}

        {/* Configuration Panel */}
        <ReportConfigPanel
          config={config}
          onConfigChange={setConfig}
          sites={sites}
          onCompile={handleCompile}
          isCompiling={isCompiling}
        />

        {/* Dynamic Display: Empty State or Compiled Dossier */}
        {dossier ? (
          <div className="space-y-6">
            {/* Dossier Summary Cards */}
            <ReportSummaryCards metrics={dossier.metrics} />

            {/* Comprehensive Dossier Document Viewer */}
            <DossierViewer
              dossier={dossier}
              includeAudits={config.includeAudits}
              includeDeficits={config.includeDeficits}
            />
          </div>
        ) : (
          <ReportEmptyState
            onSelectTemplate={handleSelectTemplate}
            onGenerate={handleCompile}
            isCompiling={isCompiling}
          />
        )}
      </div>
    </OperationsSectionShell>
  );
}

export default function ReportsOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs text-slate-400 font-mono">
          Loading report generation workspace...
        </div>
      }
    >
      <ReportsOperationsContent />
    </Suspense>
  );
}
