"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import {
  AuditSummaryCards,
  AuditFilterBar,
  AuditTable,
  AuditDetailModal,
} from "@/components/operations/audit";
import {
  AuditActionCategory,
  AuditRecord,
  AuditSummaryKPIs,
  HashIntegrityResult,
} from "@/types/audit";
import {
  listAuditRecords,
  getAuditKPIs,
  verifyAuditIntegrity,
  INITIAL_AUDIT_RECORDS,
} from "@/lib/api/audit";
import { ShieldCheck, RefreshCw, ShieldAlert, Lock } from "lucide-react";

function AuditOperationsContent() {
  const [records, setRecords] = useState<AuditRecord[]>(INITIAL_AUDIT_RECORDS);
  const [kpis, setKpis] = useState<AuditSummaryKPIs>({
    totalEvents: INITIAL_AUDIT_RECORDS.length,
    officerSignOffs: INITIAL_AUDIT_RECORDS.filter((r) => r.category === "officer_decision").length,
    automatedActions: INITIAL_AUDIT_RECORDS.filter((r) => r.category !== "officer_decision").length,
    integrityPercentage: 100,
  });

  // Filter & Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<AuditActionCategory>("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedTimeRange, setSelectedTimeRange] = useState<"all" | "24h" | "7d" | "30d">("all");

  // Selection & Modal state
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Status flags
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error" | "info";
    message: string;
    details?: string;
  } | null>(null);

  // Load records and KPIs
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [fetchedRecords, fetchedKpis] = await Promise.all([
        listAuditRecords({
          query: searchQuery,
          category: selectedCategory,
          decisionStatus: selectedStatus,
          timeRange: selectedTimeRange,
        }),
        getAuditKPIs(),
      ]);

      setRecords(fetchedRecords);
      setKpis(fetchedKpis);
    } catch {
      setNotification({
        type: "error",
        message: "Failed to retrieve audit log events. Please retry.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedCategory, selectedStatus, selectedTimeRange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reset all filters
  const handleResetFilters = () => {
    setSearchQuery("");
    setSelectedCategory("all");
    setSelectedStatus("all");
    setSelectedTimeRange("all");
    setNotification(null);
  };

  // Inspect a specific record
  const handleInspectRecord = (record: AuditRecord) => {
    setSelectedRecord(record);
    setIsDetailOpen(true);
  };

  // Run cryptographic hash integrity verification
  const handleVerifyIntegrity = async () => {
    setIsVerifying(true);
    try {
      const result: HashIntegrityResult = await verifyAuditIntegrity();
      if (result.isValid) {
        setNotification({
          type: "success",
          message: `Cryptographic Audit Verification Passed: 100% of recorded actions (${result.verifiedCount}/${result.totalCount}) match their cryptographic SHA-256 seal.`,
          details: `Verification Engine: ${result.algorithm} • Timestamp: ${new Date(result.verifiedAt).toLocaleTimeString("en-IN")}`,
        });
      } else {
        setNotification({
          type: "error",
          message: `Integrity Warning: ${result.totalCount - result.verifiedCount} records failed hash seal verification.`,
        });
      }
    } catch {
      setNotification({
        type: "error",
        message: "Failed to execute cryptographic verification probe.",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <OperationsSectionShell
      title="Audit Log & Traceability"
      description="Immutable decision trail, cryptographically verifiable action history, and compliance logging for all AI recommendations and officer sign-offs."
      chunkId="M6-09"
      chunkTitle="Audit Log & Traceability UI"
      prerequisiteChunk="Chunk M6-08 (Officer Review & Action Sign-Off Workflow — COMMITTED)"
      actionToolbar={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleVerifyIntegrity}
            isLoading={isVerifying}
            disabled={isVerifying}
            leftIcon={
              !isVerifying ? (
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              ) : undefined
            }
            data-testid="verify-hashes-btn"
          >
            Verify Cryptographic Hashes
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={loadData}
            isLoading={isLoading}
            disabled={isLoading}
            leftIcon={
              !isLoading ? (
                <RefreshCw className="h-3.5 w-3.5" />
              ) : undefined
            }
            data-testid="refresh-audit-btn"
          >
            Refresh Trail
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Statutory Governance & Audit Trail Posture Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border-base bg-surface-raised px-3.5 py-2.5 text-xs text-text-secondary font-mono shadow-2xs">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-[#0969da] dark:text-[#2f81f7] shrink-0" />
            <span>
              Protocol: <strong className="text-text-primary">Statutory Governance & Compliance Ledger</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[#1a7f37] dark:text-[#3fb950] font-medium">
              <span className="h-2 w-2 rounded-full bg-[#1a7f37] dark:bg-[#3fb950] animate-pulse" />
              <span>Tamper-Evident SHA-256 Ledger</span>
            </div>
            <span className="text-border-base">|</span>
            <span className="text-text-muted">Read-Only Statutory Archive</span>
          </div>
        </div>

        {/* Feedback Alert Banner */}
        {notification && (
          <Alert
            severity={notification.type === "success" ? "success" : "danger"}
            title={notification.type === "success" ? "Cryptographic Verification" : "Operational Notice"}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="space-y-0.5">
                <div>{notification.message}</div>
                {notification.details && (
                  <div className="text-[11px] font-mono opacity-80">
                    {notification.details}
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => setNotification(null)}
                className="text-xs underline font-mono ml-4 hover:opacity-80 shrink-0"
              >
                Dismiss
              </button>
            </div>
          </Alert>
        )}

        {/* Executive Summary Metric Cards */}
        <AuditSummaryCards metrics={kpis} isLoading={isLoading} />

        {/* Filter & Search Bar */}
        <AuditFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          selectedStatus={selectedStatus}
          onStatusChange={setSelectedStatus}
          selectedTimeRange={selectedTimeRange}
          onTimeRangeChange={setSelectedTimeRange}
          onReset={handleResetFilters}
          totalResults={records.length}
        />

        {/* Read-Only Audit Table */}
        <AuditTable
          records={records}
          selectedRecordId={selectedRecord?.id}
          onSelectRecord={handleInspectRecord}
          isLoading={isLoading}
        />

        {/* Deep Inspection Detail Modal */}
        <AuditDetailModal
          record={selectedRecord}
          isOpen={isDetailOpen}
          onClose={() => {
            setIsDetailOpen(false);
            setSelectedRecord(null);
          }}
        />
      </div>
    </OperationsSectionShell>
  );
}

export default function AuditOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs text-slate-400 font-mono">
          Loading audit log and decision traceability workspace...
        </div>
      }
    >
      <AuditOperationsContent />
    </Suspense>
  );
}
