"use client";

import React from "react";
import { OperationsNav } from "./OperationsNav";
import { useAuth } from "@/context/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { DATA_MODE_CONFIG, DataMode } from "@/design-system/tokens";
import { ShieldCheck, User } from "lucide-react";
import { cn } from "@/lib/utils";

export interface OperationsShellProps {
  children: React.ReactNode;
  className?: string;
}

export const OperationsShell: React.FC<OperationsShellProps> = ({
  children,
  className,
}) => {
  const { user } = useAuth();
  const dataMode: DataMode =
    (process.env.NEXT_PUBLIC_DATA_MODE as DataMode) || "demo";
  const modeConfig = DATA_MODE_CONFIG[dataMode] || DATA_MODE_CONFIG.demo;

  const roleLabels: Record<string, string> = {
    admin: "Platform Administrator",
    district_officer: "District Disaster Officer",
    field_responder: "Field Response Officer",
    viewer: "Operational Observer",
  };

  return (
    <div className={cn("flex flex-col space-y-5", className)}>
      {/* Operations Command Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-950 border border-sky-600/70 text-sky-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-sky-400">
                Operations Console • Chunk M6-01
              </span>
              <span className="rounded bg-slate-800 border border-slate-700 px-1.5 py-0.2 text-[10px] font-mono text-slate-300 uppercase">
                Officer Shell
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-slate-100 tracking-tight">
              Disaster Response & Relocation Decision System
            </h2>
          </div>
        </div>

        {/* Operational Context Strip */}
        <div className="flex flex-wrap items-center gap-2">
          {user && (
            <div className="flex items-center gap-1.5 rounded bg-slate-900 border border-slate-800 px-2.5 py-1 text-xs text-slate-300 font-mono">
              <User className="h-3.5 w-3.5 text-slate-400" />
              <span>{roleLabels[user.role] || user.role}</span>
            </div>
          )}

          <Badge variant="outline" size="sm" className="font-mono text-slate-300">
            Himalayan Pilot (Chamoli)
          </Badge>

          <span
            className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-mono font-semibold tracking-wider uppercase ${modeConfig.badgeClass}`}
          >
            {modeConfig.label}
          </span>
        </div>
      </div>

      {/* Persistent Operations Sub-Navigation */}
      <OperationsNav />

      {/* Operational Workspace Viewport */}
      <section
        id="operations-workspace"
        aria-label="Operations Workspace"
        className="w-full"
      >
        {children}
      </section>
    </div>
  );
};
