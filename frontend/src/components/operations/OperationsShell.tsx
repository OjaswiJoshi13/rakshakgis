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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-surface-elevated border border-border-subtle text-text-secondary">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-text-muted">
                <span className="sr-only">Operations Console • Chunk M6-01</span>
                <span>Operations Console</span>
              </span>
              <span className="rounded bg-surface-elevated border border-border-subtle px-1.5 py-0.5 text-[11px] text-text-secondary">
                Active Protocol
              </span>
            </div>
            <h2 className="text-base font-semibold text-text-primary tracking-tight">
              Disaster Response & Relocation Decision System
            </h2>
          </div>
        </div>

        {/* Operational Context Strip */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {user && (
            <div className="flex items-center gap-1.5 rounded bg-surface-elevated border border-border-subtle px-2.5 py-1 text-xs text-text-secondary">
              <User className="h-3 w-3 text-text-muted" />
              <span>{roleLabels[user.role] || user.role}</span>
            </div>
          )}

          <Badge variant="outline" size="sm" className="text-xs text-text-secondary border-border-subtle">
            Himalayan Pilot (Chamoli)
          </Badge>

          <span
            className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${modeConfig.badgeClass}`}
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
