"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { AuditRecord, AuditDecisionStatus } from "@/types/audit";
import { ShieldCheck, Cpu, Eye, Clock, UserCheck } from "lucide-react";

interface AuditTableProps {
  records: AuditRecord[];
  selectedRecordId?: string;
  onSelectRecord: (record: AuditRecord) => void;
  isLoading?: boolean;
}

export const AuditTable: React.FC<AuditTableProps> = ({
  records,
  selectedRecordId,
  onSelectRecord,
  isLoading = false,
}) => {
  const getStatusBadge = (status: AuditDecisionStatus) => {
    switch (status) {
      case "approved":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-emerald-800 border-emerald-300 bg-emerald-50 dark:text-emerald-400 dark:border-emerald-600/50 dark:bg-emerald-950/30">
            Approved
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-rose-800 border-rose-300 bg-rose-50 dark:text-rose-400 dark:border-rose-600/50 dark:bg-rose-950/30">
            Rejected
          </Badge>
        );
      case "revision_requested":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-amber-800 border-amber-300 bg-amber-50 dark:text-amber-400 dark:border-amber-600/50 dark:bg-amber-950/30">
            Revision
          </Badge>
        );
      case "committed":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-purple-800 border-purple-300 bg-purple-50 dark:text-purple-400 dark:border-purple-600/50 dark:bg-purple-950/30">
            Committed
          </Badge>
        );
      case "executed":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-cyan-800 border-cyan-300 bg-cyan-50 dark:text-cyan-400 dark:border-cyan-600/50 dark:bg-cyan-950/30">
            Executed
          </Badge>
        );
      case "acknowledged":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-sky-800 border-sky-300 bg-sky-50 dark:text-sky-400 dark:border-sky-600/50 dark:bg-sky-950/30">
            Acknowledged
          </Badge>
        );
      case "exported":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-text-secondary border-border-subtle bg-surface-elevated">
            Exported
          </Badge>
        );
      case "reopened":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-amber-800 border-amber-300 bg-amber-50 dark:text-yellow-300 dark:border-yellow-600/50 dark:bg-yellow-950/30">
            Reopened
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="font-mono text-text-muted">
            {status}
          </Badge>
        );
    }
  };

  if (isLoading && records.length === 0) {
    return (
      <div className="rounded-lg border border-border-subtle bg-surface-panel p-12 text-center text-xs font-mono text-text-muted">
        <Clock className="h-6 w-6 animate-spin mx-auto text-sky-600 dark:text-sky-400 mb-2" />
        Loading immutable audit trail...
      </div>
    );
  }

  if (records.length === 0) {
    return (
      <div
        data-testid="audit-empty-state"
        className="rounded-lg border border-dashed border-border-strong bg-surface-panel/80 p-12 text-center space-y-2"
      >
        <p className="text-sm font-semibold text-text-primary">
          No audit records found matching your filters.
        </p>
        <p className="text-xs text-text-muted">
          Adjust your search terms or filter selections to view recorded events.
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="audit-table"
      className="rounded-lg border border-border-subtle bg-surface-panel overflow-hidden shadow-sm"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border-subtle bg-surface-elevated text-text-muted font-mono text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Timestamp & ID</th>
              <th className="py-3 px-4">Actor / Official</th>
              <th className="py-3 px-4">Action & Status</th>
              <th className="py-3 px-4">Target Entity & Resource</th>
              <th className="py-3 px-4">Official Rationale / Notes</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle bg-surface-panel">
            {records.map((record) => {
              const isSelected = selectedRecordId === record.id;
              const isOfficerDecision = record.category === "officer_decision";

              return (
                <tr
                  key={record.id}
                  data-testid={`audit-row-${record.id}`}
                  className={`hover:bg-surface-subtle transition-colors ${
                    isSelected ? "bg-sky-50 dark:bg-sky-950/30" : ""
                  }`}
                >
                  {/* Timestamp & ID */}
                  <td className="py-3 px-4 whitespace-nowrap font-mono">
                    <div className="font-semibold text-text-primary">
                      {new Date(record.timestamp).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </div>
                    <div className="text-[10px] text-text-muted">
                      {new Date(record.timestamp).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </div>
                    <div className="text-[10px] text-sky-700 dark:text-sky-400 font-mono mt-0.5">
                      {record.id}
                    </div>
                  </td>

                  {/* Actor / Official */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      {isOfficerDecision ? (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-50 text-emerald-700 border border-emerald-300 dark:bg-emerald-950 dark:border-emerald-600/60 dark:text-emerald-400 shrink-0">
                          <UserCheck className="h-3 w-3" />
                        </div>
                      ) : (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-50 text-purple-700 border border-purple-300 dark:bg-purple-950 dark:border-purple-600/60 dark:text-purple-400 shrink-0">
                          <Cpu className="h-3 w-3" />
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-text-primary">
                          {record.actor.name}
                        </div>
                        <div className="text-[10px] font-mono text-text-muted">
                          {record.actor.role}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Action & Status */}
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="font-medium text-text-primary line-clamp-1">
                        {record.action_label}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {getStatusBadge(record.decision_status)}
                        {isOfficerDecision && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] font-mono text-emerald-700 dark:text-emerald-400">
                            <ShieldCheck className="h-3 w-3" />
                            Rule 12
                          </span>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Target Entity & Resource */}
                  <td className="py-3 px-4 max-w-xs">
                    <div className="font-medium text-text-primary line-clamp-1">
                      {record.target_entity_name}
                    </div>
                    <div className="font-mono text-[10px] text-text-muted truncate">
                      {record.resource_id}
                    </div>
                  </td>

                  {/* Reason / Justification Snippet */}
                  <td className="py-3 px-4 max-w-sm">
                    {record.reason ? (
                      <p className="text-text-secondary text-[11px] line-clamp-2 italic">
                        &ldquo;{record.reason}&rdquo;
                      </p>
                    ) : (
                      <span className="text-[11px] text-text-muted font-mono">
                        No recorded justification
                      </span>
                    )}
                  </td>

                  {/* Inspect Details Button */}
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => onSelectRecord(record)}
                      className="text-xs h-7 gap-1"
                      data-testid={`inspect-audit-${record.id}`}
                    >
                      <Eye className="h-3 w-3" />
                      <span>Inspect</span>
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
