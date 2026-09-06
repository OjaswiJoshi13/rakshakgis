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
          <Badge variant="outline" size="sm" className="font-mono text-emerald-400 border-emerald-600/50 bg-emerald-950/30">
            Approved
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-rose-400 border-rose-600/50 bg-rose-950/30">
            Rejected
          </Badge>
        );
      case "revision_requested":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-amber-400 border-amber-600/50 bg-amber-950/30">
            Revision
          </Badge>
        );
      case "committed":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-purple-400 border-purple-600/50 bg-purple-950/30">
            Committed
          </Badge>
        );
      case "executed":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-cyan-400 border-cyan-600/50 bg-cyan-950/30">
            Executed
          </Badge>
        );
      case "acknowledged":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-sky-400 border-sky-600/50 bg-sky-950/30">
            Acknowledged
          </Badge>
        );
      case "exported":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-slate-300 border-slate-600/50 bg-slate-900/30">
            Exported
          </Badge>
        );
      case "reopened":
        return (
          <Badge variant="outline" size="sm" className="font-mono text-yellow-300 border-yellow-600/50 bg-yellow-950/30">
            Reopened
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="font-mono text-slate-400">
            {status}
          </Badge>
        );
    }
  };

  if (isLoading && records.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-12 text-center text-xs font-mono text-slate-400">
        <Clock className="h-6 w-6 animate-spin mx-auto text-sky-400 mb-2" />
        Loading immutable audit trail...
      </div>
    );
  }

  if (records.length === 0) {
    return (
      <div
        data-testid="audit-empty-state"
        className="rounded-lg border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center space-y-2"
      >
        <p className="text-sm font-semibold text-slate-300">
          No audit records found matching your filters.
        </p>
        <p className="text-xs text-slate-500">
          Adjust your search terms or filter selections to view recorded events.
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="audit-table"
      className="rounded-lg border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Timestamp & ID</th>
              <th className="py-3 px-4">Actor / Official</th>
              <th className="py-3 px-4">Action & Status</th>
              <th className="py-3 px-4">Target Entity & Resource</th>
              <th className="py-3 px-4">Official Rationale / Notes</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {records.map((record) => {
              const isSelected = selectedRecordId === record.id;
              const isOfficerDecision = record.category === "officer_decision";

              return (
                <tr
                  key={record.id}
                  data-testid={`audit-row-${record.id}`}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    isSelected ? "bg-sky-950/20" : ""
                  }`}
                >
                  {/* Timestamp & ID */}
                  <td className="py-3 px-4 whitespace-nowrap font-mono">
                    <div className="font-semibold text-slate-200">
                      {new Date(record.timestamp).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      {new Date(record.timestamp).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </div>
                    <div className="text-[10px] text-sky-400 font-mono mt-0.5">
                      {record.id}
                    </div>
                  </td>

                  {/* Actor / Official */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      {isOfficerDecision ? (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-950 border border-emerald-600/60 text-emerald-400 shrink-0">
                          <UserCheck className="h-3 w-3" />
                        </div>
                      ) : (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-950 border border-purple-600/60 text-purple-400 shrink-0">
                          <Cpu className="h-3 w-3" />
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-slate-200">
                          {record.actor.name}
                        </div>
                        <div className="text-[10px] font-mono text-slate-400">
                          {record.actor.role}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Action & Status */}
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="font-medium text-slate-200 line-clamp-1">
                        {record.action_label}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {getStatusBadge(record.decision_status)}
                        {isOfficerDecision && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] font-mono text-emerald-400">
                            <ShieldCheck className="h-3 w-3" />
                            Rule 12
                          </span>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Target Entity & Resource */}
                  <td className="py-3 px-4 max-w-xs">
                    <div className="font-medium text-slate-200 line-clamp-1">
                      {record.target_entity_name}
                    </div>
                    <div className="font-mono text-[10px] text-slate-400 truncate">
                      {record.resource_id}
                    </div>
                  </td>

                  {/* Reason / Justification Snippet */}
                  <td className="py-3 px-4 max-w-sm">
                    {record.reason ? (
                      <p className="text-slate-300 text-[11px] line-clamp-2 italic">
                        &ldquo;{record.reason}&rdquo;
                      </p>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-mono">
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
